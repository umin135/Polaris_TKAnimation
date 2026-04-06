# ==============================================================================
# 1. 씬 스케일 조절 (Unit Scale 보정)
# ==============================================================================
TK7_SCALE_DIV = 10.0
TK7_Y_OFFSET = 0.0115

# ==============================================================================
# 2. 마스터 프로필 (동기화 Basis + 궁극의 Post-Process)
# ==============================================================================
# ⚠️ basis: 스켈레톤 간의 오차를 맞추는 절대값 (수정 금지)
# 🎯 post_map: 애니메이션 축 교환 및 반전 ('x', '-y', 'z', '0' 등 입력 가능)
# 🎯 post_offset: 최종 결과물에 고정 각도(도 단위) 추가

TK7_GROUPS = {
    # --- 루트 및 위치 보정 ---
    'BODY_SCALE__group': {
        "bones": {'BODY_SCALE__group'}, "basis": (0.0, 0.0, 90.0), 
        "loc_map": ('y', '-x', 'z')
    },
    'BASE': {
        "bones": {'BASE'}, 
        "basis": (0.0, 0.0, 90.0), 
        "loc_map": ('-y', 'x', '-z'),
        "post_map": ('0', '0', '-z'),
        "post_offset": (0, 0, 0)
    },
    
    
    
    # --- 척추 및 머리 ---
    # 💡 Spine1이 반대로 숙여진다면? -> post_map을 ('-x', 'y', 'z') 로 변경해보세요!
    'Spine1': {
        "bones": {'Spine1'}, 
        "basis": (90.0, -90.0, 0.0), 
        "post_map": ('-y', 'x', 'z'), 
        "post_offset": (0, -90, 0)
        },
    # 'Spine2': {"bones": {'Spine2'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'Neck': {"bones": {'Neck'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'Head': {"bones": {'Head'}, "basis": (-87.1, 90.0, -0.1), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    
    # --- 왼쪽 팔 ---
    'L_Shoulder': {
        "bones": {'L_Shoulder'}, 
        "basis": (0.0, 0.0, 90.0), 
        "post_map": ('x', 'y', '-z'), 
        "post_offset": (0, 0, 0)
    },
    'L_Arm': {
        "bones": {'L_Arm'}, 
        "basis": (0.0, 0.0, 90.0), 
        "post_map": ('x', 'y', 'z'), 
        "post_offset": (0, 0, 0)
    },
    'L_ForeArm': {"bones": {'L_ForeArm'}, "basis": (0.0, 0.0, 90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'L_Hand': {"bones": {'L_Hand'}, "basis": (0.0, 0.0, -90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    
    # --- 오른쪽 팔 ---
    'R_Shoulder': {"bones": {'R_Shoulder'}, "basis": (0.0, 0.0, 90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'R_Arm': {"bones": {'R_Arm'}, "basis": (0.0, -180.0, 90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'R_ForeArm': {"bones": {'R_ForeArm'}, "basis": (0.0, 180.0, 90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'R_Hand': {"bones": {'R_Hand'}, "basis": (0.0, 0.0, 90.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    
    # --- 하반신 및 다리 ---
    'Hip': {
        "bones": {'Hip'}, 
        "basis": (90.0, -90.0, 0.0), 
        "post_map": ('x', 'y', 'z'), 
        "post_offset": (0, 0, 0)},

    'L_UpLeg': {"bones": {'L_UpLeg'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'L_Leg': {"bones": {'L_Leg'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'L_Foot': {"bones": {'L_Foot'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    
    'R_UpLeg': {"bones": {'R_UpLeg'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'R_Leg': {"bones": {'R_Leg'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
    'R_Foot': {"bones": {'R_Foot'}, "basis": (90.0, -90.0, 0.0), "post_map": ('x', 'y', 'z'), "post_offset": (0, 0, 0)},
}