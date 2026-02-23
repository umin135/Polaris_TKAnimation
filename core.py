import bpy
import struct
import mathutils
import math
import os
from .profiles import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS

def read_uint32(f):
    data = f.read(4)
    if len(data) < 4: return 0
    return struct.unpack('<I', data)[0]

def execute_import(filepath, obj, anim_type, apply_apose=False): 
    if not obj.animation_data:
        obj.animation_data_create()
    
    if not obj.animation_data.action:
        obj.animation_data.action = bpy.data.actions.new(name=f"Polaris_{anim_type}_Action")
    else:
        action = obj.animation_data.action
        for fcurve in action.fcurves:
            action.fcurves.remove(fcurve)

    for pbone in obj.pose.bones:
        pbone.location = (0, 0, 0)
        pbone.rotation_quaternion = (1, 0, 0, 0)
        pbone.rotation_euler = (0, 0, 0)
        pbone.scale = (1, 1, 1)

    file_size = os.path.getsize(filepath)
    missing_bones = [] 

    root_bones, target_groups = PROFILE_REGISTRY.get(anim_type, (set(), {}))

    do_apose_correction = apply_apose and anim_type in ('FULLBODY', 'EXTRA')

    with open(filepath, 'rb') as f:
        f.seek(0x40)
        total_frame_count = read_uint32(f)
        f.seek(0x50)
        first_c_ptr = read_uint32(f)
        f.seek(0x94)
        bone_count = read_uint32(f)
        
        f.seek(0x98)
        bone_offsets = []
        for _ in range(bone_count):
            curr = f.tell()
            rel_offset = read_uint32(f)
            bone_offsets.append(curr + rel_offset)
            
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = total_frame_count
        
        for i, a_offset in enumerate(bone_offsets):
            f.seek(a_offset)
            curr = f.tell()
            f.seek(curr + 0x10)
            rel_b_offset = read_uint32(f)
            block_b_offset = (curr + 0x10) + rel_b_offset - 8
            
            f.seek(a_offset + 0x14)
            name_len = read_uint32(f)
            bone_name = f.read(name_len).decode('utf-8', errors='ignore').strip('\x00')
            
            if bone_name not in obj.pose.bones:
                missing_bones.append(bone_name)
                continue
                
            pbone = obj.pose.bones[bone_name]
            pbone.rotation_mode = 'QUATERNION'
            
            f.seek(block_b_offset + 0xC)
            indicator = read_uint32(f)
            f.seek(block_b_offset + 0x18)
            bone_frames = read_uint32(f)
            if bone_frames == 0: bone_frames = 1
            
            if indicator == 0x20:
                final_c_start = first_c_ptr
            elif indicator == 0x24:
                f.seek(block_b_offset + 0x20)
                c_rel = read_uint32(f)
                final_c_start = first_c_ptr + c_rel
            else:
                continue

            if final_c_start >= file_size:
                continue

            selected_group = None
            for group_name, group_data in target_groups.items():
                if bone_name in group_data["bones"]:
                    selected_group = group_data
                    break
                    
            if not selected_group:
                selected_group = DEFAULT_FALLBACK
                
            rx, ry, rz = selected_group["basis"]
            do_flip = selected_group["flip"]
            ox, oy, oz = selected_group["offset"]
            mx, my, mz = selected_group["loc_map"]
            scale_div = selected_group["scale_div"]

            C_mat = mathutils.Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix().to_4x4()
            C_inv = C_mat.inverted()

            f.seek(final_c_start)
            
            for frame in range(bone_frames):
                raw_chunk = f.read(44)
                if len(raw_chunk) < 44:
                    break
                    
                vals = struct.unpack('<11f', raw_chunk)
                sx, sy, sz = vals[0:3]
                qx, qy, qz, qw = vals[3:7]
                
                px = vals[7] / scale_div
                py = vals[8] / scale_div
                pz = vals[9] / scale_div
                
                if do_flip:
                    py, qy = -py, -qy
                    
                loc_dict = {'x': px, 'y': py, 'z': pz, '-x': -px, '-y': -py, '-z': -pz}
                mapped_px = loc_dict[mx]
                mapped_py = loc_dict[my]
                mapped_pz = loc_dict[mz]
                    
                anim_loc = mathutils.Vector((mapped_px, mapped_py, mapped_pz))
                anim_quat = mathutils.Quaternion((qw, qx, qy, qz))
                
                # 원본 엔진 오프셋 적용
                offset_quat = mathutils.Euler((math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ').to_quaternion()
                anim_quat = anim_quat @ offset_quat
                
                anim_scale = mathutils.Vector((sx, sy, sz))
                M_engine = mathutils.Matrix.LocRotScale(anim_loc, anim_quat, anim_scale)
                
                # 블렌더 공간 변환
                M_blender = C_mat @ M_engine @ C_inv
                b_loc, b_rot, b_sca = M_blender.decompose()
                
                # =======================================================
                # [수학적 완벽함] Rest Pose Apply 시뮬레이션
                # =======================================================
                if do_apose_correction and bone_name in APOSE_OFFSETS:
                    ax, ay, az = APOSE_OFFSETS[bone_name]
                    apose_quat = mathutils.Euler((math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ').to_quaternion()
                    
                    # 애니메이션(b_rot)의 '왼쪽'에 곱함으로써, apose_quat을 이 뼈대의 새로운 축(Rest Pose)으로 만듭니다!
                    b_rot = apose_quat @ b_rot
                # =======================================================
                
                if bone_name in root_bones:
                    pbone.location = b_loc
                    pbone.keyframe_insert(data_path="location", frame=frame)
                
                pbone.rotation_quaternion = b_rot
                pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
    return missing_bones