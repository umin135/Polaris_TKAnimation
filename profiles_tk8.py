# =======================================================
# 완전히 무시할 본 목록
# - Import: 키프레임 삽입 안 함
# - Export: C-블록에 쓰지 않음 (템플릿 원본값 유지)
# 절차적으로 엔진이 구동하거나 미사용으로 확인된 본을 여기에 추가
# =======================================================
IGNORE_BONES = {
}

DEFAULT_FALLBACK = {
    "basis": (0, 0, 90),
    "flip": False,
    "offset": (0, 0, 0),
    "loc_map": ("x", "y", "z"),
    "scale_div": 100.0,
    # post_rot: import 후 b_rot에 우측 곱셈으로 추가 보정 (도 단위 XYZ 오일러)
    # 좌표계가 아닌 로컬 보정이 필요할 때 사용. 기본값 (0,0,0) = 영향 없음
    "post_rot": (0, 0, 0),
}

# =======================================================
# ROOT MOTION 튜닝 파라미터
# -------------------------------------------------------
# 루트본(Trans, Top, Rot) 위치가 잘못됐을 때 여기만 수정.
#
# [loc_map] 엔진 축 3개 → Blender 축 매핑 (순서: X, Y, Z)
#   선택지: "x" "-x" "y" "-y" "z" "-z"
#   예) 앞뒤가 반대면 → "-y" 를 "y" 로 바꿔보세요
#   예) 좌우가 반대면 → "-x" 를 "x" 로 바꿔보세요
#   예) 좌우/앞뒤 축이 뒤바뀌면 → ("y", "x", "z") 식으로 순서를 교체
#
# [scale_div] 단위 보정
#   100.0 → cm → m 변환 (일반 뼈 기본값)
#   1.0   → 변환 없음 (루트본이 이미 다른 스케일인 경우)
#
# [basis] 좌표계 기저 회전 (도 단위, XYZ 오일러)
#   (0,0,90) → Z축 90도 회전 (대부분의 뼈 기본값)
#   회전 방향이 통째로 틀릴 때 수정
#
# [rot_offset] 루트본 회전에만 추가할 고정 오프셋 (도 단위)
# =======================================================
ROOT_MOTION_LOC_MAP   = ("x", "y", "z")   # ← 축 방향 문제시 수정
ROOT_MOTION_SCALE     = 1.0                 # ← 스케일 문제시 수정
ROOT_MOTION_BASIS     = (0, 0, 90)          # ← 회전 기저 문제시 수정
ROOT_MOTION_FLIP      = False
ROOT_MOTION_ROT_OFFSET = (0, 0, 0)

