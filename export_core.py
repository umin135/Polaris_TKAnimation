import bpy
import struct
import mathutils
import math
import os
import base64
from .profiles_tk8 import PROFILE_REGISTRY, DEFAULT_FALLBACK, APOSE_OFFSETS, CATEGORY_MASKS, IGNORE_BONES

# kaz_idle_ori.bin 에서 추출한 FlatBuffers 헤더 (4684 bytes)
# block_c_base = 4684 (0x124C)
_FULLBODY_HEADER_B64 = (
    "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"
    "AAAAAQ=="
)

def _load_fullbody_template():
    """내장된 base64 헤더를 디코딩하여 FlatBuffers 헤더 bytearray를 반환합니다.
    ori.bin 파일 참조 없이 동작합니다."""
    raw = base64.b64decode(_FULLBODY_HEADER_B64)
    return bytearray(raw), None


# ==============================================================================
# HAND (왼손) FlatBuffers 헤더 — TEST_hand.anmhd 에서 추출 (0x88C = 2188 bytes)
# ==============================================================================
_HAND_L_HEADER_B64 = (
    "FAAAAFBBTk0MAA4AAAAAAAcACAAMAAAAAAAAASAAAAAAABoAKAAAAAQACAAMABAAFAAYABwAAAAg"
    "ACQAGgAAAOUAAAAAAHBCAQAAABgAAACMCAAAoAMAAKADAACgAwAAGAAAAAEAAAAgAAAADAAMAAAA"
    "AAAEAAgADAAAAAAAgD8EAAAAAAAAAC79//8BAAAABAAAABMAAADMAgAAnAIAAHQCAABMAgAAJAIA"
    "APwBAADUAQAArAEAAIQBAABcAQAANAEAAAwBAADoAAAAxAAAAKAAAAB4AAAAUAAAACgAAAAEAAAA"
    "iv3//xAAAAAEAAAAAQAAANQCAAAHAAAATF9SaW5nMACq/f//EAAAAAQAAAABAAAANAMAAAgAAABM"
    "X0luZGV4MAAAAADO/f//EAAAAAQAAAABAAAA0AIAAAkAAABMX01pZGRsZTAAAADy/f//EAAAAAQA"
    "AAABAAAAbAMAAAgAAABMX1Bpbmt5MgAAAAAW/v//EAAAAAQAAAABAAAAyAMAAAcAAABMX1Jpbmcz"
    "ADb+//8QAAAABAAAAAEAAADoAwAABwAAAExfUmluZzIAVv7//xAAAAAEAAAAAQAAAAgEAAAHAAAA"
    "TF9SaW5nMQB2/v//EAAAAAQAAAABAAAAKAMAAAgAAABMX1Bpbmt5MQAAAACa/v//EAAAAAQAAAAB"
    "AAAABAQAAAkAAABMX01pZGRsZTMAAAC+/v//EAAAAAQAAAABAAAAYAIAAAgAAABMX1Bpbmt5MwAA"
    "AADi/v//EAAAAAQAAAABAAAAPAQAAAkAAABMX01pZGRsZTEAAAAG////EAAAAAQAAAABAAAAWAQA"
    "AAgAAABMX0luZGV4MwAAAAAq////EAAAAAQAAAABAAAA9AAAAAgAAABMX1Bpbmt5MAAAAABO////"
    "EAAAAAQAAAABAAAAkAMAAAkAAABMX01pZGRsZTIAAABy////EAAAAAQAAAABAAAALAQAAAgAAABM"
    "X0luZGV4MgAAAACW////EAAAAAQAAAABAAAASAQAAAgAAABMX0luZGV4MQAAAAC6////EAAAAAQA"
    "AAABAAAAZAQAAAgAAABMX1RodW1iMgAAAADe////EAAAAAQAAAABAAAAmAQAAAgAAABMX1RodW1i"
    "MQAACgAMAAAABAAIAAoAAAAQAAAABAAAAAEAAADQBAAACAAAAExfVGh1bWIwAAAAAL77//8kAAAA"
    "AQAAAAIAAAABAAAAJAAAAGADAAAsAAAABAAAAAAAAAAJAAAAVHJhbnNmb3JtAAAASvv//wABAQH+"
    "+///JAAAAAEAAAACAAAAAQAAACQAAAAwAwAALAAAAAQAAAAAAAAACQAAAFRyYW5zZm9ybQAAAIr7"
    "//8AAQEBPvz//yQAAAABAAAAAgAAAAEAAAAkAAAAAAMAACwAAAAEAAAAAAAAAAkAAABUcmFuc2Zv"
    "cm0AAADK+///AAEBAX78//8kAAAAAQAAAAIAAAABAAAAJAAAANACAAAsAAAABAAAAAAAAAAJAAAA"
    "VHJhbnNmb3JtAAAACvz//wABAQG+/P//JAAAAAEAAAACAAAAAQAAACQAAACgAgAALAAAAAQAAAAA"
    "AAAACQAAAFRyYW5zZm9ybQAAAEr8//8AAQEB/vz//yQAAAABAAAAAgAAAAEAAAAkAAAAcAIAACwA"
    "AAAEAAAAAAAAAAkAAABUcmFuc2Zvcm0AAACK/P//AAEBAT79//8kAAAAAQAAAAIAAAABAAAAJAAA"
    "AEACAAAsAAAABAAAAAAAAAAJAAAAVHJhbnNmb3JtAAAAyvz//wABAQF+/f//JAAAAAEAAAACAAAA"
    "AQAAACQAAAAQAgAALAAAAAQAAAAAAAAACQAAAFRyYW5zZm9ybQAAAAr9//8AAQEBvv3//yQAAAAB"
    "AAAAAgAAAAEAAAAkAAAA4AEAACwAAAAEAAAAAAAAAAkAAABUcmFuc2Zvcm0AAABK/f//AAEBAf79"
    "//8kAAAAAQAAAAIAAAABAAAAJAAAALABAAAsAAAABAAAAAAAAAAJAAAAVHJhbnNmb3JtAAAAiv3/"
    "/wABAQE+/v//JAAAAAEAAAACAAAAAQAAACQAAACAAQAALAAAAAQAAAAAAAAACQAAAFRyYW5zZm9y"
    "bQAAAMr9//8AAQEBfv7//yQAAAABAAAAAgAAAAEAAAAkAAAAUAEAACwAAAAEAAAAAAAAAAkAAABU"
    "cmFuc2Zvcm0AAAAK/v//AAEBAb7+//8kAAAAAQAAAAIAAAABAAAAJAAAACABAAAsAAAABAAAAAAA"
    "AAAJAAAAVHJhbnNmb3JtAAAASv7//wABAQH+/v//JAAAAAEAAAACAAAAAQAAACQAAADwAAAALAAA"
    "AAQAAAAAAAAACQAAAFRyYW5zZm9ybQAAAIr+//8AAQEBPv///yQAAAABAAAAAgAAAAEAAAAkAAAA"
    "wAAAACwAAAAEAAAAAAAAAAkAAABUcmFuc2Zvcm0AAADK/v//AAEBAX7///8kAAAAAQAAAAIAAAAB"
    "AAAAJAAAAJAAAAAsAAAABAAAAAAAAAAJAAAAVHJhbnNmb3JtAAAACv///wABAQG+////JAAAAAEA"
    "AAACAAAAAQAAACQAAABgAAAALAAAAAQAAAAAAAAACQAAAFRyYW5zZm9ybQAAAKr///8AAAABAQEW"
    "ACQAAAAEAAgADAAQABQAGAAcACAAFgAAACQAAAABAAAAAgAAAAEAAAAwAAAAMAAAACwAAAAEAAAA"
    "AAAAAAkAAABUcmFuc2Zvcm0ADgAKAAAABwAAAAgACQAOAAAAAAAAAQEBFgAgAAAABAAIAAwAEAAU"
    "AAAAGAAcABYAAAAgAAAAAQAAAAIAAAABAAAALAAAACwAAAAEAAAAAAAAAAkAAABUcmFuc2Zvcm0A"
    "DgAIAAAABQAAAAYABwAOAAAAAAEBAQ=="
)

