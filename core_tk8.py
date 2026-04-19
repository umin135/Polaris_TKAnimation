import bpy
import struct
import mathutils
import math
import os
import re

from .profiles_tk8 import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS, CATEGORY_MASKS, IGNORE_BONES

halfpi = math.pi / 2

# =======================================================
# 디버그 플래그
# True 로 바꾸면 루트본 첫 프레임 값을 콘솔에 출력합니다.
# 위치 튜닝 시 켜두고, 확인 후 False 로 되돌리세요.
# =======================================================
DEBUG_ROOT = False

def read_uint32(f):
    data = f.read(4)
    if len(data) < 4: return 0
    return struct.unpack('<I', data)[0]

class BitReader:
    def __init__(self, data_bytes):
        self.data = data_bytes
        self.bit_pos = 0

    def read_bits(self, num_bits):
        if num_bits == 0: return 0
        value = 0
        bits_read = 0
        while bits_read < num_bits:
            byte_idx = self.bit_pos // 8
            bit_in_byte = self.bit_pos % 8
            if byte_idx >= len(self.data): break
            current_byte = self.data[byte_idx]
            bits_available = 8 - bit_in_byte
            bits_to_read_now = min(num_bits - bits_read, bits_available)
            extracted = (current_byte >> bit_in_byte) & ((1 << bits_to_read_now) - 1)
            value |= (extracted << bits_read)
            self.bit_pos += bits_to_read_now
            bits_read += bits_to_read_now
        return value

