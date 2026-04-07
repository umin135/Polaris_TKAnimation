import bpy
import struct
import mathutils
import math
import os
from .profiles_tk8 import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS, CATEGORY_MASKS, IGNORE_BONES


def _load_fullbody_template():
    """원본 PANM 파일에서 FlatBuffers 헤더 + 전체 데이터를 로드합니다."""
    ref_path = os.path.join(os.path.dirname(__file__), '_ref', 'anim_diff', 'kaz_idle_ori.bin')
    if not os.path.exists(ref_path):
        for name in ('original.bin', 'template.bin'):
            alt = os.path.join(os.path.dirname(__file__), '_ref', 'anim_diff', name)
            if os.path.exists(alt):
                ref_path = alt
                break
        else:
            return None, None
    with open(ref_path, 'rb') as f:
        data = f.read()
    block_c_base = struct.unpack_from('<I', data, 0x50)[0]
    # 헤더(FlatBuffers 메타데이터)와 원본 C-블록 데이터 모두 반환
    return bytearray(data[:block_c_base]), data

# ==============================================================================
# FULLBODY 43개 뼈대 트랙 정보 (kaz_idle_ori.bin에서 추출)
# enc: 1=프레임별 애니메이션, 2=정적 레스트 포즈 (1샘플)
# t_tbl: FlatBuffers 템플릿 내 트랙 테이블 시작 오프셋
# c_rel_orig: 원본에서의 C-블록 상대 오프셋 (새 c_rel 계산을 위한 순서 기준)
# tf4/tf6/tf7: 트랙 테이블 내 sample_count/c_rel/c_size 필드 오프셋
# ==============================================================================
_FULLBODY_TRACK_INFO = [
    # (bone_name, enc, c_rel_orig, t_tbl, tf4, tf6, tf7)
    ("Top",                  1,     0, 4604, 16, 0,  24),
    ("L_Shoulder",           1, 42976, 3328, 16, 24, 28),
    ("L_UpperLeg",           1, 70608, 2176, 16, 24, 28),
    ("Trans",                1,  3872, 4500, 16, 24, 28),
    ("HARA_ROT1",            2,  7744, 4416, 16, 24, 28),
    ("Hip",                  2, 11712, 4224, 16, 24, 28),
    ("Rot",                  1,  7792, 4352, 16, 24, 28),
    ("PMP_L_Shoulder",       2, 58656, 2816, 16, 24, 28),
    ("Spine1",               1, 11760, 4160, 16, 24, 28),
    ("MUKI",                 2, 11664, 4288, 16, 24, 28),
    ("PMP_R_LowerLeg",       2, 70512, 2304, 16, 24, 28),
    ("Spine2",               1, 15632, 4096, 16, 24, 28),
    ("R_Toe",                2, 70464, 2368, 16, 24, 28),
    ("PMP_L_UpperLeg",       2, 82320, 1856, 16, 24, 28),
    ("Neck",                 1, 19504, 4032, 16, 24, 28),
    ("L_Have",               2, 58464, 3072, 16, 24, 28),
    ("Head",                 1, 23376, 3968, 16, 24, 28),
    ("R_Hand",               1, 38864, 3712, 16, 24, 28),
    ("PMP_L_Chest",          2, 58704, 2752, 16, 24, 28),
    ("R_Shoulder",           1, 27248, 3904, 16, 24, 28),
    ("L_UpperArm",           1, 46848, 3264, 16, 24, 28),
    ("R_UpperArm",           1, 31120, 3840, 16, 24, 28),
    ("R_LowerArm",           1, 34992, 3776, 16, 24, 28),
    ("R_Have",               2, 42736, 3648, 16, 24, 28),
    ("PMP_L_UpperArm",       2, 58608, 2880, 16, 24, 28),
    ("PMP_R_UpperLeg",       2, 70560, 2240, 16, 24, 28),
    ("PMP_R_LowerArm",       2, 42784, 3584, 16, 24, 28),
    ("PMP_R_LowerArm_fore",  2, 42832, 3520, 16, 24, 28),
    ("L_Foot",               1, 78352, 2048, 16, 24, 28),
    ("PMP_R_UpperArm",       2, 42880, 3456, 16, 24, 28),
    ("PMP_R_Shoulder",       2, 42928, 3392, 16, 24, 28),
    ("L_LowerArm",           1, 50720, 3200, 16, 24, 28),
    ("L_Hand",               1, 54592, 3136, 16, 24, 28),
    ("PMP_L_LowerArm",       2, 58512, 3008, 16, 24, 28),
    ("PMP_L_LowerArm_fore",  2, 58560, 2944, 16, 24, 28),
    ("PMP_R_Chest",          2, 58752, 2688, 16, 24, 28),
    ("C_Leg",                2, 58800, 2624, 16, 24, 28),
    ("R_UpperLeg",           1, 58848, 2560, 16, 24, 28),
    ("R_Foot",               1, 66592, 2432, 16, 24, 28),
    ("R_LowerLeg",           1, 62720, 2496, 16, 24, 28),
    ("L_LowerLeg",           1, 74480, 2112, 16, 24, 28),
    ("L_Toe",                2, 82224, 1984, 16, 24, 28),
    ("PMP_L_LowerLeg",       2, 82272, 1920, 16, 24, 28),
]

