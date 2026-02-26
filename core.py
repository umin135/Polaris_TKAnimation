import bpy
import struct
import mathutils
import math
import os
import re
from .profiles import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS, CATEGORY_MASKS

halfpi = math.pi / 2

# =======================================================
# 🧮 TK7 회전(Rotation) 수학 유틸리티 (Kilo 스크립트 완벽 이식)
# =======================================================
def kilo_get_quat(roll, pitch, yaw):
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return [qx, qy, qz, qw]

def kilo_quat_to_mat(Q):
    q0, q1, q2, q3 = Q[0], Q[1], Q[2], Q[3]
    r00 = 2 * (q0 * q0 + q1 * q1) - 1
    r01 = 2 * (q1 * q2 - q0 * q3)
    r02 = 2 * (q1 * q3 + q0 * q2)
    r10 = 2 * (q1 * q2 + q0 * q3)
    r11 = 2 * (q0 * q0 + q2 * q2) - 1
    r12 = 2 * (q2 * q3 - q0 * q1)
    r20 = 2 * (q1 * q3 - q0 * q2)
    r21 = 2 * (q2 * q3 + q0 * q1)
    r22 = 2 * (q0 * q0 + q3 * q3) - 1
    return [[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]]

def transpose_3x3(m):
    return [
        [m[0][0], m[1][0], m[2][0]],
        [m[0][1], m[1][1], m[2][1]],
        [m[0][2], m[1][2], m[2][2]]
    ]