# ==============================================================================
# HAND 왼손 트랙 정보 — TEST_hand.anmhd 에서 추출
# (bone_name, enc_orig, c_rel_orig, t_tbl, tf4, tf6, tf7)
#   enc_orig  : 원본 인코딩 (2=static)
#   c_rel_orig: C-블록 정렬 기준 (sorted → C-블록 작성 순서)
#   t_tbl     : 헤더 내 Track 테이블 절대 오프셋
#   tf4=16    : sample_count 필드 오프셋 (항상 16)
#   tf6       : c_rel 필드 오프셋 (0이면 short vtable, 필드 없음)
#   tf7       : c_size 필드 오프셋 (ob=32→24, ob=36→28)
# ==============================================================================
_HAND_L_TRACK_INFO = [
    ("L_Thumb0",  2, 0x000, 0x844, 16,  0, 24),
    ("L_Thumb1",  2, 0x030, 0x7E0, 16, 24, 28),
    ("L_Thumb2",  2, 0x060, 0x788, 16, 24, 28),
    ("L_Index1",  2, 0x090, 0x748, 16, 24, 28),
    ("L_Index2",  2, 0x0C0, 0x708, 16, 24, 28),
    ("L_Index3",  2, 0x0F0, 0x6C8, 16, 24, 28),
    ("L_Middle1", 2, 0x120, 0x688, 16, 24, 28),
    ("L_Middle2", 2, 0x150, 0x648, 16, 24, 28),
    ("L_Middle3", 2, 0x180, 0x608, 16, 24, 28),
    ("L_Ring1",   2, 0x1B0, 0x5C8, 16, 24, 28),
    ("L_Ring2",   2, 0x1E0, 0x588, 16, 24, 28),
    ("L_Ring3",   2, 0x210, 0x548, 16, 24, 28),
    ("L_Pinky1",  2, 0x240, 0x508, 16, 24, 28),
    ("L_Pinky2",  2, 0x270, 0x4C8, 16, 24, 28),
    ("L_Pinky3",  2, 0x2A0, 0x488, 16, 24, 28),
    ("L_Index0",  2, 0x2D0, 0x448, 16, 24, 28),
    ("L_Middle0", 2, 0x300, 0x408, 16, 24, 28),
    ("L_Ring0",   2, 0x330, 0x3C8, 16, 24, 28),
    ("L_Pinky0",  2, 0x360, 0x388, 16, 24, 28),
]
_HAND_L_CBLOCK_ORDER = sorted(_HAND_L_TRACK_INFO, key=lambda x: x[2])

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



