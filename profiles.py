DEFAULT_FALLBACK = {
    "basis": (0, 0, 90),
    "flip": False,
    "offset": (0, 0, 0), 
    "loc_map": ("x", "y", "z"),
    "scale_div": 100.0
}

# =======================================================
# 1. FULLBODY (전신) 프로필
# =======================================================
FULLBODY_ROOTS = {"Top", "Trans"}

FULLBODY_GROUPS = {
    "ROOT_MOTION": {
        "bones": {"Top", "Trans", "Rot"}, 
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, 0, 0),
        "loc_map": ("-x", "y", "z"), 
        "scale_div": 1.0 
    },
    "GROUP_A": { 
        "bones": {"Spine1", "Spine2", "Neck", "Head", "R_UpperArm", "PMP_R_UpperArm", "R_LowerArm", "PMP_R_LowerArm", "R_LowerLeg", "L_UpperArm", "PMP_L_UpperArm", "L_LowerArm", "PMP_L_LowerArm", "L_LowerLeg", "L_Foot", "R_Foot"},
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, 0, 0), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_B": { 
        "bones": {"R_Shoulder"},
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, -90, 0),
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_C": { 
        "bones": {"L_Shoulder"},
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, 90, 0),
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_D": { 
        "bones": {"R_UpperLeg", "L_UpperLeg"}, 
        "basis": (0, 0, -90), 
        "flip": False, 
        "offset": (0, 0, 180), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_E": { 
        "bones": {"L_Hand"}, 
        "basis": (0, 0, -90), 
        "flip": False, 
        "offset": (-90, 0, 0), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_F": { 
        "bones": {"R_Hand"}, 
        "basis": (0, 0, 0), 
        "flip": False, 
        "offset": (90, 0, 0), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_G": { 
        "bones": {"L_Toe", "R_Toe"}, 
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, 0, 90), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_H": { 
        "bones": {"Hip"}, 
        "basis": (0, 0, 90), 
        "flip": False, 
        "offset": (0, -90, -90), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_I_global": { 
        "bones": {"DUMMY"}, 
        "basis": (0, 0, 90),
        "flip": False,
        "offset": (0, 0, 0), 
        "loc_map": ("x", "y", "z"),
        "scale_div": 100.0
    },
}

# =======================================================
# 2. 다른 카테고리 프로필 준비 (추후 디버깅하며 채워넣기)
# =======================================================
HAND_ROOTS = set()
HAND_GROUPS = {}

FACIAL_ROOTS = set()
FACIAL_GROUPS = {}

WING_ROOTS = set()
WING_GROUPS = {}

CAMERA_ROOTS = set()
CAMERA_GROUPS = {}

EXTRA_ROOTS = set()
EXTRA_GROUPS = {}

# =======================================================
# 엔진에서 호출할 프로필 레지스트리 (UI의 키값과 1:1 매칭)
# =======================================================
PROFILE_REGISTRY = {
    'FULLBODY': (FULLBODY_ROOTS, FULLBODY_GROUPS),
    'HAND':     (HAND_ROOTS, HAND_GROUPS),
    'FACIAL':   (FACIAL_ROOTS, FACIAL_GROUPS),
    'WING':     (WING_ROOTS, WING_GROUPS),
    'CAMERA':   (CAMERA_ROOTS, CAMERA_GROUPS),
    'EXTRA':    (EXTRA_ROOTS, EXTRA_GROUPS)
}

# =======================================================
# 3. A-Pose 보정 오프셋 (사용자 맞춤형 황금 수치)
# =======================================================
APOSE_OFFSETS = {
    "L_Shoulder": (-10, 0, 0),
    "R_Shoulder": (10, 0, 0),
    "L_UpperArm": (-35, 0, 0), 
    "R_UpperArm": (35, 0, 0),
    "L_LowerArm": (0, 0, -15),
    "R_LowerArm": (0, 0, -15),
    "L_UpperLeg": (-5.99981, 0, 0),
    "R_UpperLeg": (5.99981, 0, 0),
    "L_Foot":     (5.99909, 0, 0),
    "R_Foot":     (-5.99909, 0, 0)
}