import bpy
import struct
import math
import os
import numpy as np
import mathutils
from .profiles_tk7 import TK7_SCALE_DIV, TK7_Y_OFFSET, TK7_GROUPS

# ==============================================================================
# 💡 기존 애드온(TekkenAnimHelper.py) 원본 수학 공식 유지
# ==============================================================================
def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

def getRotationFromMatrix(te, mode=0):
    m11, m12, m13 = te[0][0], te[0][1], te[0][2]
    m21, m22, m23 = te[1][0], te[1][1], te[1][2]
    m31, m32, m33 = te[2][0], te[2][1], te[2][2]

    if mode == 1:
        x = math.asin(-clamp(m23, -1, 1))
        if abs(m23) < 0.9999999:
            y = math.atan2(m13, m33)
            z = math.atan2(m21, m22)
        else:
            y = math.atan2(-m31, m11)
            z = 0
    else:
        y = math.asin(clamp(m13, -1, 1))
        if abs(m13) < 0.9999999:
            x = math.atan2(-m23, m33)
            z = math.atan2(-m12, m11)
        else:
            x = math.atan2(m32, m22)
            z = 0
    return x, y, z

def quaternionToRotationMatrix(Q):
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
    return np.array([[r00, r01, r02], [r10, r11, r12], [r20, r21, r22]])

def get_quaternion_from_euler(roll, pitch, yaw):
    qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
    qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
    qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
    return [qx, qy, qz, qw]

def convertArmToBlenderXYZ(x, y, z):
    halfpi = math.pi / 2
    orig_quat = get_quaternion_from_euler(-halfpi, halfpi, 0)
    orig_mat = np.linalg.inv(quaternionToRotationMatrix(orig_quat))
    
    quat = get_quaternion_from_euler(x, y, z)
    mat = np.matmul(quaternionToRotationMatrix(quat), orig_mat)
    
    ex, ey, ez = getRotationFromMatrix(mat, mode=1)
    return -ez, ey, -ex

def find_bone_name(pose_bones, target_name):
    if target_name in pose_bones: return target_name
    for b in pose_bones:
        if b.name.lower() == target_name.lower(): return b.name
    return target_name