# aux 필드 값 (FlatBuffers Track 테이블)
# Trans=56, Top=52, 나머지 41개=36 (kaz 전수 확인 기준)
_AUX_MAP = {"Trans": 56, "Top": 52}


def _build_panm_flatbuf_header(total_frames, bone_enc, new_c_rel, raw_size):
    """
    PANM FlatBuffers 헤더를 scratch에서 빌드합니다. 외부 파일 참조 없음.
    total_frames : 총 프레임 수
    bone_enc     : dict {bone_name: enc (1 or 2)}
    new_c_rel    : dict {bone_name: block_c_rel}
    raw_size     : C-블록 전체 바이트 크기
    반환값: bytearray (완성된 PANM FlatBuffers 헤더, C-블록 불포함)
    """
    buf = bytearray()
    _pending = {}       # label -> [patch_positions] for uoffsets
    _pending_soff = {}  # label -> (patch_pos, table_pos) for deferred soffsets

    def _pos():
        return len(buf)

    def _pad(n):
        r = (-_pos()) % n
        if r:
            buf.extend(b'\x00' * r)

    def _wu16(v):
        buf.extend(struct.pack('<H', v & 0xFFFF))

    def _wu32(v):
        _pad(4)
        buf.extend(struct.pack('<I', v & 0xFFFFFFFF))

    def _wf32(v):
        _pad(4)
        buf.extend(struct.pack('<f', v))

    def _place_uoff(label):
        """4-byte aligned placeholder uoffset; patched when _label() is called."""
        _pad(4)
        pos = _pos()
        buf.extend(b'\x00\x00\x00\x00')
        _pending.setdefault(label, []).append(pos)

    def _label(name):
        """Mark current position; patches all pending uoffsets for this label."""
        target = _pos()
        for patch_pos in _pending.pop(name, []):
            struct.pack_into('<I', buf, patch_pos, target - patch_pos)

    def _write_str(s):
        """FlatBuffers string: length(u32) + bytes + null + 4-byte pad."""
        b = s.encode('utf-8')
        _pad(4)
        buf.extend(struct.pack('<I', len(b)))
        buf.extend(b)
        buf.append(0)
        _pad(4)

    def _place_soff(label):
        """Write placeholder i32 soffset at current (4-byte aligned) position.
        Stores (patch_pos, table_pos) for later patching via _flush_soff."""
        _pad(4)
        patch_pos = _pos()
        buf.extend(struct.pack('<i', 0))
        _pending_soff[label] = (patch_pos, patch_pos)  # table_pos == soffset pos

    def _flush_soff(label, vt_pos):
        """Patch stored soffset: value = table_pos - vt_pos."""
        patch_pos, table_pos = _pending_soff.pop(label)
        struct.pack_into('<i', buf, patch_pos, table_pos - vt_pos)

    # File header
    _place_uoff('panm_root')   # root offset (u32)
    buf.extend(b'PANM')        # file identifier

    # PanmRoot vtable: vt_size=12, ob_size=14, fields=[0,0,7,8]
    vt_root = _pos()
    _wu16(12); _wu16(14)
    _wu16(0); _wu16(0); _wu16(7); _wu16(8)

    # PanmRoot table
    _pad(4); _label('panm_root')
    t = _pos()
    buf.extend(struct.pack('<i', t - vt_root))   # soffset
    buf.extend(b'\x00\x00\x00\x01')             # +4..+6 pad, +7 flag=1
    _place_uoff('panm_anim')                     # +8  animation uoffset
    buf.extend(b'\x00\x00')                      # +12..+13 trailing pad (ob_size=14)

    # PanmAnimation vtable: vt_size=26, ob_size=40
    # fields=[0,4,8,12,16,20,24,28,0,32,36]  (_unused0, _unused8 omitted)
    vt_anim = _pos()
    _wu16(26); _wu16(40)
    _wu16(0);  _wu16(4);  _wu16(8);  _wu16(12); _wu16(16)
    _wu16(20); _wu16(24); _wu16(28); _wu16(0);  _wu16(32); _wu16(36)

    # PanmAnimation table
    _pad(4); _label('panm_anim')
    t = _pos()
    buf.extend(struct.pack('<i', t - vt_anim))
    _wu32(total_frames - 1)    # +4  frame_count_minus_one
    _wf32(60.0)                # +8  fps
    _wu32(1)                   # +12 one
    _place_uoff('groups_vec')  # +16 groups
    # +20 block_c_base: placeholder, patched at the end
    _pad(4); block_c_base_pos = _pos()
    buf.extend(b'\x00\x00\x00\x00')
    _wu32(raw_size)            # +24 raw_size_0
    _wu32(raw_size)            # +28 raw_size_1
    _wu32(raw_size)            # +32 raw_size_2 (field[9]; field[8] _unused8 omitted)
    _place_uoff('offset_mode') # +36 offset_mode

    # groups vector: count=1, one BoneGroup uoffset
    _pad(4); _label('groups_vec')
    _wu32(1)
    _place_uoff('bonegroup')

    # OffsetMode vtable: vt_size=12, ob_size=12, fields=[0,0,4,8]
    vt_om = _pos()
    _wu16(12); _wu16(12)
    _wu16(0); _wu16(0); _wu16(4); _wu16(8)

    # OffsetMode table
    _pad(4); _label('offset_mode')
    t = _pos()
    buf.extend(struct.pack('<i', t - vt_om))
    _wf32(1.0)   # +4 scale
    _wu32(4)     # +8 type
    # OffsetMode ends at 132.

    # Explicit 4-byte pad so BoneGroup lands at 136
    buf.extend(b'\x00\x00\x00\x00')  # pos 132-135

    # BoneGroup table at 136 (soffset deferred -- vt_bone written later at ~368)
    # vt_bone is at a higher address; soffset will be negative, which is valid.
    _label('bonegroup')        # patches groups_vec uoffset -> target=136
    _place_soff('bonegroup')   # soffset placeholder i32 at 136
    _wu32(1)                   # +4 group_type=1
    _place_uoff('bones_vec')   # +8 bones uoffset

    # bones vector at 0x94=148 (game reads bone_count here)
    _pad(4); _label('bones_vec')
    _wu32(len(_FULLBODY_TRACK_INFO))   # count=43 at offset 0x94
    for bn, *_ in _FULLBODY_TRACK_INFO:
        _place_uoff(f'bone_{bn}')      # uoffsets start at 0x98

    # Shared Track vtables
    # "Full": block_c_rel present, ob_size=36, fields=[0,4,8,12,16,20,24,28,32]
    vt_trk_full = _pos()
    _wu16(22); _wu16(36)
    _wu16(0); _wu16(4);  _wu16(8);  _wu16(12); _wu16(16)
    _wu16(20); _wu16(24); _wu16(28); _wu16(32)

    # "Short": block_c_rel=0 omitted, ob_size=32, fields=[0,4,8,12,16,20,0,24,28]
    vt_trk_short = _pos()
    _wu16(22); _wu16(32)
    _wu16(0); _wu16(4);  _wu16(8);  _wu16(12); _wu16(16)
    _wu16(20); _wu16(0); _wu16(24); _wu16(28)

    # Shared vtable for BoneGroup and all Bone tables
    # vt_size=10, ob_size=12, fields=[0,4,8]  (_unused0 omitted)
    vt_bone = _pos()
    _wu16(10); _wu16(12)
    _wu16(0); _wu16(4); _wu16(8)
    # Now that vt_bone position is known, patch BoneGroup's deferred soffset.
    _flush_soff('bonegroup', vt_bone)

    # Per-bone data: Bone table -> tracks_vec -> bone_name_string -> track_table -> "Transform"
    # This layout matches the game's A-Block format:
    #   A-Block+0x04 = name_uoff  -> bone_name_string (16 bytes ahead)
    #   A-Block+0x08 = tracks_uoff -> tracks_vec (4 bytes ahead)
    #   A-Block+0x0C = tracks_vec count=1
    #   A-Block+0x10 = track uoffset -> track_table (after name string)
    #   A-Block+0x14 = name_len (first 4 bytes of bone_name_string)
    #   A-Block+0x18 = name bytes
    for bn, enc_orig, _ in _FULLBODY_TRACK_INFO:
        enc      = bone_enc.get(bn, enc_orig)
        c_rel    = new_c_rel.get(bn, 0)
        sc       = total_frames if enc == 1 else 1
        c_sz     = sc * 44
        aux      = _AUX_MAP.get(bn, 36)
        has_crel = (c_rel != 0)

        # Bone table (12 bytes: soffset + name_uoff + tracks_uoff)
        _pad(4); _label(f'bone_{bn}')
        _place_soff(f'bone_{bn}')   # deferred soffset
        _place_uoff(f'bname_{bn}')  # +4  name uoffset  (-> bone_name_string)
        _place_uoff(f'tvec_{bn}')   # +8  tracks uoffset (-> tracks_vec, 4 bytes ahead)

        # tracks_vec (8 bytes: count=1 + track_uoffset)
        _pad(4); _label(f'tvec_{bn}')
        _wu32(1)
        _place_uoff(f'track_{bn}')

        # Bone name string  <-- A-Block+0x14=name_len, +0x18=name_bytes
        _pad(4); _label(f'bname_{bn}')
        _write_str(bn)

        # Track table  <-- immediately follows bone_name_string
        _pad(4); _label(f'track_{bn}')
        t = _pos()
        if has_crel:
            buf.extend(struct.pack('<i', t - vt_trk_full))
            _place_uoff(f'tname_{bn}')  # +4  name="Transform"
            _wu32(1)     # +8  track_type
            _wu32(enc)   # +12 encoding
            _wu32(sc)    # +16 sample_count
            _wu32(aux)   # +20 aux
            _wu32(c_rel) # +24 block_c_rel
            _wu32(c_sz)  # +28 block_c_size
            _wu32(4)     # +32 align4
        else:
            # Top bone: block_c_rel=0 -> field omitted in vtable
            buf.extend(struct.pack('<i', t - vt_trk_short))
            _place_uoff(f'tname_{bn}')  # +4  name="Transform"
            _wu32(1)     # +8  track_type
            _wu32(enc)   # +12 encoding
            _wu32(sc)    # +16 sample_count
            _wu32(aux)   # +20 aux
            # field[6] block_c_rel: omitted (c_rel==0 = default)
            _wu32(c_sz)  # +24 block_c_size  (field[7])
            _wu32(4)     # +28 align4         (field[8])

        # "Transform" string
        _pad(4); _label(f'tname_{bn}')
        _write_str('Transform')

        # Flush this bone's deferred soffset now that vt_bone is known
        _flush_soff(f'bone_{bn}', vt_bone)

    # Patch block_c_base = total header size
    struct.pack_into('<I', buf, block_c_base_pos, _pos())

    return buf


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