# =======================================================
# 1. FULLBODY (전신) 프로필
# =======================================================
FULLBODY_ROOTS = {"Top", "Trans"}
FULLBODY_GROUPS = {
    "ROOT_MOTION": {
        "bones": {"Top", "Trans", "Rot"},
        "basis":     ROOT_MOTION_BASIS,
        "flip":      ROOT_MOTION_FLIP,
        "offset":    ROOT_MOTION_ROT_OFFSET,
        "loc_map":   ROOT_MOTION_LOC_MAP,
        "scale_div": ROOT_MOTION_SCALE,
    },
    "Root2": {
        "bones": {"HARA_ROT1"},
        "basis": (0, 0, 90),
        "flip": False,
        "offset": (0, 0, 0),
        "post_rot": (0, 0, 180),
        "loc_map": ("x", "y", "z"),
        "scale_div": 100.0
    },


    "GROUP_A": { 
        "bones": {
            "Spine1", "Spine2", "Neck", "Head", "R_UpperArm", "PMP_R_UpperArm", "R_LowerArm", "PMP_R_LowerArm", "R_LowerLeg", 
            "L_UpperArm", "PMP_L_UpperArm", "L_LowerArm", "PMP_L_LowerArm", "L_LowerLeg", "L_Foot", "R_Foot",
            "PMP_L_Chest", "PMP_R_Chest", "PMP_L_LowerArm_fore", "PMP_R_LowerArm_fore", "PMP_L_Shoulder", "PMP_R_Shoulder",
            "PMP_L_UpperLeg", "PMP_R_UpperLeg"
        },
        "basis": (0, 0, 90), "flip": False, "offset": (0, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_B": { 
        "bones": {"R_Shoulder"}, 
        "basis": (0, -90, 90), 
        "flip": False, 
        "offset": (0, -90, 0), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_C": { 
        "bones": {"L_Shoulder"}, 
        "basis": (0, 90, 90), 
        "flip": False, 
        "offset": (0, 90, 0), 
        "loc_map": ("x", "y", "z"), 
        "scale_div": 100.0
    },
    "GROUP_D": { 
        "bones": {"R_UpperLeg", "L_UpperLeg"}, "basis": (0, 0, -90), "flip": False, "offset": (0, 0, 180), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_E": { 
        "bones": {"L_Hand"}, "basis": (-90, 0, 90), "flip": False, "offset": (-90, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_F": { 
        "bones": {"R_Hand"}, "basis": (90, 0, 90), "flip": False, "offset": (90, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_G": { 
        "bones": {"L_Toe", "R_Toe"}, "basis": (90, 0, 0), "flip": False, "offset": (0, 0, 90), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_H": { 
        "bones": {"Hip"}, "basis": (0, 0, 90), "flip": False, "offset": (0, -90, -90), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_BODY_AUX": { 
        "bones": {"MUKI", "MUNE_jnt", "KOSI_NULL2", "Neck2", "BASE", "C_Leg"}, "basis": (0, 0, 90), "flip": False, "offset": (0, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_PROPS_PHYSICS": {
        "bones": {
            "ATH_Hip_Body", "ATH_Hip_Root", "ATH_Hip_bottom", "ATH_Hip_box_cover", "ATH_Hip_box_studs", "ATH_Hip_front_grip", "ATH_Hip_grip_base", "ATH_Hip_grip_rot", "ATH_Hip_saya01", "ATH_Hip_saya02", "ATH_Hip_saya03", "ATH_Hip_saya04", "ATH_Hip_scope_base_rot", "ATH_Hip_scope_extend", "ATH_Hip_scope_rot_a", "ATH_Hip_scope_rot_b", "ATH_Hip_scope_rot_c", "ATH_Hip_scope_rot_d", "ATH_Hip_stretch", "ATH_Hip_top", "ATH_Hip_trigger", "ATH_Hip_tsuka", "ATH_L_Arm_separator", "ATH_L_Hand_separator", "ATH_L_LowerArm", "ATH_L_burnier", "ATH_L_burnier_separator", "ATH_L_got_00", "ATH_L_got_01", "ATH_L_got_Index1", "ATH_L_got_Index2", "ATH_L_got_Index3", "ATH_L_got_Middle1", "ATH_L_got_Middle2", "ATH_L_got_Middle3", "ATH_L_got_Pinky1", "ATH_L_got_Pinky2", "ATH_L_got_Pinky3", "ATH_L_got_Ring1", "ATH_L_got_Ring2", "ATH_L_got_Ring3", "ATH_L_got_Thumb0", "ATH_L_got_Thumb1", "ATH_L_got_Thumb2", "ATH_L_knife", "ATH_L_saya01", "ATH_L_saya02", "ATH_L_saya03", "ATH_L_saya04", "ATH_L_spear", "ATH_L_spear_2nd", "ATH_L_tsuka", "ATH_L_weapon001", "ATH_Neck_separator", "ATH_R_Arm_separator", "ATH_R_Hand_separator", "ATH_R_LowerArm", "ATH_R_Thigh_karambit", "ATH_R_burnier", "ATH_R_burnier_separator", "ATH_R_flashlight", "ATH_R_folding001", "ATH_R_folding002", "ATH_R_folding003", "ATH_R_folding004", "ATH_R_folding005", "ATH_R_folding006", "ATH_R_grenade", "ATH_R_handgun01", "ATH_R_handgun02", "ATH_R_karambit", "ATH_R_katana", "ATH_R_spear", "ATH_R_spear_2nd", "ATH_R_weapon001", "ATH_Spine1_separator", "ATH_cane", "ATH_chest_beam", "ATH_katanaL_1st", "ATH_katanaL_2nd", "ATH_katanaR_1st", "ATH_katanaR_2nd", "ATH_katasaya_1st", "ATH_katasaya_2nd", "ATH_katatuka", "ATH_mnt_C_burnier_back", "ATH_mnt_L_burnier_back", "ATH_mnt_R_burnier_back", "ATH_pikL_1st", "ATH_pyaL_1st", "ATH_pyaL_2nd", "ATH_pyaR_1st", "ATH_pyaR_2nd", "ATH_pyaR_B_1st", "ATH_pyaR_B_2nd", "ATH_saya_1st", "ATH_saya_2nd", "ATH_swordR_1st", "ATH_swordR_2nd", "ATH_sword_back", "ATH_tail_01", "ATH_tail_02", "ATH_tail_03", "ATH_tail_04", "ATH_tail_05", "ATH_tail_06", "ATH_tail_07", "ATH_tail_08", "ATH_tail_09", "ATH_tail_10", "ATH_tail_11", "ATH_tail_12", "ATH_tail_13", "ATH_tail_14", "ATH_tail_15", "ATH_tail_16", "ATH_thirdeye_beam", "ATH_tuka_top", "ATH_visor001", "ATH_visor002", "ATH_visor003", "ATH_visor004", "BUKI_1_jnt", "BUKI_2_jnt", "L_Have", "L_Have2", "R_Have", "R_Have2", "mushi_R_1", "mushi_R_2", "mushi_R_3", "mushi_R_4", "mushi_R_5", "mushi_R_6", "mushi_R_7", "mushi_R_8"
        },
        "basis": (0, 0, 90), "flip": False, "offset": (0, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "GROUP_I_global": { 
        "bones": {"DUMMY"}, "basis": (0, 0, 90), "flip": False, "offset": (0, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
}

# =======================================================
# 카테고리 준비
# =======================================================
HAND_ROOTS = set()
HAND_GROUPS = {}

# =======================================================
# 3. Facial 프로필
# =======================================================
FACIAL_ROOTS = set()
FACIAL_GROUPS = {
    "FACIAL_ALL_TEMP": {
        "bones": {
            "ASHI_L_jnt", "ASHI_R_jnt", "ATAMA_jnt", "ATH_katanaL_1st", "ATH_katanaL_2nd", "ATH_katanaR_1st", "ATH_katanaR_2nd", "ATH_katasaya_1st", "ATH_katasaya_2nd", "ATH_katatuka", "ATH_tuka_top", "BASE", "Bero1_Joint", "Bero1_Joint_pos", "Bero2_Joint", "Bero3_Joint", "C_Forehead", "C_Jaw_Root", "C_Leg", "C_LipChin", "C_LowChin", "C_LowJaw", "C_LowLip", "C_LowLipZipper", "C_LowMidLip", "C_LowTeeth", "C_Nose1", "C_Nose2", "C_Nose3", "C_Nose4", "C_Tongue1", "C_Tongue2", "C_Tongue3", "C_UpChin", "C_UpJaw", "C_UpLip", "C_UpLipZipper", "C_UpMidLip", "C_UpTeeth", "C_UpThroat", "HARA_ROT1", "HIZA_L_jnt", "HIZA_R_jnt", "Head", "Head_scale_null", "Hip", "Jaw_Joint", "KATA_L_jnt", "KATA_R_jnt", "KOSHI_jnt", "KOSI_NULL2", "KUBI_jnt", "L_Brow1", "L_Brow2", "L_Brow3", "L_Brow4", "L_Cheek1", "L_Cheek2", "L_Cheek3", "L_Cheek4", "L_Cheek5", "L_Cheek6", "L_Cheek7", "L_Cheek8", "L_CheekLine1", "L_CheekLine2", "L_Chobo_Joint", "L_DoubleEyelid1", "L_DoubleEyelid2", "L_DoubleEyelid3", "L_DoubleEyelid4", "L_Eye", "L_EyePupil", "L_Eye_Joint", "L_Eyecorner", "L_Eyelid1", "L_Eyelid2", "L_Foot", "L_Forehead1", "L_Forehead2", "L_Hana_Joint", "L_Hana_transY", "L_Hand", "L_Have", "L_Hoho1_Joint", "L_Hoho2_Joint", "L_Hoho3_Joint", "L_Hoho4_Joint", "L_Hoho5_Joint", "L_HohoShiwa_Joint", "L_Hoho_Joint", "L_Hoho_transY", "L_Index0", "L_Index1", "L_Index2", "L_Index3", "L_Kobana_Joint", "L_LipCorner", "L_LipD_Joint", "L_LipE_Joint", "L_LipU_Joint", "L_LowChin1", "L_LowChin2", "L_LowEar", "L_LowEyelid", "L_LowEyelid1", "L_LowEyelid2", "L_LowEyelid3", "L_LowEyelid4", "L_LowEyelid5", "L_LowLip01Zipper", "L_LowLip1", "L_LowLip11Zipper", "L_LowLip12Zipper", "L_LowLip2", "L_LowLip21Zipper", "L_LowLip22Zipper", "L_LowLip23Zipper", "L_LowLip3", "L_LowLip31Zipper", "R_LowLip32Zipper", "R_LowLip4", "R_LowMidLip1", "R_LowMidLip2", "R_LowMidLip3", "R_LowTeeth", "R_LowerArm", "R_LowerLeg", "R_Mayu1_Joint", "R_Mayu1_transY", "R_Mayu2_Joint", "R_Mayu3_Joint", "R_Middle0", "R_Middle1", "R_Middle2", "R_Middle3", "R_Nose1", "R_Nose2", "R_Pinky0", "R_Pinky1", "R_Pinky2", "R_Pinky3", "R_Ring0", "R_Ring1", "R_Ring2", "R_Ring3", "R_Shoulder", "R_SitaMabuta_Joint", "R_SubBrow1", "R_SubBrow2", "R_SubBrow3", "R_SubBrow4", "R_SubLowEyelid2", "R_SubLowEyelid3", "R_SubLowEyelid4", "R_Temple", "R_ThirdEyelid", "R_Thumb0", "R_Thumb1", "R_Thumb2", "R_Toe", "R_UpChin1", "R_UpEar", "R_UpEyelid", "R_UpEyelid1", "R_UpEyelid2", "R_UpEyelid3", "R_UpEyelid4", "R_UpEyelid5", "R_UpLip01Zipper", "R_UpLip1", "R_UpLip11Zipper", "R_UpLip12Zipper", "R_UpLip2", "R_UpLip21Zipper", "R_UpLip22Zipper", "R_UpLip23Zipper", "R_UpLip3", "R_UpLip31Zipper", "R_UpLip32Zipper", "R_UpMidLip1", "R_UpMidLip2", "R_UpMidLip3", "R_UpTeeth", "R_UpperArm", "R_UpperLeg", "R_UwaMabuta_Joint", "R_throat", "Root", "Rot", "SAKOTSU_L_jnt", "SAKOTSU_R_jnt", "Spine1", "Spine2", "TE_L_jnt", "TE_R_jnt", "Top", "Trans", "UDE_L_jnt", "UDE_R_jnt", "UNKNOWN_0_jnt", "UNKNOWN_10_jnt", "UNKNOWN_11_jnt", "UNKNOWN_12_jnt", "UNKNOWN_13_jnt", "UNKNOWN_14_jnt", "UNKNOWN_15_jnt", "UNKNOWN_16_jnt", "UNKNOWN_17_jnt", "UNKNOWN_18_jnt", "UNKNOWN_19_jnt", "UNKNOWN_1_jnt", "UNKNOWN_20_jnt", "UNKNOWN_21_jnt", "UNKNOWN_22_jnt", "UNKNOWN_23_jnt", "UNKNOWN_24_jnt", "UNKNOWN_25_jnt", "UNKNOWN_26_jnt", "UNKNOWN_27_jnt", "UNKNOWN_28_jnt", "UNKNOWN_29_jnt", "UNKNOWN_2_jnt", "UNKNOWN_30_jnt", "UNKNOWN_31_jnt", "UNKNOWN_32_jnt", "UNKNOWN_33_jnt", "UNKNOWN_34_jnt", "UNKNOWN_35_jnt", "UNKNOWN_36_jnt", "UNKNOWN_37_jnt", "UNKNOWN_38_jnt", "UNKNOWN_39_jnt", "UNKNOWN_3_jnt", "UNKNOWN_40_jnt", "UNKNOWN_41_jnt", "UNKNOWN_42_jnt", "UNKNOWN_43_jnt", "UNKNOWN_44_jnt", "UNKNOWN_45_jnt", "UNKNOWN_46_jnt", "UNKNOWN_47_jnt", "UNKNOWN_48_jnt", "UNKNOWN_49_jnt", "UNKNOWN_4_jnt", "UNKNOWN_50_jnt", "UNKNOWN_51_jnt", "UNKNOWN_52_jnt", "UNKNOWN_53_jnt", "UNKNOWN_54_jnt", "UNKNOWN_5_jnt", "UNKNOWN_6_jnt", "UNKNOWN_7_jnt", "UNKNOWN_8_jnt", "UNKNOWN_9_jnt"
        },
        "basis": (0, 0, 0),    # 💡 기본값 (0,0,90)을 제거하고 순정 상태로 만듭니다.
        "flip": False,
        "offset": (0, 0, 90), 
        "loc_map": ("x", "y", "z"),
        "scale_div": 100.0
    }
}

CAMERA_ROOTS = set()
CAMERA_GROUPS = {}

# =======================================================
# SWING (139개) 프로필
# =======================================================
SWING_ROOTS = set()
SWING_GROUPS = {
    "SWING_LEFT": {
        "bones": {
            "ATH_L_burnier", "ATH_L_burnier_separator", "ATH_L_got_00", "ATH_L_got_01", "ATH_L_got_Index1", "ATH_L_got_Index2", "ATH_L_got_Index3", "ATH_L_got_Middle1", "ATH_L_got_Middle2", "ATH_L_got_Middle3", "ATH_L_got_Pinky1", "ATH_L_got_Pinky2", "ATH_L_got_Pinky3", "ATH_L_got_Ring1", "ATH_L_got_Ring2", "ATH_L_got_Ring3", "ATH_L_got_Thumb0", "ATH_L_got_Thumb1", "ATH_L_got_Thumb2", "ATH_mnt_L_armwing", "ATH_mnt_L_burnier_back", "ATH_mnt_L_chainsaw", "ATH_pse_featherA_01_l", "ATH_pse_featherA_02_l", "ATH_pse_featherA_03_l", "ATH_pse_featherA_04_l", "ATH_pse_featherA_05_l", "ATH_pse_featherB_01_l", "ATH_pse_featherB_02_l", "ATH_pse_featherB_03_l", "ATH_pse_featherB_04_l", "ATH_pse_featherC_01_l", "ATH_pse_featherC_02_l", "ATH_pse_featherC_03_l", "ATH_pse_launchPadA_01_l", "ATH_pse_launchPadA_02_l", "ATH_pse_launchPadA_03_l", "ATH_pse_launchPadA_04_l", "ATH_pse_launchPadB_01_l", "ATH_pse_launchPadB_02_l", "ATH_pse_launchPadB_03_l", "ATH_pse_launchPadRootA_01_l", "ATH_pse_launchPadRootB_01_l", "ATH_pse_wing_01_l", "ATH_pse_wing_02_l", "ATH_wingL_1st", "ATH_wingL_2nd", "ATH_wingL_5th", "ATH_wingL_6th", "ATH_wingL_top", "L_Have", "OPT600_haneLtop", "OPT601_haneL1st", "OPT602_haneL2nd", "OPT606_haneL3rd", "OPT607_haneL4th", "OPT702_wingL_2nd", "OPT703_wingL_3rd", "OPT704_wingL_top", "OPT705_wingL_top", "OPT900_wingL_top", "OPT901_wingL_1st", "OPT902_wingL_2nd", "OPT903_wingL_3rd", "OPT904_wingL_top", "OPT905_wingL_top", "OPT950_wingL_top", "OPT951_wingL_1st", "OPT952_wingL_2nd", "OPT953_wingL_3rd", "OPT954_wingL_top", "OPT955_wingL_top", "SWG_wingL_3rd", "SWG_wingL_4th", "ATH_Head_Leyelid", "ATH_Spine2_Leyelid"
        },
        "basis": (0, 0, 90), "flip": False, "offset": (180, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "SWING_RIGHT": {
        "bones": {
            "ATH_R_burnier", "ATH_R_burnier_separator", "ATH_mnt_R_armwing", "ATH_mnt_R_burnier_back", "ATH_mnt_R_chainsaw", "ATH_pse_featherA_01_r", "ATH_pse_featherA_02_r", "ATH_pse_featherA_03_r", "ATH_pse_featherA_04_r", "ATH_pse_featherA_05_r", "ATH_pse_featherB_01_r", "ATH_pse_featherB_02_r", "ATH_pse_featherB_03_r", "ATH_pse_featherB_04_r", "ATH_pse_featherC_01_r", "ATH_pse_featherC_02_r", "ATH_pse_featherC_03_r", "ATH_pse_launchPadA_01_r", "ATH_pse_launchPadA_02_r", "ATH_pse_launchPadA_03_r", "ATH_pse_launchPadA_04_r", "ATH_pse_launchPadB_01_r", "ATH_pse_launchPadB_02_r", "ATH_pse_launchPadB_03_r", "ATH_pse_launchPadRootA_01_r", "ATH_pse_launchPadRootB_01_r", "ATH_pse_wing_01_r", "ATH_pse_wing_02_r", "ATH_wingR_1st", "ATH_wingR_2nd", "ATH_wingR_5th", "ATH_wingR_6th", "ATH_wingR_top", "OPT603_haneRtop", "OPT604_haneR1st", "OPT605_haneR2nd", "OPT608_haneR3rd", "OPT609_haneR4th", "OPT720_wingR_top", "OPT721_wingR_1st", "OPT722_wingR_2nd", "OPT723_wingR_3rd", "OPT724_wingR_top", "OPT725_wingR_top", "OPT920_wingR_top", "OPT921_wingR_1st", "OPT922_wingR_2nd", "OPT923_wingR_3rd", "OPT924_wingR_top", "OPT925_wingR_top", "OPT970_wingR_top", "OPT971_wingR_1st", "OPT972_wingR_2nd", "OPT973_wingR_3rd", "OPT974_wingR_top", "OPT975_wingR_top", "R_Have", "SWG_wingR_3rd", "SWG_wingR_4th", "ATH_Head_Reyelid", "ATH_Spine2_Reyelid"
        },
        "basis": (0, 0, 90), "flip": False, "offset": (180, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    },
    "SWING_CENTER_ETC": {
        "bones": { "ATH_Head_eye", "ATH_Spine2_eye" },
        "basis": (0, 0, 90), "flip": False, "offset": (0, 0, 0), "loc_map": ("x", "y", "z"), "scale_div": 100.0
    }
}

# =======================================================
# EXTRA (44개) 프로필
# =======================================================
EXTRA_ROOTS = set()
EXTRA_GROUPS = {}

# =======================================================
# 엔진에서 호출할 프로필 레지스트리
# =======================================================
PROFILE_REGISTRY = {
    'FULLBODY': (FULLBODY_ROOTS, FULLBODY_GROUPS),
    'HAND':     (HAND_ROOTS, HAND_GROUPS),
    'FACIAL':   (FACIAL_ROOTS, FACIAL_GROUPS),
    'SWING':    (SWING_ROOTS, SWING_GROUPS),
    'CAMERA':   (CAMERA_ROOTS, CAMERA_GROUPS),
    'EXTRA':    (EXTRA_ROOTS, EXTRA_GROUPS),
}

APOSE_OFFSETS = {
    "L_Shoulder": (-10, 0, 0), "R_Shoulder": (10, 0, 0), "L_UpperArm": (-35, 0, 0), "R_UpperArm": (35, 0, 0),
    "L_LowerArm": (0, 0, -15), "R_LowerArm": (0, 0, -15), "L_UpperLeg": (-5.99981, 0, 0), "R_UpperLeg": (5.99981, 0, 0),
    "L_Foot":     (5.99909, 0, 0), "R_Foot":     (-5.99909, 0, 0)
}

# =======================================================
# 레이어 마스크 셋업 
# =======================================================
MASK_HAND_L = {
    "L_Index0", "L_Index1", "L_Index2", "L_Index3", "L_Middle0", "L_Middle1", "L_Middle2", "L_Middle3",
    "L_Pinky0", "L_Pinky1", "L_Pinky2", "L_Pinky3", "L_Ring0", "L_Ring1", "L_Ring2", "L_Ring3", "L_Thumb0", "L_Thumb1", "L_Thumb2"
}
MASK_HAND_R = {
    "R_Index0", "R_Index1", "R_Index2", "R_Index3", "R_Middle0", "R_Middle1", "R_Middle2", "R_Middle3",
    "R_Pinky0", "R_Pinky1", "R_Pinky2", "R_Pinky3", "R_Ring0", "R_Ring1", "R_Ring2", "R_Ring3", "R_Thumb0", "R_Thumb1", "R_Thumb2"
}

MASK_FULLBODY = {
    "ATH_Hip_Body", "ATH_Hip_Root", "ATH_Hip_bottom", "ATH_Hip_box_cover", "ATH_Hip_box_studs", "ATH_Hip_front_grip", "ATH_Hip_grip_base", "ATH_Hip_grip_rot", "ATH_Hip_saya01", "ATH_Hip_saya02", "ATH_Hip_saya03", "ATH_Hip_saya04", "ATH_Hip_scope_base_rot", "ATH_Hip_scope_extend", "ATH_Hip_scope_rot_a", "ATH_Hip_scope_rot_b", "ATH_Hip_scope_rot_c", "ATH_Hip_scope_rot_d", "ATH_Hip_stretch", "ATH_Hip_top", "ATH_Hip_trigger", "ATH_Hip_tsuka", "ATH_L_Arm_separator", "ATH_L_Hand_separator", "ATH_L_LowerArm", "ATH_L_burnier", "ATH_L_burnier_separator", "ATH_L_got_00", "ATH_L_got_01", "ATH_L_got_Index1", "ATH_L_got_Index2", "ATH_L_got_Index3", "ATH_L_got_Middle1", "ATH_L_got_Middle2", "ATH_L_got_Middle3", "ATH_L_got_Pinky1", "ATH_L_got_Pinky2", "ATH_L_got_Pinky3", "ATH_L_got_Ring1", "ATH_L_got_Ring2", "ATH_L_got_Ring3", "ATH_L_got_Thumb0", "ATH_L_got_Thumb1", "ATH_L_got_Thumb2", "ATH_L_knife", "ATH_L_saya01", "ATH_L_saya02", "ATH_L_saya03", "ATH_L_saya04", "ATH_L_spear", "ATH_L_spear_2nd", "ATH_L_tsuka", "ATH_L_weapon001", "ATH_Neck_separator", "ATH_R_Arm_separator", "ATH_R_Hand_separator", "ATH_R_LowerArm", "ATH_R_Thigh_karambit", "ATH_R_burnier", "ATH_R_burnier_separator", "ATH_R_flashlight", "ATH_R_folding001", "ATH_R_folding002", "ATH_R_folding003", "ATH_R_folding004", "ATH_R_folding005", "ATH_R_folding006", "ATH_R_grenade", "ATH_R_handgun01", "ATH_R_handgun02", "ATH_R_karambit", "ATH_R_katana", "ATH_R_spear", "ATH_R_spear_2nd", "ATH_R_weapon001", "ATH_Spine1_separator", "ATH_cane", "ATH_chest_beam", "ATH_katanaL_1st", "ATH_katanaL_2nd", "ATH_katanaR_1st", "ATH_katanaR_2nd", "ATH_katasaya_1st", "ATH_katasaya_2nd", "ATH_katatuka", "ATH_mnt_C_burnier_back", "ATH_mnt_L_burnier_back", "ATH_mnt_R_burnier_back", "ATH_pikL_1st", "ATH_pyaL_1st", "ATH_pyaL_2nd", "ATH_pyaR_1st", "ATH_pyaR_2nd", "ATH_pyaR_B_1st", "ATH_pyaR_B_2nd", "ATH_saya_1st", "ATH_saya_2nd", "ATH_swordR_1st", "ATH_swordR_2nd", "ATH_sword_back", "ATH_tail_01", "ATH_tail_02", "ATH_tail_03", "ATH_tail_04", "ATH_tail_05", "ATH_tail_06", "ATH_tail_07", "ATH_tail_08", "ATH_tail_09", "ATH_tail_10", "ATH_tail_11", "ATH_tail_12", "ATH_tail_13", "ATH_tail_14", "ATH_tail_15", "ATH_tail_16", "ATH_thirdeye_beam", "ATH_tuka_top", "ATH_visor001", "ATH_visor002", "ATH_visor003", "ATH_visor004", "BASE", "BUKI_1_jnt", "BUKI_2_jnt", "C_Leg", "HARA_ROT1", "Head", "Hip", "KOSI_NULL2", "L_Foot", "L_Hand", "L_Have", "L_Have2", "L_LowerArm", "L_LowerLeg", "L_Shoulder", "L_Toe", "L_UpperArm", "L_UpperLeg", "MUKI", "MUNE_jnt", "Neck", "Neck2", "PHY_Hip__a001", "PHY_Hip__a002", "PHY_Hip__a003", "PHY_Hip__a004", "PHY_Hip__a005", "PHY_Hip__a006", "PHY_Hip__a007", "PHY_Hip__a008", "PMP_L_Chest", "PMP_L_LowerArm", "PMP_L_LowerArm_fore", "PMP_L_LowerLeg", "PMP_L_Shoulder", "PMP_L_UpperArm", "PMP_L_UpperLeg", "PMP_R_Chest", "PMP_R_LowerArm", "PMP_R_LowerArm_fore", "PMP_R_LowerLeg", "PMP_R_Shoulder", "PMP_R_UpperArm", "PMP_R_UpperLeg", "R_Foot", "R_Hand", "R_Have", "R_Have2", "R_LowerArm", "R_LowerLeg", "R_Shoulder", "R_Toe", "R_UpperArm", "R_UpperLeg", "Rot", "Spine1", "Spine2", "Top", "Trans", "mushi_R_1", "mushi_R_2", "mushi_R_3", "mushi_R_4", "mushi_R_5", "mushi_R_6", "mushi_R_7", "mushi_R_8"
}

MASK_EXTRA = {
    "ATH_thirdeye_beam", "C_Leg", "HARA_ROT1", "Head", "Hip", "L_Foot", "L_Hand", "L_Have", "L_LowerArm", "L_LowerLeg", "L_Shoulder", "L_Toe", "L_UpperArm", "L_UpperLeg", "MUKI", "Neck", "PMP_L_Chest", "PMP_L_LowerArm", "PMP_L_LowerArm_fore", "PMP_L_LowerLeg", "PMP_L_Shoulder", "PMP_L_UpperArm", "PMP_L_UpperLeg", "PMP_R_Chest", "PMP_R_LowerArm", "PMP_R_LowerArm_fore", "PMP_R_LowerLeg", "PMP_R_Shoulder", "PMP_R_UpperArm", "PMP_R_UpperLeg", "R_Foot", "R_Hand", "R_Have", "R_LowerArm", "R_LowerLeg", "R_Shoulder", "R_Toe", "R_UpperArm", "R_UpperLeg", "Rot", "Spine1", "Spine2", "Top", "Trans"
}

MASK_SWING = {
    "ATH_Head_Leyelid", "ATH_Head_Reyelid", "ATH_Head_eye", "ATH_L_burnier", "ATH_L_burnier_separator", "ATH_L_got_00", "ATH_L_got_01", "ATH_L_got_Index1", "ATH_L_got_Index2", "ATH_L_got_Index3", "ATH_L_got_Middle1", "ATH_L_got_Middle2", "ATH_L_got_Middle3", "ATH_L_got_Pinky1", "ATH_L_got_Pinky2", "ATH_L_got_Pinky3", "ATH_L_got_Ring1", "ATH_L_got_Ring2", "ATH_L_got_Ring3", "ATH_L_got_Thumb0", "ATH_L_got_Thumb1", "ATH_L_got_Thumb2", "ATH_R_burnier", "ATH_R_burnier_separator", "ATH_Spine2_Leyelid", "ATH_Spine2_Reyelid", "ATH_Spine2_eye", "ATH_mnt_L_armwing", "ATH_mnt_L_burnier_back", "ATH_mnt_L_chainsaw", "ATH_mnt_R_armwing", "ATH_mnt_R_burnier_back", "ATH_mnt_R_chainsaw", "ATH_pse_featherA_01_l", "ATH_pse_featherA_01_r", "ATH_pse_featherA_02_l", "ATH_pse_featherA_02_r", "ATH_pse_featherA_03_l", "ATH_pse_featherA_03_r", "ATH_pse_featherA_04_l", "ATH_pse_featherA_04_r", "ATH_pse_featherA_05_l", "ATH_pse_featherA_05_r", "ATH_pse_featherB_01_l", "ATH_pse_featherB_01_r", "ATH_pse_featherB_02_l", "ATH_pse_featherB_02_r", "ATH_pse_featherB_03_l", "ATH_pse_featherB_03_r", "ATH_pse_featherB_04_l", "ATH_pse_featherB_04_r", "ATH_pse_featherC_01_l", "ATH_pse_featherC_01_r", "ATH_pse_featherC_02_l", "ATH_pse_featherC_02_r", "ATH_pse_featherC_03_l", "ATH_pse_featherC_03_r", "ATH_pse_launchPadA_01_l", "ATH_pse_launchPadA_01_r", "ATH_pse_launchPadA_02_l", "ATH_pse_launchPadA_02_r", "ATH_pse_launchPadA_03_l", "ATH_pse_launchPadA_03_r", "ATH_pse_launchPadA_04_l", "ATH_pse_launchPadA_04_r", "ATH_pse_launchPadB_01_l", "ATH_pse_launchPadB_01_r", "ATH_pse_launchPadB_02_l", "ATH_pse_launchPadB_02_r", "ATH_pse_launchPadB_03_l", "ATH_pse_launchPadB_03_r", "ATH_pse_launchPadRootA_01_l", "ATH_pse_launchPadRootA_01_r", "ATH_pse_launchPadRootB_01_l", "ATH_pse_launchPadRootB_01_r", "ATH_pse_wing_01_l", "ATH_pse_wing_01_r", "ATH_pse_wing_02_l", "ATH_pse_wing_02_r", "ATH_wingL_1st", "ATH_wingL_2nd", "ATH_wingL_5th", "ATH_wingL_6th", "ATH_wingL_top", "ATH_wingR_1st", "ATH_wingR_2nd", "ATH_wingR_5th", "ATH_wingR_6th", "ATH_wingR_top", "L_Have", "OPT600_haneLtop", "OPT601_haneL1st", "OPT602_haneL2nd", "OPT603_haneRtop", "OPT604_haneR1st", "OPT605_haneR2nd", "OPT606_haneL3rd", "OPT607_haneL4th", "OPT608_haneR3rd", "OPT609_haneR4th", "OPT702_wingL_2nd", "OPT703_wingL_3rd", "OPT704_wingL_top", "OPT705_wingL_top", "OPT720_wingR_top", "OPT721_wingR_1st", "OPT722_wingR_2nd", "OPT723_wingR_3rd", "OPT724_wingR_top", "OPT725_wingR_top", "OPT900_wingL_top", "OPT901_wingL_1st", "OPT902_wingL_2nd", "OPT903_wingL_3rd", "OPT904_wingL_top", "OPT905_wingL_top", "OPT920_wingR_top", "OPT921_wingR_1st", "OPT922_wingR_2nd", "OPT923_wingR_3rd", "OPT924_wingR_top", "OPT925_wingR_top", "OPT950_wingL_top", "OPT951_wingL_1st", "OPT952_wingL_2nd", "OPT953_wingL_3rd", "OPT954_wingL_top", "OPT955_wingL_top", "OPT970_wingR_top", "OPT971_wingR_1st", "OPT972_wingR_2nd", "OPT973_wingR_3rd", "OPT974_wingR_top", "OPT975_wingR_top", "R_Have", "SWG_wingL_3rd", "SWG_wingL_4th", "SWG_wingR_3rd", "SWG_wingR_4th"
}

# 💡 415개의 페이셜 전체 마스크
MASK_FACIAL = {
    "ASHI_L_jnt", "ASHI_R_jnt", "ATAMA_jnt", "ATH_katanaL_1st", "ATH_katanaL_2nd", "ATH_katanaR_1st", "ATH_katanaR_2nd", "ATH_katasaya_1st", "ATH_katasaya_2nd", "ATH_katatuka", "ATH_tuka_top", "BASE", "Bero1_Joint", "Bero1_Joint_pos", "Bero2_Joint", "Bero3_Joint", "C_Forehead", "C_Jaw_Root", "C_Leg", "C_LipChin", "C_LowChin", "C_LowJaw", "C_LowLip", "C_LowLipZipper", "C_LowMidLip", "C_LowTeeth", "C_Nose1", "C_Nose2", "C_Nose3", "C_Nose4", "C_Tongue1", "C_Tongue2", "C_Tongue3", "C_UpChin", "C_UpJaw", "C_UpLip", "C_UpLipZipper", "C_UpMidLip", "C_UpTeeth", "C_UpThroat", "HARA_ROT1", "HIZA_L_jnt", "HIZA_R_jnt", "Head", "Head_scale_null", "Hip", "Jaw_Joint", "KATA_L_jnt", "KATA_R_jnt", "KOSHI_jnt", "KOSI_NULL2", "KUBI_jnt", "L_Brow1", "L_Brow2", "L_Brow3", "L_Brow4", "L_Cheek1", "L_Cheek2", "L_Cheek3", "L_Cheek4", "L_Cheek5", "L_Cheek6", "L_Cheek7", "L_Cheek8", "L_CheekLine1", "L_CheekLine2", "L_Chobo_Joint", "L_DoubleEyelid1", "L_DoubleEyelid2", "L_DoubleEyelid3", "L_DoubleEyelid4", "L_Eye", "L_EyePupil", "L_Eye_Joint", "L_Eyecorner", "L_Eyelid1", "L_Eyelid2", "L_Foot", "L_Forehead1", "L_Forehead2", "L_Hana_Joint", "L_Hana_transY", "L_Hand", "L_Have", "L_Hoho1_Joint", "L_Hoho2_Joint", "L_Hoho3_Joint", "L_Hoho4_Joint", "L_Hoho5_Joint", "L_HohoShiwa_Joint", "L_Hoho_Joint", "L_Hoho_transY", "L_Index0", "L_Index1", "L_Index2", "L_Index3", "L_Kobana_Joint", "L_LipCorner", "L_LipD_Joint", "L_LipE_Joint", "L_LipU_Joint", "L_LowChin1", "L_LowChin2", "L_LowEar", "L_LowEyelid", "L_LowEyelid1", "L_LowEyelid2", "L_LowEyelid3", "L_LowEyelid4", "L_LowEyelid5", "L_LowLip01Zipper", "L_LowLip1", "L_LowLip11Zipper", "L_LowLip12Zipper", "L_LowLip2", "L_LowLip21Zipper", "L_LowLip22Zipper", "L_LowLip23Zipper", "L_LowLip3", "L_LowLip31Zipper", "R_LowLip32Zipper", "R_LowLip4", "R_LowMidLip1", "R_LowMidLip2", "R_LowMidLip3", "R_LowTeeth", "R_LowerArm", "R_LowerLeg", "R_Mayu1_Joint", "R_Mayu1_transY", "R_Mayu2_Joint", "R_Mayu3_Joint", "R_Middle0", "R_Middle1", "R_Middle2", "R_Middle3", "R_Nose1", "R_Nose2", "R_Pinky0", "R_Pinky1", "R_Pinky2", "R_Pinky3", "R_Ring0", "R_Ring1", "R_Ring2", "R_Ring3", "R_Shoulder", "R_SitaMabuta_Joint", "R_SubBrow1", "R_SubBrow2", "R_SubBrow3", "R_SubBrow4", "R_SubLowEyelid2", "R_SubLowEyelid3", "R_SubLowEyelid4", "R_Temple", "R_ThirdEyelid", "R_Thumb0", "R_Thumb1", "R_Thumb2", "R_Toe", "R_UpChin1", "R_UpEar", "R_UpEyelid", "R_UpEyelid1", "R_UpEyelid2", "R_UpEyelid3", "R_UpEyelid4", "R_UpEyelid5", "R_UpLip01Zipper", "R_UpLip1", "R_UpLip11Zipper", "R_UpLip12Zipper", "R_UpLip2", "R_UpLip21Zipper", "R_UpLip22Zipper", "R_UpLip23Zipper", "R_UpLip3", "R_UpLip31Zipper", "R_UpLip32Zipper", "R_UpMidLip1", "R_UpMidLip2", "R_UpMidLip3", "R_UpTeeth", "R_UpperArm", "R_UpperLeg", "R_UwaMabuta_Joint", "R_throat", "Root", "Rot", "SAKOTSU_L_jnt", "SAKOTSU_R_jnt", "Spine1", "Spine2", "TE_L_jnt", "TE_R_jnt", "Top", "Trans", "UDE_L_jnt", "UDE_R_jnt", "UNKNOWN_0_jnt", "UNKNOWN_10_jnt", "UNKNOWN_11_jnt", "UNKNOWN_12_jnt", "UNKNOWN_13_jnt", "UNKNOWN_14_jnt", "UNKNOWN_15_jnt", "UNKNOWN_16_jnt", "UNKNOWN_17_jnt", "UNKNOWN_18_jnt", "UNKNOWN_19_jnt", "UNKNOWN_1_jnt", "UNKNOWN_20_jnt", "UNKNOWN_21_jnt", "UNKNOWN_22_jnt", "UNKNOWN_23_jnt", "UNKNOWN_24_jnt", "UNKNOWN_25_jnt", "UNKNOWN_26_jnt", "UNKNOWN_27_jnt", "UNKNOWN_28_jnt", "UNKNOWN_29_jnt", "UNKNOWN_2_jnt", "UNKNOWN_30_jnt", "UNKNOWN_31_jnt", "UNKNOWN_32_jnt", "UNKNOWN_33_jnt", "UNKNOWN_34_jnt", "UNKNOWN_35_jnt", "UNKNOWN_36_jnt", "UNKNOWN_37_jnt", "UNKNOWN_38_jnt", "UNKNOWN_39_jnt", "UNKNOWN_3_jnt", "UNKNOWN_40_jnt", "UNKNOWN_41_jnt", "UNKNOWN_42_jnt", "UNKNOWN_43_jnt", "UNKNOWN_44_jnt", "UNKNOWN_45_jnt", "UNKNOWN_46_jnt", "UNKNOWN_47_jnt", "UNKNOWN_48_jnt", "UNKNOWN_49_jnt", "UNKNOWN_4_jnt", "UNKNOWN_50_jnt", "UNKNOWN_51_jnt", "UNKNOWN_52_jnt", "UNKNOWN_53_jnt", "UNKNOWN_54_jnt", "UNKNOWN_5_jnt", "UNKNOWN_6_jnt", "UNKNOWN_7_jnt", "UNKNOWN_8_jnt", "UNKNOWN_9_jnt"
}

# 💡 1. 풀바디와 겹치는 더미 데이터 마스크 (교집합)
MASK_FACIAL_DUMMY = MASK_FACIAL.intersection(MASK_FULLBODY)

# 💡 2. 순수 페이셜 전용 데이터 마스크 (차집합)
MASK_FACIAL_EXCLUSIVE = MASK_FACIAL - MASK_FULLBODY

CATEGORY_MASKS = {
    'FULLBODY': MASK_FULLBODY.union(MASK_EXTRA),
    'EXTRA': MASK_FULLBODY.union(MASK_EXTRA),
    'HAND': MASK_HAND_L.union(MASK_HAND_R), 
    'SWING': MASK_SWING,
    'FACIAL': MASK_FACIAL, # core.py에서 조건에 따라 동적으로 교체됩니다.
}