def applyRotationFromAnimdata(armature, animdata, scale_div, y_offset):
    halfpi = math.pi / 2
    
    offset_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'BODY_SCALE__group'))
    base_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'BASE'))
    upper_body_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'Spine1'))
    # spine2_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'Spine2'))
    lower_body_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'Hip'))
    neck_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'Neck'))
    head_bone = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'Head'))

    right_inner_shoulder = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_Shoulder'))
    right_outer_shoulder = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_Arm'))
    right_elbow = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_ForeArm'))
    right_hand = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_Hand'))

    left_inner_shoulder = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_Shoulder'))
    left_outer_shoulder = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_Arm'))
    left_elbow = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_ForeArm'))
    left_hand = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_Hand'))

    right_hip = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_UpLeg'))
    right_knee = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_Leg'))
    right_foot = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'R_Foot'))

    left_hip = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_UpLeg'))
    left_knee = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_Leg'))
    left_foot = armature.pose.bones.get(find_bone_name(armature.pose.bones, 'L_Foot'))

    if offset_bone:
        offset_bone.location.x = animdata[0] / scale_div
        offset_bone.location.y = animdata[1] / scale_div
        offset_bone.location.z = animdata[2] / scale_div

    if base_bone:
        base_bone.location.x = animdata[3] / scale_div
        base_bone.location.y = animdata[4] / scale_div
        base_bone.location.z = animdata[5] / scale_div
        
        base_bone.rotation_euler.x = animdata[11]
        base_bone.rotation_euler.y = animdata[10]
        base_bone.rotation_euler.z = -animdata[9]

    if upper_body_bone:
        upper_body_bone.rotation_euler.x = animdata[14] - halfpi
        upper_body_bone.rotation_euler.y = animdata[13]
        upper_body_bone.rotation_euler.z = animdata[12] * -1

    #if spine2_bone:
    #    spine2_bone.rotation_euler.x = animdata[20] - halfpi
    #    spine2_bone.rotation_euler.y = animdata[19]
    #    spine2_bone.rotation_euler.z = animdata[18] * -1

    if lower_body_bone:
        lower_body_bone.rotation_euler.x = animdata[17] + halfpi
        lower_body_bone.rotation_euler.y = animdata[16]
        lower_body_bone.rotation_euler.z = animdata[15] * -1

    if neck_bone:
        neck_bone.rotation_euler.x = animdata[23]
        neck_bone.rotation_euler.y = animdata[22]
        neck_bone.rotation_euler.z = animdata[21] * -1

    if head_bone:
        head_bone.rotation_euler.x = animdata[25]
        head_bone.rotation_euler.y = animdata[26] - halfpi
        head_bone.rotation_euler.z = animdata[24] - halfpi

    if right_inner_shoulder:
        x, y, z = convertArmToBlenderXYZ(animdata[27], animdata[28], animdata[29])
        right_inner_shoulder.rotation_euler.x = x
        right_inner_shoulder.rotation_euler.y = y
        right_inner_shoulder.rotation_euler.z = z

    if right_outer_shoulder:
        right_outer_shoulder.rotation_euler.x = animdata[30] * -1 - halfpi
        right_outer_shoulder.rotation_euler.y = animdata[32] * -1
        right_outer_shoulder.rotation_euler.z = animdata[31] * -1

    if right_elbow:
        right_elbow.rotation_euler.x = animdata[33] * -1
        right_elbow.rotation_euler.y = animdata[34]
        right_elbow.rotation_euler.z = animdata[35] * -1

    if right_hand:
        right_hand.rotation_euler.x = animdata[36] - halfpi
        right_hand.rotation_euler.y = animdata[38]
        right_hand.rotation_euler.z = animdata[37] * -1

    if left_inner_shoulder:
        x, y, z = convertArmToBlenderXYZ(animdata[39], animdata[40], animdata[41])
        left_inner_shoulder.rotation_euler.x = 0 - x
        left_inner_shoulder.rotation_euler.y = y
        left_inner_shoulder.rotation_euler.z = z + math.pi

    if left_outer_shoulder:
        left_outer_shoulder.rotation_euler.x = animdata[42] + halfpi
        left_outer_shoulder.rotation_euler.y = animdata[44] * -1
        left_outer_shoulder.rotation_euler.z = animdata[43]

    if left_elbow:
        left_elbow.rotation_euler.x = animdata[45]
        left_elbow.rotation_euler.y = animdata[46]
        left_elbow.rotation_euler.z = animdata[47]

    if left_hand:
        left_hand.rotation_euler.x = animdata[48] * -1 + halfpi
        left_hand.rotation_euler.y = animdata[50] * -1
        left_hand.rotation_euler.z = animdata[49] * -1

    if right_hip:
        right_hip.rotation_euler.x = animdata[53]
        right_hip.rotation_euler.y = animdata[52]
        right_hip.rotation_euler.z = animdata[51] * -1

    if right_knee:
        right_knee.rotation_euler.x = animdata[56]
        right_knee.rotation_euler.y = animdata[55]
        right_knee.rotation_euler.z = animdata[54] * -1

    if right_foot:
        right_foot.rotation_euler.x = animdata[59]
        right_foot.rotation_euler.y = animdata[58]
        right_foot.rotation_euler.z = animdata[57] * -1

    if left_hip:
        left_hip.rotation_euler.x = animdata[62]
        left_hip.rotation_euler.y = animdata[61]
        left_hip.rotation_euler.z = animdata[60] * -1

    if left_knee:
        left_knee.rotation_euler.x = animdata[65]
        left_knee.rotation_euler.y = animdata[64]
        left_knee.rotation_euler.z = animdata[63] * -1

    if left_foot:
        left_foot.rotation_euler.x = animdata[68]
        left_foot.rotation_euler.y = animdata[67]
        left_foot.rotation_euler.z = animdata[66] * -1

    return {
        "offset": offset_bone,
        "base_loc": base_bone,
        "rotations": [
            base_bone, upper_body_bone, lower_body_bone, neck_bone, head_bone,
            right_inner_shoulder, right_outer_shoulder, right_elbow, right_hand,
            left_inner_shoulder, left_outer_shoulder, left_elbow, left_hand,
            right_hip, right_knee, right_foot, left_hip, left_knee, left_foot #spine2_bone,
        ]
    }