def _load_hand_template(side='L'):
    """LEFT-hand FlatBuffers 헤더를 로드합니다.
    side='R'이면 헤더 내 본 이름의 'L_' 접두사를 'R_'로 패치합니다."""
    buf = bytearray(base64.b64decode(_HAND_L_HEADER_B64))
    if side == 'R':
        i = 0
        while i < len(buf) - 1:
            if buf[i] == ord('L') and buf[i + 1] == ord('_'):
                buf[i] = ord('R')
            i += 1
    return buf


def _export_hand_side(export_path, obj, side, track_info, cblock_order,
                      total_frames, start_frame, end_frame, target_groups):
    """단일 손(L 또는 R) FlatBuffers HAND 파일을 내보냅니다."""
    print(f"[*] HAND ({side}) Export → {export_path}")

    # 1. 뼈대별 enc 결정
    bone_enc = {}
    for bn, enc_orig, *_ in track_info:
        bone_enc[bn] = 1 if _has_keyframes(obj, bn) else enc_orig

    # 2. C-rel 재계산 (animated 뼈 = total_frames×44, static = 44)
    new_c_rel = {}
    c_offset = 0
    for bn, enc_orig, *_ in cblock_order:
        enc = bone_enc[bn]
        new_c_rel[bn] = c_offset
        c_offset += (total_frames * 44 if enc == 1 else 44) + 4
    raw_size = c_offset - 4 + 20

    # 3. 템플릿 로드 및 패치
    buf = _load_hand_template(side)
    struct.pack_into('<I', buf, 0x40, total_frames - 1)
    struct.pack_into('<I', buf, 0x54, raw_size)
    struct.pack_into('<I', buf, 0x58, raw_size)
    struct.pack_into('<I', buf, 0x5C, raw_size)

    for bn, enc_orig, c_rel_orig, t_tbl, tf4, tf6, tf7 in track_info:
        enc  = bone_enc[bn]
        nc   = new_c_rel[bn]
        sc   = total_frames if enc == 1 else 1
        c_sz = total_frames * 44 if enc == 1 else 44
        struct.pack_into('<I', buf, t_tbl + 12, enc)
        struct.pack_into('<I', buf, t_tbl + tf4, sc)
        if tf6 != 0:
            struct.pack_into('<I', buf, t_tbl + tf6, nc)
        struct.pack_into('<I', buf, t_tbl + tf7, c_sz)

    # 4. 포즈 데이터 수집
    group_cache = {}
    for bn, *_ in track_info:
        group_cache[bn] = next(
            (g for g in target_groups.values() if bn in g["bones"]),
            DEFAULT_FALLBACK
        )

    scene = bpy.context.scene
    scene.frame_set(start_frame)
    bpy.context.view_layer.update()
    static_data = {
        bn: _read_bone_sample(obj, bn, group_cache[bn], False)
        for bn, enc_orig, *_ in track_info if bone_enc[bn] != 1
    }

    anim_data = {bn: [] for bn, enc_orig, *_ in track_info if bone_enc[bn] == 1}
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for bn in anim_data:
            anim_data[bn].append(_read_bone_sample(obj, bn, group_cache[bn], False))

    # 5. C-블록 구축
    c_block = bytearray()
    for i, (bn, *_) in enumerate(cblock_order):
        is_last = (i == len(cblock_order) - 1)
        if bone_enc[bn] == 1:
            frames = anim_data.get(bn, [])
            while len(frames) < total_frames:
                frames.append(frames[-1] if frames else (1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0.0))
            for sample in frames:
                c_block.extend(struct.pack('<11f', *sample))
        else:
            c_block.extend(struct.pack('<11f', *static_data.get(bn, (1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0.0))))
        if not is_last:
            c_block.extend(bytes(4))
    c_block.extend(bytes(20))

    with open(export_path, 'wb') as f:
        f.write(buf)
        f.write(c_block)

    print(f"[+] HAND ({side}) FlatBuffers Export 완료! ({len(buf) + len(c_block)} bytes)")