# c_rel_orig 기준으로 정렬된 순서 (C-블록 작성 순서)
_FULLBODY_CBLOCK_ORDER = sorted(_FULLBODY_TRACK_INFO, key=lambda x: x[2])

# ==============================================================================
# ROOT 뼈대 집합 (위치 애니메이션이 있는 뼈대)
# ==============================================================================
_FULLBODY_ROOT_BONES = {"Trans", "Top", "Rot"}


def _inverse_loc_map(mx, my, mz, mapped_x, mapped_y, mapped_z):
    """
    loc_map 역연산: 매핑된 좌표(e_loc) → 엔진 원래 좌표(px, py, pz)
    """
    engine = {'x': 0.0, 'y': 0.0, 'z': 0.0}
    for mapped_val, axis_str in [(mapped_x, mx), (mapped_y, my), (mapped_z, mz)]:
        base = axis_str.lstrip('-')
        sign = -1.0 if axis_str.startswith('-') else 1.0
        engine[base] = sign * mapped_val
    return engine['x'], engine['y'], engine['z']


def _get_enc2_sample(obj, bone_name, selected_group, do_apose_correction):
    """
    enc=2 정적 뼈대의 PANM 샘플을 계산합니다.
    - 회전: 현재 프레임의 pbone.rotation_quaternion (임포트 시 프로필 변환으로 설정된 값) 역변환
    - 위치: 아마추어 레스트 포즈 (엔진 단위 그대로, scale_div 미적용)
    """
    pbone = obj.pose.bones.get(bone_name)
    if pbone is None:
        return (1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)

    rx, ry, rz = selected_group["basis"]
    do_flip    = selected_group["flip"]
    ox, oy, oz = selected_group["offset"]
    prx, pry, prz = selected_group.get("post_rot", (0, 0, 0))

    C_mat = mathutils.Euler(
        (math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ'
    ).to_matrix().to_4x4()
    C_inv = C_mat.inverted()
    offset_quat_inv   = mathutils.Euler(
        (math.radians(ox),  math.radians(oy),  math.radians(oz)),  'XYZ'
    ).to_quaternion().inverted()
    post_rot_quat_inv = mathutils.Euler(
        (math.radians(prx), math.radians(pry), math.radians(prz)), 'XYZ'
    ).to_quaternion().inverted()

    if do_apose_correction and bone_name in APOSE_OFFSETS:
        ax, ay, az = APOSE_OFFSETS[bone_name]
        apose_quat_inv = mathutils.Euler(
            (math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ'
        ).to_quaternion().inverted()
    else:
        apose_quat_inv = mathutils.Quaternion((1, 0, 0, 0))

    # 회전: pbone 에서 읽어 임포트 프로필 변환 역적용 (post_rot 먼저 제거)
    b_rot = pbone.rotation_quaternion.copy() @ post_rot_quat_inv
    b_rot = apose_quat_inv @ b_rot
    M_blender = mathutils.Matrix.LocRotScale(
        mathutils.Vector((0, 0, 0)), b_rot, mathutils.Vector((1, 1, 1))
    )
    M_engine = C_inv @ M_blender @ C_mat
    _, e_rot, e_sca = M_engine.decompose()
    e_rot = e_rot @ offset_quat_inv

    qw, qx, qy, qz = e_rot.w, e_rot.x, e_rot.y, e_rot.z
    if do_flip:
        qy = -qy

    # 위치: 아마추어 레스트 포즈 (scale_div 미적용 — 아마추어는 엔진 cm 단위)
    px, py, pz = _get_rest_pos_engine(obj, bone_name, selected_group)

    return (e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 0.0)


def _get_rest_pos_engine(obj, bone_name, selected_group):
    """
    비루트 뼈대의 아마추어 레스트 포즈 위치를 엔진 공간으로 변환합니다.
    아마추어가 엔진 cm 단위로 설정돼 있으므로 scale_div를 적용하지 않습니다.
    """
    arm = obj.data
    arm_bone = arm.bones.get(bone_name)
    if arm_bone is None:
        return 0.0, 0.0, 0.0

    if arm_bone.parent:
        rest_mat = arm_bone.parent.matrix_local.inverted() @ arm_bone.matrix_local
    else:
        rest_mat = arm_bone.matrix_local

    b_pos = rest_mat.to_translation()

    rx, ry, rz = selected_group["basis"]
    do_flip    = selected_group["flip"]
    mx, my, mz = selected_group["loc_map"]

    C_mat = mathutils.Euler(
        (math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ'
    ).to_matrix().to_4x4()
    C_inv = C_mat.inverted()

    e_loc = C_inv.to_3x3() @ b_pos
    px, py, pz = _inverse_loc_map(mx, my, mz, e_loc.x, e_loc.y, e_loc.z)

    if do_flip:
        py = -py

    # scale_div 미적용: 아마추어 위치가 이미 엔진 단위(cm)
    return px, py, pz


def _has_keyframes(obj, bone_name):
    """
    현재 액션에서 해당 본의 rotation_quaternion 키프레임이 2개 이상 있으면 True.
    enc=1 (animated) / enc=2 (static) 동적 결정에 사용.
    """
    action = obj.animation_data and obj.animation_data.action
    if not action:
        return False
    data_path = f'pose.bones["{bone_name}"].rotation_quaternion'
    for fc in action.fcurves:
        if fc.data_path == data_path and len(fc.keyframe_points) >= 2:
            return True
    return False


def _has_constraints(obj, bone_name):
    """
    해당 본에 컨스트레인트가 하나라도 있으면 True.
    IK 등 컨스트레인트로 구동되는 본은 키프레임이 없어도 enc=1로 처리.
    """
    pbone = obj.pose.bones.get(bone_name)
    if pbone is None:
        return False
    return len(pbone.constraints) > 0


def _bake_to_temp_action(obj, start_frame, end_frame):
    """
    IK/컨스트레인트 결과를 임시 액션으로 베이크합니다.
    반환값: (original_action, baked_action)
    내보내기 후 original_action으로 복원하고 baked_action을 삭제하세요.
    """
    original_action = obj.animation_data.action if obj.animation_data else None

    prev_active = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj

    prev_mode = obj.mode
    if prev_mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')

    bpy.ops.pose.select_all(action='SELECT')

    bpy.ops.nla.bake(
        frame_start=start_frame,
        frame_end=end_frame,
        step=1,
        only_selected=False,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,
        bake_types={'POSE'},
    )

    baked_action = obj.animation_data.action

    if prev_mode != 'POSE':
        bpy.ops.object.mode_set(mode=prev_mode)
    bpy.context.view_layer.objects.active = prev_active

    return original_action, baked_action


def execute_export(export_path, obj, anim_type, apply_apose=True, include_dummy=False):
    print(f"\n[*] Starting Polaris Export for {anim_type}")
    print(f"[*] Output File: {export_path}")

    if anim_type == 'CAMERA':
        print("[!] Camera export is not supported yet.")
        return

    if anim_type == 'FULLBODY':
        _execute_export_fullbody(export_path, obj, apply_apose)
        return

    # ── 기타 카테고리: 기존 커스텀 포맷 내보내기 ──────────────────────────────
    _execute_export_custom(export_path, obj, anim_type, apply_apose, include_dummy)


# ==============================================================================
# FULLBODY 전용 내보내기 (FlatBuffers 템플릿 기반)
# ==============================================================================
def _execute_export_fullbody(export_path, obj, apply_apose):
    """
    원본 PANM FlatBuffers 헤더를 템플릿으로 사용해 정확한 바이너리를 생성합니다.
    C-블록 데이터는 Blender 포즈 + 아마추어 레스트 포즈에서 계산합니다.
    """
    template, template_raw = _load_fullbody_template()
    if template is None:
        print("[!] 템플릿 파일을 찾을 수 없습니다: _ref/anim_diff/kaz_idle_ori.bin")
        print("[!] 커스텀 포맷으로 폴백합니다...")
        _execute_export_custom(export_path, obj, 'FULLBODY', apply_apose, False)
        return
    template_c_base = struct.unpack_from('<I', template_raw, 0x50)[0]

    scene = bpy.context.scene
    start_frame = int(scene.frame_start)
    end_frame   = int(scene.frame_end)
    total_frames = max(1, end_frame - start_frame + 1)

    root_bones, target_groups = PROFILE_REGISTRY.get('FULLBODY', (set(), {}))
    do_apose_correction = apply_apose

    # ── 1. 트랙 인포에서 뼈대 집합 확인 ─────────────────────────────────────
    track_names = {t[0] for t in _FULLBODY_TRACK_INFO}
    missing = [n for n in track_names if n not in obj.pose.bones]
    if missing:
        print(f"[!] 아마추어에 누락된 뼈대: {missing[:5]}{'...' if len(missing)>5 else ''}")

    print(f"[*] 프레임 범위: {start_frame}~{end_frame} (총 {total_frames}프레임)")

    # ── 2. 각 뼈대 그룹 정보 캐시 ────────────────────────────────────────────
    group_cache = {}
    for bone_name, enc, *_ in _FULLBODY_TRACK_INFO:
        grp = next(
            (g for g in target_groups.values() if bone_name in g["bones"]),
            DEFAULT_FALLBACK
        )
        group_cache[bone_name] = grp

    # ── 3. enc 동적 결정 (키프레임 유무 기준) ────────────────────────────────
    # IGNORE_BONES는 항상 템플릿 원본 enc 유지 (데이터 건드리지 않음)
    _CONSTRAINT_IGNORE_BONES = {"Rot"}  # 컨스트레인트를 무시하고 키프레임만 참조할 본

    dynamic_enc = {}
    for bone_name, enc_orig, *_ in _FULLBODY_TRACK_INFO:
        if bone_name in IGNORE_BONES:
            dynamic_enc[bone_name] = enc_orig
        elif bone_name not in _CONSTRAINT_IGNORE_BONES and _has_constraints(obj, bone_name):
            dynamic_enc[bone_name] = 1  # 컨스트레인트 본은 항상 전 프레임 베이크
        elif _has_keyframes(obj, bone_name):
            dynamic_enc[bone_name] = 1
        else:
            dynamic_enc[bone_name] = enc_orig
    animated_bones = {n for n, e in dynamic_enc.items() if e == 1 and n not in IGNORE_BONES}
    static_bones   = {n for n, e in dynamic_enc.items() if e == 2 and n not in IGNORE_BONES}
    promoted = animated_bones - {n for n, e, *_ in _FULLBODY_TRACK_INFO if e == 1}
    if promoted:
        print(f"[*] enc=2→1 승격 뼈대: {sorted(promoted)}")

    # ── 3b. 컨스트레인트 본이 있으면 임시 베이크 ─────────────────────────────
    # IK 등 컨스트레인트 결과는 pbone.rotation_quaternion에 반영되지 않으므로
    # visual_keying 베이크로 실제 포즈를 fcurve에 기록한 뒤 내보내기에 사용
    baked_action   = None
    original_action = None
    needs_bake = any(
        bone_name not in _CONSTRAINT_IGNORE_BONES and _has_constraints(obj, bone_name)
        for bone_name in animated_bones
    )
    if needs_bake:
        print("[*] IK/컨스트레인트 본 감지 → 임시 베이크 시작...")
        original_action, baked_action = _bake_to_temp_action(obj, start_frame, end_frame)
        print(f"[*] 임시 베이크 완료: {baked_action.name}")

    # ── 4. 레스트 포즈 위치 캐시 (비루트 enc=1 뼈대용) ───────────────────────
    rest_pos_cache = {}
    for bone_name in animated_bones:
        if bone_name not in _FULLBODY_ROOT_BONES:
            grp = group_cache[bone_name]
            rest_pos_cache[bone_name] = _get_rest_pos_engine(obj, bone_name, grp)

    # ── 5. 프레임별 포즈 데이터 수집 (enc=1 뼈대) ────────────────────────────
    anim_data = {}
    for bone_name in animated_bones:
        anim_data[bone_name] = []

    for frame_idx, frame in enumerate(range(start_frame, end_frame + 1)):
        scene.frame_set(frame)
        for bone_name in list(anim_data.keys()):
            if bone_name not in obj.pose.bones:
                anim_data[bone_name].append((1,1,1, 0,0,0,1, 0,0,0, 0.0))
                continue

            pbone = obj.pose.bones[bone_name]
            grp   = group_cache[bone_name]

            rx, ry, rz = grp["basis"]
            do_flip    = grp["flip"]
            ox, oy, oz = grp["offset"]
            mx, my, mz = grp["loc_map"]
            scale_div  = grp["scale_div"]
            prx, pry, prz = grp.get("post_rot", (0, 0, 0))

            C_mat = mathutils.Euler(
                (math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ'
            ).to_matrix().to_4x4()
            C_inv = C_mat.inverted()
            offset_quat_inv   = mathutils.Euler(
                (math.radians(ox),  math.radians(oy),  math.radians(oz)),  'XYZ'
            ).to_quaternion().inverted()
            post_rot_quat_inv = mathutils.Euler(
                (math.radians(prx), math.radians(pry), math.radians(prz)), 'XYZ'
            ).to_quaternion().inverted()

            if do_apose_correction and bone_name in APOSE_OFFSETS:
                ax, ay, az = APOSE_OFFSETS[bone_name]
                apose_quat_inv = mathutils.Euler(
                    (math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ'
                ).to_quaternion().inverted()
            else:
                apose_quat_inv = mathutils.Quaternion((1, 0, 0, 0))

            b_rot = pbone.rotation_quaternion.copy()
            # post_rot 역변환 (import 시 우측 곱한 것을 제거)
            b_rot = b_rot @ post_rot_quat_inv
            b_rot = apose_quat_inv @ b_rot

            is_root = bone_name in _FULLBODY_ROOT_BONES

            # ── 회전 변환 ─────────────────────────────────────────────────────
            M_blender = mathutils.Matrix.LocRotScale(mathutils.Vector((0, 0, 0)), b_rot, pbone.scale)
            M_engine   = C_inv @ M_blender @ C_mat
            _, e_rot, e_sca = M_engine.decompose()
            e_rot = e_rot @ offset_quat_inv

            qw, qx, qy, qz = e_rot.w, e_rot.x, e_rot.y, e_rot.z
            if do_flip:
                qy = -qy

            # ── 위치 변환 ─────────────────────────────────────────────────────
            if is_root:
                # 루트본: 포즈 위치 → 엔진 공간 (scale_div 적용)
                b_loc = pbone.location.copy()
                M_bl_loc = mathutils.Matrix.LocRotScale(b_loc, b_rot, pbone.scale)
                M_en_loc = C_inv @ M_bl_loc @ C_mat
                e_loc_root = M_en_loc.decompose()[0]
                px, py, pz = _inverse_loc_map(mx, my, mz, e_loc_root.x, e_loc_root.y, e_loc_root.z)
                if do_flip:
                    py = -py
                px, py, pz = px * scale_div, py * scale_div, pz * scale_div
            else:
                # 비루트본: 아마추어 레스트 위치 (캐시 사용)
                px, py, pz = rest_pos_cache.get(bone_name, (0.0, 0.0, 0.0))

            anim_data[bone_name].append(
                (e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 0.0)
            )

    # ── 6. 정적 뼈대(enc=2) 샘플 계산 ────────────────────────────────────────
    # IGNORE_BONES는 계산하지 않음 → C-블록 구축 시 템플릿 원본 데이터 사용
    scene.frame_set(start_frame)
    static_samples = {}
    for bone_name in static_bones:
        grp = group_cache[bone_name]
        static_samples[bone_name] = _get_enc2_sample(
            obj, bone_name, grp, do_apose_correction
        )

    # ── 7. 새 c_rel 값 계산 (dynamic_enc 기준) ───────────────────────────────
    new_c_rel = {}
    c_offset = 0
    for bone_name, enc_orig, c_rel_orig, *_ in _FULLBODY_CBLOCK_ORDER:
        enc = dynamic_enc[bone_name]
        new_c_rel[bone_name] = c_offset
        c_size = (total_frames * 44) if enc == 1 else 44
        c_offset += c_size + 4  # 4바이트 갭

    raw_size = c_offset - 4 + 20  # 마지막 갭 제외, 20바이트 패딩 추가

    # ── 8. 템플릿 패치 ────────────────────────────────────────────────────────
    buf = template

    struct.pack_into('<I', buf, 0x40, total_frames - 1)
    struct.pack_into('<I', buf, 0x54, raw_size)
    struct.pack_into('<I', buf, 0x58, raw_size)
    struct.pack_into('<I', buf, 0x5C, raw_size)

    for bone_name, enc_orig, c_rel_orig, t_tbl, tf4, tf6, tf7 in _FULLBODY_TRACK_INFO:
        enc = dynamic_enc[bone_name]
        nc  = new_c_rel[bone_name]
        sc   = total_frames if enc == 1 else 1
        c_sz = total_frames * 44 if enc == 1 else 44

        # encoding 필드 (field[3], 항상 offset=12)
        struct.pack_into('<I', buf, t_tbl + 12, enc)
        # sample_count
        struct.pack_into('<I', buf, t_tbl + tf4, sc)
        # c_rel (tf6==0 이면 Top처럼 기본값 0이므로 패치 불필요)
        if tf6 != 0:
            struct.pack_into('<I', buf, t_tbl + tf6, nc)
        # c_size
        struct.pack_into('<I', buf, t_tbl + tf7, c_sz)

    # ── 9. C-블록 구축 (dynamic_enc 기준) ────────────────────────────────────
    c_block = bytearray()
    for i, (bone_name, enc_orig, c_rel_orig, *_) in enumerate(_FULLBODY_CBLOCK_ORDER):
        enc     = dynamic_enc[bone_name]
        is_last = (i == len(_FULLBODY_CBLOCK_ORDER) - 1)

        if bone_name in IGNORE_BONES:
            # 템플릿 원본 데이터를 그대로 복사
            src_off = template_c_base + c_rel_orig
            c_block.extend(template_raw[src_off : src_off + 44])
        elif enc == 1:
            frames_data = anim_data.get(bone_name, [])
            while len(frames_data) < total_frames:
                frames_data.append(frames_data[-1] if frames_data else (1,1,1,0,0,0,1,0,0,0,0))
            for sample in frames_data:
                c_block.extend(struct.pack('<11f', *sample))
        else:
            sample = static_samples.get(bone_name, (1,1,1, 0,0,0,1, 0,0,0, 0.0))
            c_block.extend(struct.pack('<11f', *sample))

        if not is_last:
            c_block.extend(b'\x00' * 4)

    c_block.extend(b'\x00' * 20)

    # ── 9. 최종 파일 저장 ────────────────────────────────────────────────────
    with open(export_path, 'wb') as f:
        f.write(buf)
        f.write(c_block)

    # ── 10. 임시 베이크 액션 폐기 및 원본 복원 ───────────────────────────────
    if baked_action is not None:
        if obj.animation_data:
            obj.animation_data.action = original_action
        bpy.data.actions.remove(baked_action)
        print("[*] 임시 베이크 액션 폐기 완료, 원본 액션 복원됨")

    print(f"[+] Polaris [FULLBODY] FlatBuffers Export 완료! ({len(buf) + len(c_block)} bytes)")


# ==============================================================================
# 기타 카테고리 내보내기 (기존 커스텀 포맷)
# ==============================================================================
def _execute_export_custom(export_path, obj, anim_type, apply_apose, include_dummy):
    print(f"[*] Custom Format Export for {anim_type}")

    target_mask = CATEGORY_MASKS.get(anim_type)
    if anim_type == 'FACIAL':
        from .profiles_tk8 import MASK_FACIAL_EXCLUSIVE, MASK_FACIAL_DUMMY
        target_mask = MASK_FACIAL_EXCLUSIVE.union(MASK_FACIAL_DUMMY) if include_dummy else MASK_FACIAL_EXCLUSIVE
    elif anim_type == 'HAND':
        from .profiles_tk8 import MASK_HAND_L, MASK_HAND_R
        target_mask = MASK_HAND_L.union(MASK_HAND_R)

    scene = bpy.context.scene
    start_frame = int(scene.frame_start)
    end_frame   = int(scene.frame_end)
    total_frames = max(1, end_frame - start_frame + 1)

    export_bones = [pb.name for pb in obj.pose.bones
                    if (target_mask is None or pb.name in target_mask)]

    print(f"[*] 프레임 범위: {start_frame}~{end_frame} (총 {total_frames})")
    print(f"[*] 내보낼 뼈대 수: {len(export_bones)}")

    root_bones, target_groups = PROFILE_REGISTRY.get(anim_type, (set(), {}))
    do_apose_correction = apply_apose and anim_type in ('FULLBODY', 'SWING')
    export_data = {b: [] for b in export_bones}

    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        for bone_name in export_bones:
            pbone = obj.pose.bones[bone_name]
            selected_group = next(
                (g for g in target_groups.values() if bone_name in g["bones"]),
                DEFAULT_FALLBACK
            )
            rx, ry, rz = selected_group["basis"]
            do_flip    = selected_group["flip"]
            ox, oy, oz = selected_group["offset"]
            mx, my, mz = selected_group["loc_map"]
            scale_div  = selected_group["scale_div"]

            C_mat = mathutils.Euler(
                (math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ'
            ).to_matrix().to_4x4()
            C_inv = C_mat.inverted()
            offset_quat_inv = mathutils.Euler(
                (math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ'
            ).to_quaternion().inverted()

            if do_apose_correction and bone_name in APOSE_OFFSETS:
                ax, ay, az = APOSE_OFFSETS[bone_name]
                apose_quat_inv = mathutils.Euler(
                    (math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ'
                ).to_quaternion().inverted()
            else:
                apose_quat_inv = mathutils.Quaternion((1, 0, 0, 0))

            b_rot = pbone.rotation_quaternion.copy()
            b_rot = apose_quat_inv @ b_rot
            M_blender = mathutils.Matrix.LocRotScale(pbone.location, b_rot, pbone.scale)
            M_engine   = C_inv @ M_blender @ C_mat
            e_loc, e_rot, e_sca = M_engine.decompose()
            e_rot = e_rot @ offset_quat_inv

            qw, qx, qy, qz = e_rot.w, e_rot.x, e_rot.y, e_rot.z
            px, py, pz = _inverse_loc_map(mx, my, mz, e_loc.x, e_loc.y, e_loc.z)

            if do_flip:
                py = -py
                qy = -qy

            px, py, pz = px * scale_div, py * scale_div, pz * scale_div
            export_data[bone_name].append(
                (e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 0.0)
            )

    # 커스텀 바이너리 구축
    buffer = bytearray(b'\x00' * 0x98)
    struct.pack_into('<I', buffer, 0x40, total_frames - 1)
    struct.pack_into('<I', buffer, 0x94, len(export_bones))

    buffer.extend(b'\x00' * (len(export_bones) * 4))
    bone_c_offset_positions = []

    for i, b_name in enumerate(export_bones):
        current_a_offset = len(buffer)
        rel_offset = current_a_offset - (0x98 + i * 4)
        struct.pack_into('<I', buffer, 0x98 + i * 4, rel_offset)

        buffer.extend(b'\x00' * 0x10)
        rel_b_offset_pos = len(buffer)
        buffer.extend(struct.pack('<I', 0))

        b_name_bytes = b_name.encode('utf-8')
        name_len = len(b_name_bytes) + 1
        buffer.extend(struct.pack('<I', name_len))
        buffer.extend(b_name_bytes + b'\x00')
        pad_len = (4 - (len(buffer) % 4)) % 4
        buffer.extend(b'\x00' * pad_len)

        b_offset = len(buffer)
        rel_b_offset = b_offset - (current_a_offset + 0x10) + 8
        struct.pack_into('<I', buffer, rel_b_offset_pos, rel_b_offset)

        buffer.extend(b'\x00' * 0x0C)
        buffer.extend(struct.pack('<I', 0x24))
        buffer.extend(struct.pack('<I', 0))
        buffer.extend(struct.pack('<I', 1))
        buffer.extend(struct.pack('<I', total_frames))
        buffer.extend(struct.pack('<I', 0))

        c_offset_pos = len(buffer)
        buffer.extend(struct.pack('<I', 0))
        buffer.extend(struct.pack('<I', 0))
        bone_c_offset_positions.append(c_offset_pos)

    pad_len = (16 - (len(buffer) % 16)) % 16
    buffer.extend(b'\x00' * pad_len)
    first_c_ptr = len(buffer)
    struct.pack_into('<I', buffer, 0x50, first_c_ptr)

    for i, b_name in enumerate(export_bones):
        c_offset = len(buffer) - first_c_ptr
        struct.pack_into('<I', buffer, bone_c_offset_positions[i], c_offset)
        for frame_data in export_data[b_name]:
            buffer.extend(struct.pack('<11f', *frame_data))

    with open(export_path, 'wb') as f:
        f.write(buffer)

    print(f"[+] Polaris [{anim_type}] Custom Export 완료!")