def import_tk7_anim(filepath, obj, anim_type, do_apose):
    print(f"[*] TK7 Ultimate ZYX Engine Import Started: {filepath}")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    magic = data[0:2]
    endian = '>' if magic in (b'\x00\xC8', b'\x00\x64') else '<'
    sig = struct.unpack(endian + 'H', data[0:2])[0]
    boneCount = struct.unpack(endian + 'H', data[2:4])[0]
    animLength = struct.unpack(endian + 'I', data[4:8])[0]
    if animLength <= 0: animLength = 1 
    
    frame_data = [[0.0] * (boneCount * 3) for _ in range(animLength)]
    
    if sig == 0x00C8: 
        offset = 0x64
        for frame in range(animLength):
            chunk_size = boneCount * 12
            if offset + chunk_size > len(data): break
            frame_floats = struct.unpack(f"{endian}{boneCount*3}f", data[offset:offset+chunk_size])
            frame_data[frame] = list(frame_floats)
            offset += chunk_size

    if not obj.animation_data: obj.animation_data_create()
    action_name = os.path.basename(filepath) + "_Action"
    if obj.animation_data.action and obj.animation_data.action.name == action_name:
        bpy.data.actions.remove(obj.animation_data.action)
    obj.animation_data.action = bpy.data.actions.new(name=action_name)
    
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = animLength - 1

    try:
        for frame in range(animLength):
            animdata = list(frame_data[frame])

            # 1. 원본 애드온 주입
            active_dict = applyRotationFromAnimdata(obj, animdata, TK7_SCALE_DIV, TK7_Y_OFFSET)

            # 2. 위치(Location) 보정 (회전과 완벽히 격리)
            for loc_key in ["offset", "base_loc"]:
                l_bone = active_dict.get(loc_key)
                if not l_bone: continue
                
                group = next((g for g in TK7_GROUPS.values() if l_bone.name in g.get("bones", set())), None)
                if group:
                    orig_x = l_bone.location.x
                    orig_y = l_bone.location.y
                    orig_z = l_bone.location.z
                    
                    loc_map = group.get("loc_map", ('x', 'y', 'z'))
                    loc_dict = {
                        'x': orig_x, '-x': -orig_x,
                        'y': orig_y, '-y': -orig_y,
                        'z': orig_z, '-z': -orig_z,
                        '0': 0.0
                    }
                    
                    l_bone.location.x = loc_dict.get(loc_map[0], orig_x)
                    l_bone.location.y = loc_dict.get(loc_map[1], orig_y)
                    l_bone.location.z = loc_dict.get(loc_map[2], orig_z)

            # 3. 회전(Rotation) 보정
            for r_bone in active_dict.get("rotations", []):
                if not r_bone: continue
                
                # 안전한 XYZ 연산을 위해 뼈대 초기화
                r_bone.rotation_mode = 'XYZ'
                
                group = next((g for g in TK7_GROUPS.values() if r_bone.name in g.get("bones", set())), None)
                if group:
                    engine_euler = r_bone.rotation_euler.copy()
                    
                    post_map = group.get("post_map", ('x', 'y', 'z'))
                    val_dict = {
                        'x': engine_euler.x, '-x': -engine_euler.x,
                        'y': engine_euler.y, '-y': -engine_euler.y,
                        'z': engine_euler.z, '-z': -engine_euler.z,
                        '0': 0.0
                    }
                    
                    fx = val_dict.get(post_map[0], engine_euler.x)
                    fy = val_dict.get(post_map[1], engine_euler.y)
                    fz = val_dict.get(post_map[2], engine_euler.z)
                    
                    # 💡 [핵심 픽스] 사다미츠 문서 규칙: 철권 엔진의 오일러 회전 순서는 ZYX다!
                    # 여기서 'ZYX'를 지정함으로써 앞뒤로 미친듯이 튀는 짐벌락 현상이 완벽하게 펴집니다.
                    M_engine = mathutils.Euler((fx, fy, fz), 'ZYX').to_matrix().to_4x4()
                    
                    # 4. 아머추어 동기화 (Basis)
                    bx, by, bz = group.get("basis", (0, 0, 0))
                    if bx != 0 or by != 0 or bz != 0:
                        C_mat = mathutils.Euler((math.radians(bx), math.radians(by), math.radians(bz)), 'XYZ').to_matrix().to_4x4()
                        C_inv = C_mat.inverted()
                        M_blender = C_mat @ M_engine @ C_inv
                    else:
                        M_blender = M_engine
                        
                    # 5. 최종 각도 보정 (post_offset) - 로컬 매트릭스를 직접 회전시킴
                    ox, oy, oz = group.get("post_offset", (0, 0, 0))
                    if ox != 0 or oy != 0 or oz != 0:
                        offset_mat = mathutils.Euler((math.radians(ox), math.radians(oy), math.radians(oz)), 'XYZ').to_matrix().to_4x4()
                        M_blender = M_blender @ offset_mat
                    
                    # 최종 결과물은 가장 안정적인 'XYZ' 모드로 출력
                    r_bone.rotation_euler = M_blender.to_euler('XYZ')

            if active_dict.get("offset"):
                active_dict["offset"].keyframe_insert(data_path='location', frame=frame)
            if active_dict.get("base_loc"):
                active_dict["base_loc"].keyframe_insert(data_path='location', frame=frame)
                
            for r_bone in active_dict.get("rotations", []):
                if r_bone:
                    r_bone.keyframe_insert(data_path='rotation_euler', frame=frame)

    except Exception as e:
        print(f"[!] 애니메이션 주입 중 오류 발생 (프레임 {frame}): {e}")
        
    print("[+] TK7 Ultimate ZYX Engine Import Complete!")