def _execute_export_hand(export_path, obj):
    """HAND 애니메이션 FlatBuffers(.anmhd) 내보내기."""
    scene = bpy.context.scene
    start_frame  = int(scene.frame_start)
    end_frame    = int(scene.frame_end)
    total_frames = max(1, end_frame - start_frame + 1)

    from .profiles_tk8 import MASK_HAND_L, MASK_HAND_R
    has_l = any(bn in obj.pose.bones for bn in MASK_HAND_L)
    has_r = any(bn in obj.pose.bones for bn in MASK_HAND_R)

    _, target_groups = PROFILE_REGISTRY.get('HAND', (set(), {}))

    # R 손의 track_info / cblock_order = L 정보에서 이름만 L_→R_ 치환
    def _r_info(info):
        return [(bn.replace('L_', 'R_'), enc, c_rel, t_tbl, tf4, tf6, tf7)
                for bn, enc, c_rel, t_tbl, tf4, tf6, tf7 in info]

    _HAND_R_TRACK_INFO   = _r_info(_HAND_L_TRACK_INFO)
    _HAND_R_CBLOCK_ORDER = _r_info(_HAND_L_CBLOCK_ORDER)

    if has_l:
        _export_hand_side(export_path, obj, 'L',
                          _HAND_L_TRACK_INFO, _HAND_L_CBLOCK_ORDER,
                          total_frames, start_frame, end_frame, target_groups)
    if has_r:
        if has_l:
            base, ext = os.path.splitext(export_path)
            r_path = base + '_R' + ext
        else:
            r_path = export_path
        _export_hand_side(r_path, obj, 'R',
                          _HAND_R_TRACK_INFO, _HAND_R_CBLOCK_ORDER,
                          total_frames, start_frame, end_frame, target_groups)


