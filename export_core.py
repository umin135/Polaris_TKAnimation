import bpy
import struct
import mathutils
import math
import os
from .profiles import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS, CATEGORY_MASKS

def execute_export(export_path, obj, anim_type, apply_apose=True, include_dummy=False):
    print(f"\n[*] Starting Polaris Export (From Scratch) for {anim_type}")
    print(f"[*] Output File: {export_path}")
    
    if anim_type == 'CAMERA':
        print("[!] Camera export from scratch is not supported yet (requires 16-bit bounding box structures).")
        return
        
    # 1. 마스크를 통해 내보낼 뼈대 필터링
    target_mask = CATEGORY_MASKS.get(anim_type)
    if anim_type == 'FACIAL':
        from .profiles import MASK_FACIAL_EXCLUSIVE, MASK_FACIAL_DUMMY
        target_mask = MASK_FACIAL_EXCLUSIVE.union(MASK_FACIAL_DUMMY) if include_dummy else MASK_FACIAL_EXCLUSIVE
    elif anim_type == 'HAND':
        from .profiles import MASK_HAND_L, MASK_HAND_R
        target_mask = MASK_HAND_L.union(MASK_HAND_R)
        
    scene = bpy.context.scene
    start_frame = int(scene.frame_start)
    end_frame = int(scene.frame_end)
    total_frames = max(1, end_frame - start_frame + 1)
    
    export_bones = [pb.name for pb in obj.pose.bones if (target_mask is None or pb.name in target_mask)]
    
    print(f"[*] Exporting Frames: {start_frame} to {end_frame} (Total: {total_frames})")
    print(f"[*] Total Bones to Export: {len(export_bones)}")

    root_bones, target_groups = PROFILE_REGISTRY.get(anim_type, (set(), {}))
    do_apose_correction = apply_apose and anim_type in ('FULLBODY', 'SWING')
    export_data = {b: [] for b in export_bones}

    def reverse_map(axis_str, mapped_val):
        return mapped_val if not axis_str.startswith('-') else -mapped_val

    # 2. 지정된 프레임 구간(Start ~ End) 데이터 캡처 및 역연산
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        for bone_name in export_bones:
            pbone = obj.pose.bones[bone_name]
            
            selected_group = next((g for g in target_groups.values() if bone_name in g["bones"]), DEFAULT_FALLBACK)
            rx, ry, rz = selected_group["basis"]
            do_flip = selected_group["flip"]
            ox, oy, oz = selected_group["offset"]
            mx, my, mz = selected_group["loc_map"]
            scale_div = selected_group["scale_div"]

            C_mat = mathutils.Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix().to_4x4()
            C_inv = C_mat.inverted()
            offset_quat_inv = mathutils.Euler((math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ').to_quaternion().inverted()
            
            if do_apose_correction and bone_name in APOSE_OFFSETS:
                ax, ay, az = APOSE_OFFSETS[bone_name]
                apose_quat_inv = mathutils.Euler((math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ').to_quaternion().inverted()
            else:
                apose_quat_inv = mathutils.Quaternion((1, 0, 0, 0))

            b_rot = pbone.rotation_quaternion.copy()
            b_rot = apose_quat_inv @ b_rot
            M_blender = mathutils.Matrix.LocRotScale(pbone.location, b_rot, pbone.scale)
            
            # 엔진 좌표계로 역변환 (Inverse Transform)
            M_engine = C_inv @ M_blender @ C_mat
            e_loc, e_rot, e_sca = M_engine.decompose()
            e_rot = e_rot @ offset_quat_inv
            
            qw, qx, qy, qz = e_rot.w, e_rot.x, e_rot.y, e_rot.z
            px, py, pz = reverse_map(mx, e_loc.x), reverse_map(my, e_loc.y), reverse_map(mz, e_loc.z)
            
            if do_flip: py, qy = -py, -qy
            px, py, pz = px * scale_div, py * scale_div, pz * scale_div
            
            # 철권 8 엔진 규격(44바이트 = 11 Floats) 맞춤 데이터
            export_data[bone_name].append((e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 1.0))

    # 3. 바이너리 빌드 (무에서 유를 창조하는 메모리 매핑)
    buffer = bytearray(b'\x00' * 0x98) # 헤더 여백
    struct.pack_into('<I', buffer, 0x40, total_frames)
    struct.pack_into('<I', buffer, 0x94, len(export_bones))
    
    # 포인터 배열 공간 할당
    buffer.extend(b'\x00' * (len(export_bones) * 4))
    bone_c_offset_positions = []

    # A-Block (뼈대 이름) 및 B-Block (메타데이터) 구축
    for i, b_name in enumerate(export_bones):
        current_a_offset = len(buffer)
        
        # 포인터 업데이트
        rel_offset = current_a_offset - (0x98 + i * 4)
        struct.pack_into('<I', buffer, 0x98 + i * 4, rel_offset)
        
        # [A-Block]
        buffer.extend(b'\x00' * 0x10)
        rel_b_offset_pos = len(buffer)
        buffer.extend(struct.pack('<I', 0)) # Placeholder for B offset
        
        b_name_bytes = b_name.encode('utf-8')
        name_len = len(b_name_bytes) + 1 # Include null terminator
        buffer.extend(struct.pack('<I', name_len))
        buffer.extend(b_name_bytes + b'\x00')
        
        pad_len = (4 - (len(buffer) % 4)) % 4
        buffer.extend(b'\x00' * pad_len)
        
        # [B-Block]
        b_offset = len(buffer)
        rel_b_offset = b_offset - (current_a_offset + 0x10) + 8
        struct.pack_into('<I', buffer, rel_b_offset_pos, rel_b_offset)
        
        buffer.extend(b'\x00' * 0x0C)
        buffer.extend(struct.pack('<I', 0x24)) # 0x0C: Indicator
        buffer.extend(struct.pack('<I', 0))
        buffer.extend(struct.pack('<I', 1))    # 0x14: Anim Flag (1 = FBF 비압축)
        buffer.extend(struct.pack('<I', total_frames))
        buffer.extend(struct.pack('<I', 0))
        
        c_offset_pos = len(buffer)
        buffer.extend(struct.pack('<I', 0)) # Placeholder for C offset
        buffer.extend(struct.pack('<I', 0))
        
        bone_c_offset_positions.append(c_offset_pos)

    # C-Block 시작 전 16바이트 정렬(Padding)
    pad_len = (16 - (len(buffer) % 16)) % 16
    buffer.extend(b'\x00' * pad_len)
    
    first_c_ptr = len(buffer)
    struct.pack_into('<I', buffer, 0x50, first_c_ptr)
    
    # [C-Block] 프레임 데이터 (Raw Floats) 적재
    for i, b_name in enumerate(export_bones):
        c_offset = len(buffer) - first_c_ptr
        struct.pack_into('<I', buffer, bone_c_offset_positions[i], c_offset)
        
        for frame_data in export_data[b_name]:
            buffer.extend(struct.pack('<11f', *frame_data))
            
    # 최종 바이너리 저장
    with open(export_path, 'wb') as f:
        f.write(buffer)
        
    print(f"[+] Polaris [{anim_type}] FBF Export (From Scratch) Completed Successfully!")