def matmul_3x3(A, B):
    return [
        [sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]

def clamp(num, min_value, max_value):
    return max(min(num, max_value), min_value)

def kilo_get_rot_mode1(te):
    m11, m12, m13 = te[0][0], te[0][1], te[0][2]
    m21, m22, m23 = te[1][0], te[1][1], te[1][2]
    m31, m32, m33 = te[2][0], te[2][1], te[2][2]
    x = math.asin( -clamp( m23, -1, 1 ) )
    if abs( m23 ) < 0.9999999:
        y = math.atan2( m13, m33 )
        z = math.atan2( m21, m22 )
    else:
        y = math.atan2( -m31, m11 )
        z = 0
    return x, y, z

def convertArmToBlenderXYZ(x, y, z):
    orig_quat = kilo_get_quat(-halfpi, halfpi, 0)
    orig_mat = kilo_quat_to_mat(orig_quat)
    orig_mat_inv = transpose_3x3(orig_mat) # Rotation matrix inverse is transpose
    
    quat = kilo_get_quat(x, y, z)
    mat = kilo_quat_to_mat(quat)
    
    res_mat = matmul_3x3(mat, orig_mat_inv)
    rx, ry, rz = kilo_get_rot_mode1(res_mat)
    
    return -rz, ry, -rx

def apply_tk7_axis_correction(b_id, x, y, z):
    if b_id == 3: return (z, y, -x) # Base
    elif b_id == 4: return (z - halfpi, y, -x) # Spine1
    elif b_id == 5: return (z + halfpi, y, -x) # Hip
    elif b_id == 7: return (z, y, -x) # Neck
    elif b_id == 8: return (x, y - halfpi, z - halfpi) # Head
    elif b_id == 9: # R_Shoulder
        rx, ry, rz = convertArmToBlenderXYZ(x, y, z)
        return (rx, ry, rz)
    elif b_id == 10: return (-x - halfpi, -z, -y) # R_Arm
    elif b_id == 11: return (-x, y, -z) # R_ForeArm
    elif b_id == 12: return (x - halfpi, z, -y) # R_Hand
    elif b_id == 13: # L_Shoulder
        rx, ry, rz = convertArmToBlenderXYZ(x, y, z)
        return (-rx, ry, rz + math.pi)
    elif b_id == 14: return (x + halfpi, -z, y) # L_Arm
    elif b_id == 15: return (x, y, z) # L_ForeArm
    elif b_id == 16: return (-x + halfpi, -z, -y) # L_Hand
    elif b_id in (17, 18, 19, 20, 21, 22): # Legs & Feet
        return (z, y, -x)
    return (x, y, z)

# =======================================================
# 🚀 메인 임포트 로직
# =======================================================
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

def execute_import(filepath, obj, anim_type, apply_apose=False, include_dummy=False): 
    file_size = os.path.getsize(filepath)
    
    if anim_type.startswith('TK7_'):
        print(f"[*] Started TK7 Import Process: {filepath}")
        
        with open(filepath, 'rb') as f:
            magic = f.read(2)
            if magic in (b'\x00\xC8', b'\x00\x64'): endian = '>'
            elif magic in (b'\xC8\x00', b'\x64\x00'): endian = '<'
            else: return []
                
            f.seek(0)
            header = f.read(8)
            sig, p_count, frame_offset = struct.unpack(endian + 'HHI', header)
            
            tk7_bones = {
                0: "Top", 1: "Trans", 2: "HARA_ROT1", 3: "BASE",
                4: "Spine1", 5: "Hip", 6: "Spine_Flex", 7: "Neck",
                8: "Head", 9: "R_Shoulder", 10: "R_Arm", 11: "R_ForeArm",
                12: "R_Hand", 13: "L_Shoulder", 14: "L_Arm", 15: "L_ForeArm",
                16: "L_Hand", 17: "R_UpLeg", 18: "R_Leg", 19: "R_Foot",
                20: "L_UpLeg", 21: "L_Leg", 22: "L_Foot"
            }
            missing_tk7_bones = []
            
            if sig in (0x00C8, 0xC800):
                print(f"[*] TK7 FBF Format Detected (Big/Little Endian Safe)")
                
                f.seek(8)
                bone_ids = [struct.unpack(endian + 'I', f.read(4))[0] for _ in range(p_count)]
                
                frame_size = p_count * 12 # FBF는 무조건 관절당 12바이트(X,Y,Z)
                total_frames = (file_size - frame_offset) // frame_size
                
                f.seek(frame_offset)
                
                if not obj.animation_data: obj.animation_data_create()
                if not obj.animation_data.action: obj.animation_data.action = bpy.data.actions.new(name="TK7_Action")
                
                bpy.context.scene.frame_start = 0
                bpy.context.scene.frame_end = total_frames
                
                for frame in range(total_frames):
                    raw_frame = f.read(frame_size)
                    if len(raw_frame) < frame_size: break
                    
                    offset = 0
                    for b_id in bone_ids:
                        b_name = tk7_bones.get(b_id, f"Unknown_{b_id}")
                        x, y, z = struct.unpack(endian + 'fff', raw_frame[offset:offset+12])
                        offset += 12
                            
                        if b_name not in obj.pose.bones:
                            if b_name not in missing_tk7_bones: missing_tk7_bones.append(b_name)
                            continue
                            
                        pbone = obj.pose.bones[b_name]
                        
                        if b_id == 0: 
                            pbone.location[0] += x / 1000.0
                            pbone.location[2] += -z / 1000.0
                            pbone.keyframe_insert(data_path="location", frame=frame)
                        elif b_id == 1: 
                            pbone.location = (x / 1000.0, (y / 1000.0) - 1.15, z / 1000.0)
                            pbone.keyframe_insert(data_path="location", frame=frame)
                        else:
                            rx, ry, rz = apply_tk7_axis_correction(b_id, x, y, z)
                            pbone.rotation_mode = 'XYZ'
                            pbone.rotation_euler = (rx, ry, rz)
                            pbone.keyframe_insert(data_path="rotation_euler", frame=frame)
                            
                print("[+] TK7 FBF Import Complete!")
                return missing_tk7_bones
            elif sig in (0x0064, 0x6400):
                print("[!] TK7 KEF Format Detected. (Decoder logic will be injected here next!)")
                return []

    # =======================================================
    # 🌟 철권 8 (Polaris) 기존 로직 유지
    # =======================================================
    if not obj.animation_data:
        obj.animation_data_create()
    if not obj.animation_data.action:
        obj.animation_data.action = bpy.data.actions.new(name="Polaris_Action")
    action = obj.animation_data.action
    target_mask = CATEGORY_MASKS.get(anim_type)

    if anim_type == 'FACIAL':
        from .profiles import MASK_FACIAL_EXCLUSIVE, MASK_FACIAL_DUMMY
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
        
        from .profiles import MASK_HAND_L, MASK_HAND_R
        if has_l_hand and not has_r_hand:
            target_mask = MASK_HAND_L
        elif has_r_hand and not has_l_hand:
            target_mask = MASK_HAND_R
        else:
            target_mask = MASK_HAND_L.union(MASK_HAND_R)

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
            
            if bone_name not in obj.pose.bones:
                missing_bones.append(bone_name)
                continue
            if target_mask is not None and bone_name not in target_mask:
                continue

            pbone = obj.pose.bones[bone_name]
            pbone.rotation_mode = 'QUATERNION'
            f.seek(block_b_offset + 0xC)
            indicator = read_uint32(f)
            f.seek(block_b_offset + 0x14)
            anim_flag = read_uint32(f)
            is_keyframed = (anim_flag == 3)
            f.seek(block_b_offset + 0x18)
            bone_frames = read_uint32(f)
            if bone_frames == 0: bone_frames = 1
            
            if indicator == 0x20:
                final_c_start = first_c_ptr
            elif indicator == 0x24:
                f.seek(block_b_offset + 0x20)
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
            do_flip = selected_group["flip"]
            ox, oy, oz = selected_group["offset"]
            mx, my, mz = selected_group["loc_map"]
            scale_div = selected_group["scale_div"]

            C_mat = mathutils.Euler((math.radians(rx), math.radians(ry), math.radians(rz)), 'XYZ').to_matrix().to_4x4()
            C_inv = C_mat.inverted()

            if is_keyframed:
                f.seek(final_c_start)
                header_chunk = f.read(16)
                base_frame_offset = struct.unpack('<H', header_chunk[4:6])[0]
                bitstream_offset = struct.unpack('<I', header_chunk[8:12])[0]
                num_tracks = (base_frame_offset - 0x10) // 16
                channels_info = []
                f.seek(final_c_start + 0x10)
                for _ in range(num_tracks):
                    c_min, c_max, c_bits, c_idx = struct.unpack('<ffII', f.read(16))
                    if abs(c_max - c_min) < 0.000001: c_bits = 0
                    elif c_bits > 32: c_bits = 0
                    channels_info.append({"min": c_min, "max": c_max, "bits": c_bits, "idx": c_idx})
                
                f.seek(final_c_start + base_frame_offset)
                base_frame = list(struct.unpack('<11f', f.read(44)))
                f.seek(final_c_start + bitstream_offset)
                bitstream_data = f.read(bone_frames * num_tracks * 4) 
                reader = BitReader(bitstream_data)
                has_qw = any(ch["idx"] == 6 for ch in channels_info)
                
                decoded_tracks = {}
                for idx, ch in enumerate(channels_info):
                    decoded_tracks[idx] = []
                    if ch["bits"] > 0:
                        for _ in range(bone_frames):
                            raw = reader.read_bits(ch["bits"])
                            max_val = (1 << ch["bits"]) - 1
                            ratio = raw / float(max_val) if max_val > 0 else 0.0
                            decoded_tracks[idx].append(ch["min"] + (ch["max"] - ch["min"]) * ratio)
                    else:
                        for _ in range(bone_frames):
                            decoded_tracks[idx].append(ch["min"])
                
                for frame in range(bone_frames):
                    comp = base_frame[:]
                    for idx, ch in enumerate(channels_info):
                        comp[ch["idx"]] = decoded_tracks[idx][frame]
                            
                    sx, sy, sz = comp[0], comp[1], comp[2]
                    qx, qy, qz = comp[3], comp[4], comp[5]
                    px, py, pz = comp[7], comp[8], comp[9]
                    
                    if not has_qw:
                        dot_product = qx**2 + qy**2 + qz**2
                        qw = math.sqrt(max(0.0, 1.0 - dot_product))
                    else:
                        qw = comp[6]
                    
                    px, py, pz = px/scale_div, py/scale_div, pz/scale_div
                    if do_flip: py, qy = -py, -qy
                    loc_dict = {'x': px, 'y': py, 'z': pz, '-x': -px, '-y': -py, '-z': -pz}
                    mapped_px, mapped_py, mapped_pz = loc_dict[mx], loc_dict[my], loc_dict[mz]
                        
                    anim_loc = mathutils.Vector((mapped_px, mapped_py, mapped_pz))
                    anim_quat = mathutils.Quaternion((qw, qx, qy, qz))
                    offset_quat = mathutils.Euler((math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ').to_quaternion()
                    anim_quat = anim_quat @ offset_quat
                    anim_scale = mathutils.Vector((sx, sy, sz))
                    
                    M_engine = mathutils.Matrix.LocRotScale(anim_loc, anim_quat, anim_scale)
                    M_blender = C_mat @ M_engine @ C_inv
                    b_loc, b_rot, b_sca = M_blender.decompose()
                    
                    if do_apose_correction and bone_name in APOSE_OFFSETS:
                        ax, ay, az = APOSE_OFFSETS[bone_name]
                        apose_quat = mathutils.Euler((math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ').to_quaternion()
                        b_rot = apose_quat @ b_rot
                    
                    if bone_name in root_bones:
                        pbone.location = b_loc
                        pbone.keyframe_insert(data_path="location", frame=frame)
                    
                    pbone.rotation_quaternion = b_rot
                    pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    
            else:
                f.seek(final_c_start)
                for frame in range(bone_frames):
                    raw_chunk = f.read(44)
                    if len(raw_chunk) < 44: break
                    vals = struct.unpack('<11f', raw_chunk)
                    sx, sy, sz = vals[0:3]
                    qx, qy, qz, qw = vals[3:7]
                    px, py, pz = vals[7]/scale_div, vals[8]/scale_div, vals[9]/scale_div
                    
                    if do_flip: py, qy = -py, -qy
                    loc_dict = {'x': px, 'y': py, 'z': pz, '-x': -px, '-y': -py, '-z': -pz}
                    mapped_px, mapped_py, mapped_pz = loc_dict[mx], loc_dict[my], loc_dict[mz]
                        
                    anim_loc = mathutils.Vector((mapped_px, mapped_py, mapped_pz))
                    anim_quat = mathutils.Quaternion((qw, qx, qy, qz))
                    offset_quat = mathutils.Euler((math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ').to_quaternion()
                    anim_quat = anim_quat @ offset_quat
                    anim_scale = mathutils.Vector((sx, sy, sz))
                    
                    M_engine = mathutils.Matrix.LocRotScale(anim_loc, anim_quat, anim_scale)
                    M_blender = C_mat @ M_engine @ C_inv
                    b_loc, b_rot, b_sca = M_blender.decompose()
                    
                    if do_apose_correction and bone_name in APOSE_OFFSETS:
                        ax, ay, az = APOSE_OFFSETS[bone_name]
                        apose_quat = mathutils.Euler((math.radians(ax), math.radians(ay), math.radians(az)), 'XYZ').to_quaternion()
                        b_rot = apose_quat @ b_rot
                    
                    if bone_name in root_bones:
                        pbone.location = b_loc
                        pbone.keyframe_insert(data_path="location", frame=frame)
                    pbone.rotation_quaternion = b_rot
                    pbone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                
    return missing_bones