def execute_export(export_path, obj, anim_type, apply_apose=True, include_dummy=False):
    print(f"\n[*] Starting Polaris Export for {anim_type}")
    print(f"[*] Output File: {export_path}")

    if anim_type == 'CAMERA':
        print("[!] Camera export is not supported yet.")
        return

    if anim_type == 'FULLBODY':
        _execute_export_fullbody(export_path, obj, apply_apose)
        return

    if anim_type == 'HAND':
        _execute_export_hand(export_path, obj)
        return

    # ── 기타 카테고리: 기존 커스텀 포맷 내보내기 ──────────────────────────────
    _execute_export_custom(export_path, obj, anim_type, apply_apose, include_dummy)


# ==============================================================================
# FULLBODY 전용 내보내기 (FlatBuffers scratch 빌드)
# ==============================================================================
def _execute_export_fullbody(export_path, obj, apply_apose):
    """
    PANM FlatBuffers 헤더를 scratch에서 빌드하여 정확한 바이너리를 생성합니다.
    C-블록 데이터는 Blender 포즈 + 아마추어 레스트 포즈에서 계산합니다.
    """
    scene = bpy.context.scene
    start_frame  = int(scene.frame_start)
    end_frame    = int(scene.frame_end)
    total_frames = max(1, end_frame - start_frame + 1)

    root_bones, target_groups = PROFILE_REGISTRY.get('FULLBODY', (set(), {}))
    do_apose_correction = apply_apose

    # 1. 트랙 인포에서 뼈대 집합 확인
    track_names = {t[0] for t in _FULLBODY_TRACK_INFO}
    missing = [n for n in track_names if n not in obj.pose.bones]
    if missing:
        print(f"[!] 아마추어에 누락된 뼈대: {missing[:5]}{'...' if len(missing)>5 else ''}")

    print(f"[*] 프레임 범위: {start_frame}~{end_frame} (총 {total_frames}프레임)")

    # 2. 각 뼈대 그룹 정보 캐시
    group_cache = {}
    for bone_name, enc, *_ in _FULLBODY_TRACK_INFO:
        grp = next(
            (g for g in target_groups.values() if bone_name in g["bones"]),
            DEFAULT_FALLBACK
        )
        group_cache[bone_name] = grp

    # 3. enc 동적 결정 (키프레임 유무 + 컨스트레인트 기준)
    # Rot 본: 컨스트레인트 무시하고 키프레임만 참조
    _CONSTRAINT_IGNORE_BONES = {"Rot"}

    dynamic_enc = {}
    for bone_name, enc_orig, *_ in _FULLBODY_TRACK_INFO:
        if bone_name in IGNORE_BONES:
            dynamic_enc[bone_name] = enc_orig
        elif bone_name not in _CONSTRAINT_IGNORE_BONES and _has_constraints(obj, bone_name):
            dynamic_enc[bone_name] = 1  # 컨스트레인트 본은 항상 전 프레임 기록
        elif _has_keyframes(obj, bone_name):
            dynamic_enc[bone_name] = 1
        else:
            dynamic_enc[bone_name] = enc_orig

    animated_bones = {n for n, e in dynamic_enc.items() if e == 1 and n not in IGNORE_BONES}
    static_bones   = {n for n, e in dynamic_enc.items() if e == 2 and n not in IGNORE_BONES}
    promoted = animated_bones - {n for n, e, *_ in _FULLBODY_TRACK_INFO if e == 1}
    if promoted:
        print(f"[*] enc=2->1 승격 뼈대: {sorted(promoted)}")

    # 3b. 컨스트레인트 본이 있으면 임시 베이크
    # IK 등 컨스트레인트 결과는 pbone.rotation_quaternion에 반영되지 않으므로
    # visual_keying 베이크로 실제 포즈를 fcurve에 기록한 뒤 사용
    baked_action    = None
    original_action = None
    needs_bake = any(
        bone_name not in _CONSTRAINT_IGNORE_BONES and _has_constraints(obj, bone_name)
        for bone_name in animated_bones
    )
    if needs_bake:
        print("[*] IK/컨스트레인트 본 감지 -> 임시 베이크 시작...")
        original_action, baked_action = _bake_to_temp_action(obj, start_frame, end_frame)
        print(f"[*] 임시 베이크 완료: {baked_action.name}")

    # 4. c_rel 계산 (dynamic_enc 기준)
    new_c_rel = {}
    c_offset  = 0
    for bone_name, enc_orig, *_ in _FULLBODY_CBLOCK_ORDER:
        enc = dynamic_enc[bone_name]
        new_c_rel[bone_name] = c_offset
        c_size    = (total_frames * 44) if enc == 1 else 44
        c_offset += c_size + 4

    raw_size = c_offset - 4 + 20

    # 5. 템플릿 로드 및 패치
    buf = _load_fullbody_template()[0]
    struct.pack_into('<I', buf, 0x40, total_frames - 1)
    struct.pack_into('<I', buf, 0x54, raw_size)
    struct.pack_into('<I', buf, 0x58, raw_size)
    struct.pack_into('<I', buf, 0x5C, raw_size)
    for bone_name, enc_orig, c_rel_orig, t_tbl, tf4, tf6, tf7 in _FULLBODY_TRACK_INFO:
        enc = dynamic_enc[bone_name]
        nc  = new_c_rel[bone_name]
        sc   = total_frames if enc == 1 else 1
        c_sz = total_frames * 44 if enc == 1 else 44
        struct.pack_into('<I', buf, t_tbl + 12, enc)
        struct.pack_into('<I', buf, t_tbl + tf4, sc)
        if tf6 != 0:
            struct.pack_into('<I', buf, t_tbl + tf6, nc)
        struct.pack_into('<I', buf, t_tbl + tf7, c_sz)

    # 6. 레스트 위치 캐시 (비루트 enc=1 뼈대)
    rest_pos_cache = {}
    for bone_name in animated_bones:
        if bone_name not in _FULLBODY_ROOT_BONES:
            grp = group_cache[bone_name]
            rest_pos_cache[bone_name] = _get_rest_pos_engine(obj, bone_name, grp)

    # 7. 프레임별 포즈 데이터 수집 (enc=1 뼈대)
    anim_data = {}
    for bone_name in animated_bones:
        anim_data[bone_name] = []

    for frame_idx, frame in enumerate(range(start_frame, end_frame + 1)):
        scene.frame_set(frame)
        for bone_name in list(anim_data.keys()):
            if bone_name not in obj.pose.bones:
                anim_data[bone_name].append((1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0.0))
                continue

            pbone = obj.pose.bones[bone_name]
            grp   = group_cache[bone_name]

            rx, ry, rz    = grp["basis"]
            do_flip       = grp["flip"]
            ox, oy, oz    = grp["offset"]
            mx, my, mz    = grp["loc_map"]
            scale_div     = grp["scale_div"]
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
            b_rot = b_rot @ post_rot_quat_inv
            b_rot = apose_quat_inv @ b_rot

            is_root = bone_name in _FULLBODY_ROOT_BONES

            M_blender = mathutils.Matrix.LocRotScale(mathutils.Vector((0, 0, 0)), b_rot, pbone.scale)
            M_engine   = C_inv @ M_blender @ C_mat
            _, e_rot, e_sca = M_engine.decompose()
            e_rot = e_rot @ offset_quat_inv

            qw, qx, qy, qz = e_rot.w, e_rot.x, e_rot.y, e_rot.z
            if do_flip:
                qy = -qy

            if is_root:
                b_loc = pbone.location.copy()
                M_bl_loc = mathutils.Matrix.LocRotScale(b_loc, b_rot, pbone.scale)
                M_en_loc = C_inv @ M_bl_loc @ C_mat
                e_loc_root = M_en_loc.decompose()[0]
                px, py, pz = _inverse_loc_map(mx, my, mz, e_loc_root.x, e_loc_root.y, e_loc_root.z)
                if do_flip:
                    py = -py
                px, py, pz = px * scale_div, py * scale_div, pz * scale_div
            else:
                px, py, pz = rest_pos_cache.get(bone_name, (0.0, 0.0, 0.0))

            anim_data[bone_name].append(
                (e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 0.0)
            )

    # 8. 정적 뼈대(enc=2) 샘플 계산
    scene.frame_set(start_frame)
    static_samples = {}
    for bone_name in static_bones:
        grp = group_cache[bone_name]
        static_samples[bone_name] = _get_enc2_sample(
            obj, bone_name, grp, do_apose_correction
        )

    # 9. C-블록 구축 (dynamic_enc 기준)
    c_block = bytearray()
    for i, (bone_name, enc_orig, *_) in enumerate(_FULLBODY_CBLOCK_ORDER):
        enc     = dynamic_enc[bone_name]
        is_last = (i == len(_FULLBODY_CBLOCK_ORDER) - 1)

        if bone_name in IGNORE_BONES:
            sample = static_samples.get(bone_name, (1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0.0))
            c_block.extend(struct.pack('<11f', *sample))
        elif enc == 1:
            frames_data = anim_data.get(bone_name, [])
            while len(frames_data) < total_frames:
                frames_data.append(frames_data[-1] if frames_data else (1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0))
            for sample in frames_data:
                c_block.extend(struct.pack('<11f', *sample))
        else:
            sample = static_samples.get(bone_name, (1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0.0))
            c_block.extend(struct.pack('<11f', *sample))

        if not is_last:
            c_block.extend(bytes(4))

    c_block.extend(bytes(20))

    # 10. 파일 저장
    with open(export_path, 'wb') as f:
        f.write(buf)
        f.write(c_block)

    # 11. 임시 베이크 액션 폐기 및 원본 복원
    if baked_action is not None:
        if obj.animation_data:
            obj.animation_data.action = original_action
        bpy.data.actions.remove(baked_action)
        print("[*] 임시 베이크 액션 폐기 완료, 원본 액션 복원됨")

    print(f"[+] Polaris [FULLBODY] FlatBuffers Export 완료! ({len(buf) + len(c_block)} bytes)")