# 💡 함수 이름이 정확히 import_tk8_anim 이어야 합니다.
def import_tk8_anim(filepath, obj, anim_type, apply_apose, include_dummy):
    print(f"[*] Started TK8 Import Process: {filepath}")
    file_size = os.path.getsize(filepath)

    if not obj.animation_data:
        obj.animation_data_create()
    if not obj.animation_data.action:
        obj.animation_data.action = bpy.data.actions.new(name="Polaris_Action")
    action = obj.animation_data.action

    target_mask = CATEGORY_MASKS.get(anim_type)

    if anim_type == 'FACIAL':
        from .profiles_tk8 import MASK_FACIAL_EXCLUSIVE, MASK_FACIAL_DUMMY
        if include_dummy:
            target_mask = MASK_FACIAL_EXCLUSIVE.union(MASK_FACIAL_DUMMY)
        else:
            target_mask = MASK_FACIAL_EXCLUSIVE

    elif anim_type == 'HAND':
        has_l_hand = False
        has_r_hand = False
        with open(filepath, 'rb') as f:
            f.seek(0x94)
            peek_bone_count = read_uint32(f)
            peek_offsets = []
            for i in range(peek_bone_count):
                f.seek(0x98 + (i * 4))
                curr = f.tell()
                peek_offsets.append(curr + read_uint32(f))
            for a_off in peek_offsets:
                f.seek(a_off + 0x14)
                n_len = read_uint32(f)
                b_name = f.read(n_len).decode('utf-8', errors='ignore').strip('\x00')
                if b_name.startswith('L_'): has_l_hand = True
                if b_name.startswith('R_'): has_r_hand = True
                if has_l_hand and has_r_hand: break
        
        from .profiles_tk8 import MASK_HAND_L, MASK_HAND_R
        if has_l_hand and not has_r_hand: target_mask = MASK_HAND_L
        elif has_r_hand and not has_l_hand: target_mask = MASK_HAND_R
        else: target_mask = MASK_HAND_L.union(MASK_HAND_R)

    if action and target_mask:
        for fcurve in list(action.fcurves):
            match = re.search(r'pose\.bones\["([^"]+)"\]', fcurve.data_path)
            if match:
                bone_name = match.group(1)
                if bone_name in target_mask:
                    action.fcurves.remove(fcurve)
    elif action and not target_mask and anim_type != 'CAMERA':
        for fcurve in list(action.fcurves):
            action.fcurves.remove(fcurve)

    missing_bones = [] 

    if anim_type == 'CAMERA':
        with open(filepath, 'rb') as f:
            f.seek(0x98)
            bone_count = read_uint32(f)
            if bone_count == 0: return []
            f.seek(0x9c)
            curr = f.tell()
            rel_offset = read_uint32(f)
            first_a_offset = curr + rel_offset
            f.seek(first_a_offset + 0x10)
            curr_magic = f.tell()
            rel_b_offset = read_uint32(f)
            block_b_offset = (curr_magic + 0x10) + rel_b_offset - 8
            f.seek(block_b_offset + 0x18)
            bone_frames = read_uint32(f)
            if bone_frames == 0: bone_frames = 1
            f.seek(block_b_offset + 0x20)
            str_len = read_uint32(f)
            padded_len = (str_len + 3) & ~3
            final_c_start = block_b_offset + 0x24 + padded_len
            
            target_offsets = [0x0a8, 0x0d8, 0x0e8, 0x0f8]
            bounding_boxes = []
            for offset in target_offsets:
                f.seek(final_c_start + offset)
                c_min = struct.unpack('<f', f.read(4))[0]
                c_max = struct.unpack('<f', f.read(4))[0]
                bounding_boxes.append((c_min, c_max))

            f.seek(final_c_start + 0x13c)
            raw_packed = f.read(4 * bone_frames * 2)
            for i in range(4):
                prop_name = f"Cam_Ch{i+1}"
                obj[prop_name] = 0.0
            for channel_idx in range(4):
                c_min, c_max = bounding_boxes[channel_idx]
                prop_name = f"Cam_Ch{channel_idx+1}"
                for frame in range(bone_frames):
                    data_idx = (channel_idx * bone_frames) + frame
                    if data_idx * 2 + 2 > len(raw_packed): break
                    val_16bit = struct.unpack('<H', raw_packed[data_idx*2 : (data_idx+1)*2])[0]
                    ratio = val_16bit / 65535.0
                    decoded_float = c_min + (c_max - c_min) * ratio
                    obj[prop_name] = decoded_float
                    obj.keyframe_insert(data_path=f'["{prop_name}"]', frame=frame)
        return missing_bones

    for pbone in obj.pose.bones:
        if target_mask is None or pbone.name in target_mask:
            pbone.location = (0, 0, 0)
            pbone.rotation_quaternion = (1, 0, 0, 0)
            pbone.rotation_euler = (0, 0, 0)
            pbone.scale = (1, 1, 1)

    root_bones, target_groups = PROFILE_REGISTRY.get(anim_type, (set(), {}))
    do_apose_correction = apply_apose and anim_type in ('FULLBODY', 'SWING')

    with open(filepath, 'rb') as f:
        f.seek(0x40)
        total_frame_count = read_uint32(f)
        f.seek(0x50)
        first_c_ptr = read_uint32(f)
        f.seek(0x94)
        bone_count = read_uint32(f)
        
        bone_offsets = []
        for i in range(bone_count):
            f.seek(0x98 + (i * 4))
            curr = f.tell()
            rel_offset = read_uint32(f)
            bone_offsets.append(curr + rel_offset)
            
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = total_frame_count
        
        for a_offset in bone_offsets:
            f.seek(a_offset)
            curr = f.tell()
            f.seek(curr + 0x10)
            rel_b_offset = read_uint32(f)
            block_b_offset = (curr + 0x10) + rel_b_offset - 8
            
            f.seek(a_offset + 0x14)
            name_len = read_uint32(f)
            bone_name = f.read(name_len).decode('utf-8', errors='ignore').strip('\x00')
            
            if bone_name in IGNORE_BONES:
                continue
            if bone_name not in obj.pose.bones:
                missing_bones.append(bone_name)
                continue
            if target_mask is not None and bone_name not in target_mask:
                continue

            pbone = obj.pose.bones[bone_name]
            pbone.rotation_mode = 'QUATERNION'

            f.seek(block_b_offset + 0xC)
            indicator = read_uint32(f)

            # B-block schema 버전 자동 감지:
            # OLD schema: anim_flag=+0x14, bone_frames=+0x18, c_rel=+0x20
            # NEW schema: anim_flag=+0x04, bone_frames=+0x08, c_rel=+0x10 (또는 +0x18 for 0x34)
            # indicator 0x34/0x38은 new schema 전용이므로 즉시 판별 가능.
            # 0x20/0x24의 경우 +0x14 값이 {1,2,3} 범위인지로 판별.
            if indicator in (0x34, 0x38):
                new_schema = True
            else:
                f.seek(block_b_offset + 0x14)
                anim_flag_old = read_uint32(f)
                new_schema = anim_flag_old not in (1, 2, 3)

            if new_schema:
                f.seek(block_b_offset + 0x04)
                anim_flag = read_uint32(f)
                f.seek(block_b_offset + 0x08)
                bone_frames = read_uint32(f)
            else:
                anim_flag = anim_flag_old
                f.seek(block_b_offset + 0x18)
                bone_frames = read_uint32(f)

            is_keyframed = (anim_flag == 3)
            if bone_frames == 0: bone_frames = 1

            if indicator == 0x20:
                final_c_start = first_c_ptr
            elif indicator == 0x24:
                c_rel_off = 0x10 if new_schema else 0x20
                f.seek(block_b_offset + c_rel_off)
                final_c_start = first_c_ptr + read_uint32(f)
            elif indicator == 0x38:
                f.seek(block_b_offset + 0x10)
                final_c_start = first_c_ptr + read_uint32(f)
            elif indicator == 0x34:
                f.seek(block_b_offset + 0x18)
                final_c_start = first_c_ptr + read_uint32(f)
            else:
                continue

            if final_c_start >= file_size: continue

            selected_group = None
            for group_name, group_data in target_groups.items():
                if bone_name in group_data["bones"]:
                    selected_group = group_data
                    break
            if not selected_group: selected_group = DEFAULT_FALLBACK
                
            rx, ry, rz = selected_group["basis"]
            do_flip     = selected_group["flip"]
            ox, oy, oz  = selected_group["offset"]
            mx, my, mz  = selected_group["loc_map"]
            scale_div   = selected_group["scale_div"]
            prx, pry, prz = selected_group.get("post_rot", (0, 0, 0))
            is_root     = bone_name in root_bones

            C_mat = mathutils.Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix().to_4x4()
            C_inv = C_mat.inverted()
            offset_quat   = mathutils.Euler((math.radians(ox),  math.radians(oy),  math.radians(oz)),  'XYZ').to_quaternion()
            post_rot_quat = mathutils.Euler((math.radians(prx), math.radians(pry), math.radians(prz)), 'XYZ').to_quaternion()

            def _process_frame(px_raw, py_raw, pz_raw, qx, qy, qz, qw, sx, sy, sz, frame):
                """엔진 raw 값 → Blender 포즈 적용 및 키프레임 삽입."""
                px = px_raw / scale_div
                py = py_raw / scale_div
                pz = pz_raw / scale_div

                if do_flip:
                    py  = -py
                    qy  = -qy

                # 축 재매핑 (loc_map)
                loc_src = {'x': px, '-x': -px, 'y': py, '-y': -py, 'z': pz, '-z': -pz}
                anim_loc  = mathutils.Vector((loc_src[mx], loc_src[my], loc_src[mz]))
                anim_quat = mathutils.Quaternion((qw, qx, qy, qz)) @ offset_quat
                anim_scale = mathutils.Vector((sx, sy, sz))

                # DEBUG: 루트본 첫 프레임 raw → 변환 전 값 출력
                if DEBUG_ROOT and is_root and frame == 0:
                    print(f"[DEBUG ROOT] bone={bone_name}  raw_pos=({px_raw:.4f}, {py_raw:.4f}, {pz_raw:.4f})"
                          f"  scaled=({px:.4f}, {py:.4f}, {pz:.4f})"
                          f"  mapped=({anim_loc.x:.4f}, {anim_loc.y:.4f}, {anim_loc.z:.4f})"
                          f"  quat=({qw:.4f}, {qx:.4f}, {qy:.4f}, {qz:.4f})")

                # 좌표계 변환: C_mat @ M_engine @ C_inv
                M_engine  = mathutils.Matrix.LocRotScale(anim_loc, anim_quat, anim_scale)
                M_blender = C_mat @ M_engine @ C_inv
                b_loc, b_rot, _ = M_blender.decompose()

                if DEBUG_ROOT and is_root and frame == 0:
                    print(f"[DEBUG ROOT] bone={bone_name}  blender_loc=({b_loc.x:.4f}, {b_loc.y:.4f}, {b_loc.z:.4f})")

                # A-Pose 보정
                if do_apose_correction and bone_name in APOSE_OFFSETS:
                    ax, ay, az = APOSE_OFFSETS[bone_name]
                    b_rot = mathutils.Euler((math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ').to_quaternion() @ b_rot

                # post_rot: 로컬 우측 보정 (basis로 표현 불가한 축 정렬 오류 수정용)
                b_rot = b_rot @ post_rot_quat

                if is_root:
                    pbone.location = b_loc
                    pbone.keyframe_insert(data_path="location", frame=frame)

                pbone.rotation_quaternion = b_rot
                pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

            # --------------------------------------------------
            # 압축(bitstream) 모드
            # --------------------------------------------------
            if is_keyframed:
                f.seek(final_c_start)
                header_chunk  = f.read(16)
                # C-block 헤더 레이아웃 (16바이트):
                #   [0:2]  magic       = 0x0004 (고정)
                #   [2:4]  mode        = 6(일반 본) / 10(루트 모션 본)
                #   [4:6]  codec_flags = 0x00A0 (Transform) / 0x0020 (FOV)
                #   [6:8]  unit_count  = 프레임당 비트 수 (bits_per_frame)
                #   [8:12] header_size = payload(bitstream) 시작 오프셋
                #   [12:16]frame_count = 프레임 수 (B-block 값과 동일)
                bits_per_frame   = struct.unpack('<H', header_chunk[6:8])[0]
                header_size      = struct.unpack('<I', header_chunk[8:12])[0]  # = bitstream 시작
                # base_frame은 header 끝 44바이트 앞에 위치
                base_frame_offset = header_size - 44
                num_tracks        = (base_frame_offset - 0x10) // 16

                channels_info = []
                f.seek(final_c_start + 0x10)
                for _ in range(num_tracks):
                    c_min, c_max, c_bits, c_idx = struct.unpack('<ffII', f.read(16))
                    if c_max == c_min: c_bits = 0   # 정확히 동일 → 비트스트림에 없음
                    elif c_bits > 32:  c_bits = 0   # 손상된 값 방어
                    channels_info.append({"min": c_min, "max": c_max, "bits": c_bits, "idx": c_idx})

                f.seek(final_c_start + base_frame_offset)
                base_frame = list(struct.unpack('<11f', f.read(44)))
                f.seek(final_c_start + header_size)
                bitstream_data = f.read(bone_frames * num_tracks * 4)
                reader = BitReader(bitstream_data)

                c_mode = struct.unpack('<H', header_chunk[2:4])[0]
                is_root_motion_bone = (c_mode == 0x000A)

                # mode=0x000A(루트 모션 본)에서 채널 테이블 인덱스가 +1 오프셋:
                #   ch6 → comp[7] (posX),  ch7 → comp[8] (posY),  ch8 → comp[9] (posZ)
                #   ch6 슬롯에 posX 값이 들어오므로 qw는 항상 유도(derive)해야 함.
                # 일반 본(mode=6)은 기존 방식 유지: ch6 = qw, ch7-9 = pos.
                if is_root_motion_bone:
                    has_qw = False
                else:
                    has_qw = (len(channels_info) > 6 and channels_info[6]["bits"] > 0)

                # bits_per_frame 헤더값과 활성채널 비트합 비교로 부호비트 존재 여부를 판단
                sum_active_bits = sum(ch["bits"] for ch in channels_info if ch["bits"] > 0)
                sign_bit_per_frame = (bits_per_frame == sum_active_bits + 1)

                # 프레임 인터리브 방식: 프레임마다 모든 활성 채널 → qw 부호비트
                for frame in range(bone_frames):
                    comp = base_frame[:]
                    for idx, ch in enumerate(channels_info):
                        if ch["bits"] > 0:
                            max_val = (1 << ch["bits"]) - 1
                            raw = reader.read_bits(ch["bits"])
                            decoded = ch["min"] + (raw / float(max_val)) * (ch["max"] - ch["min"])
                            # mode=0x000A: 위치 채널(idx>=6)은 comp[idx+1]에 기록
                            if is_root_motion_bone and idx >= 6:
                                if idx + 1 < len(comp):
                                    comp[idx + 1] = decoded
                            else:
                                comp[idx] = decoded

                    sx, sy, sz = comp[0], comp[1], comp[2]
                    qx, qy, qz = comp[3], comp[4], comp[5]

                    if has_qw:
                        qw = comp[6]
                    else:
                        dot = qx*qx + qy*qy + qz*qz
                        if sign_bit_per_frame:
                            sign_bit = reader.read_bits(1)
                            sign = -1.0 if sign_bit else 1.0
                        else:
                            sign = math.copysign(1.0, base_frame[6])
                        qw = sign * math.sqrt(max(0.0, 1.0 - dot))

                    _process_frame(comp[7], comp[8], comp[9], qx, qy, qz, qw, sx, sy, sz, frame)

            # --------------------------------------------------
            # FBF (비압축) 모드
            # --------------------------------------------------
            else:
                f.seek(final_c_start)
                for frame in range(bone_frames):
                    raw_chunk = f.read(44)
                    if len(raw_chunk) < 44: break
                    vals = struct.unpack('<11f', raw_chunk)
                    # 샘플 레이아웃: Scale(0-2), Quat XYZW(3-6), Pos(7-9), Pad(10)
                    sx, sy, sz         = vals[0], vals[1], vals[2]
                    qx, qy, qz, qw     = vals[3], vals[4], vals[5], vals[6]
                    px_raw, py_raw, pz_raw = vals[7], vals[8], vals[9]

                    _process_frame(px_raw, py_raw, pz_raw, qx, qy, qz, qw, sx, sy, sz, frame)
                
    return missing_bones