# ==============================================================================
# 기타 카테고리 내보내기 (기존 커스텀 포맷)
# ==============================================================================
def _read_bone_sample(obj, bone_name, selected_group, do_apose_correction):
    """현재 프레임에서 bone의 PANM 샘플 11개 float를 반환합니다."""
    pbone = obj.pose.bones.get(bone_name)
    if pbone is None:
        return (1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0)

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
    return (e_sca.x, e_sca.y, e_sca.z, qx, qy, qz, qw, px, py, pz, 0.0)


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

    # 그룹 캐시: 뼈대별 프로필 그룹 미리 조회
    group_cache = {}
    for bone_name in export_bones:
        group_cache[bone_name] = next(
            (g for g in target_groups.values() if bone_name in g["bones"]),
            DEFAULT_FALLBACK
        )

    # 뼈대별 애니메이션 여부 판별 (키프레임 2개 이상 = animated, 아니면 static)
    bone_is_animated = {b: _has_keyframes(obj, b) for b in export_bones}
    animated_count = sum(1 for v in bone_is_animated.values() if v)
    static_count   = len(export_bones) - animated_count
    print(f"[*] Animated: {animated_count}  Static: {static_count}")

    # 1. 정적 뼈대: start_frame에서 1회만 읽기
    scene.frame_set(start_frame)
    bpy.context.view_layer.update()
    static_data = {}
    for bone_name in export_bones:
        if not bone_is_animated[bone_name]:
            static_data[bone_name] = _read_bone_sample(
                obj, bone_name, group_cache[bone_name], do_apose_correction
            )

    # 2. 애니메이션 뼈대: 프레임별 순회
    anim_data = {b: [] for b in export_bones if bone_is_animated[b]}
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for bone_name in anim_data:
            anim_data[bone_name].append(
                _read_bone_sample(obj, bone_name, group_cache[bone_name], do_apose_correction)
            )

    # 3. 커스텀 바이너리 구축
    buffer = bytearray(b'\x00' * 0x98)
    struct.pack_into('<I', buffer, 0x40, total_frames - 1)
    struct.pack_into('<I', buffer, 0x94, len(export_bones))

    buffer.extend(b'\x00' * (len(export_bones) * 4))
    bone_c_offset_positions = []

    for i, b_name in enumerate(export_bones):
        is_anim     = bone_is_animated[b_name]
        anim_flag   = 1 if is_anim else 2
        bone_frames = total_frames if is_anim else 1

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
        buffer.extend(struct.pack('<I', 0x24))       # indicator
        buffer.extend(struct.pack('<I', 0))           # +0x10
        buffer.extend(struct.pack('<I', anim_flag))   # +0x14
        buffer.extend(struct.pack('<I', bone_frames)) # +0x18
        buffer.extend(struct.pack('<I', 0))           # +0x1C

        c_offset_pos = len(buffer)
        buffer.extend(struct.pack('<I', 0))           # +0x20: c_rel placeholder
        buffer.extend(struct.pack('<I', 0))           # +0x24
        bone_c_offset_positions.append(c_offset_pos)

    pad_len = (16 - (len(buffer) % 16)) % 16
    buffer.extend(b'\x00' * pad_len)
    first_c_ptr = len(buffer)
    struct.pack_into('<I', buffer, 0x50, first_c_ptr)

    for i, b_name in enumerate(export_bones):
        c_offset = len(buffer) - first_c_ptr
        struct.pack_into('<I', buffer, bone_c_offset_positions[i], c_offset)
        if bone_is_animated[b_name]:
            for frame_data in anim_data[b_name]:
                buffer.extend(struct.pack('<11f', *frame_data))
        else:
            buffer.extend(struct.pack('<11f', *static_data[b_name]))

    with open(export_path, 'wb') as f:
        f.write(buffer)

    print(f"[+] Polaris [{anim_type}] Custom Export 완료!")
