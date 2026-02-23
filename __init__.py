bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (0, 1, 0), 
    "blender": (3, 6, 0), 
    "location": "File > Import-Export",
    "description": "Import Polaris (.bin) modular animation data.",
    "category": "Import-Export",
}

# =========================================================
# [마법의 리로드 코드] 무조건 파일 '최상단'에 위치해야 합니다!
# =========================================================
if "bpy" in locals():
    import importlib
    importlib.reload(profiles)
    importlib.reload(core)
else:
    import bpy
    from . import profiles
    from . import core
# =========================================================

import os
import bpy.utils.previews
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator

custom_icons = None

class ImportPolarisTKAnimation(Operator, ImportHelper):
    bl_idname = "import_anim.polaris_tk"
    bl_label = "Import Polaris TK Anim"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})

    anim_type: EnumProperty(
        name="Animation Type",
        description="Select the type of animation to apply the correct bone profiles",
        items=(
            ('FULLBODY', "Fullbody", "전신 애니메이션 (Spine, Legs, Arms)"),
            ('HAND', "Hand", "손가락 전용 애니메이션"),
            ('FACIAL', "Facial", "얼굴 표정 애니메이션"),
            ('WING', "Wing", "날개 및 특수 본 애니메이션"),
            ('CAMERA', "Camera", "카메라 애니메이션"),
            ('EXTRA', "Extra", "기타 엑스트라 애니메이션"),
        ),
        default='FULLBODY',
    )

    apply_apose_offset: BoolProperty(
        name="ImportToPolaris(A-Pose Base)",
        description="원본(A-Pose) 뼈대에 T-Pose 애니메이션을 맞추기 위해 관절에 추가 회전 오프셋을 적용합니다.",
        default=True,
    )

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "뷰포트에서 캐릭터의 Armature(뼈대)를 선택해주세요.")
            return {'CANCELLED'}

        # 이제 core가 완벽하게 인식됩니다!
        missing_bones = core.execute_import(self.filepath, obj, self.anim_type, self.apply_apose_offset)

        if missing_bones:
            missing_msg = f"일부 뼈대를 찾지 못해 건너뛰었습니다 ({len(missing_bones)}개). 시스템 콘솔을 확인하세요."
            self.report({'WARNING'}, missing_msg)
            print(f"[*] 미구현/누락 뼈대 목록: {', '.join(missing_bones)}")
            
        self.report({'INFO'}, f"Polaris [{self.anim_type}] Animation Import DONE!")
        return {'FINISHED'}

def menu_func_import(self, context):
    global custom_icons
    if custom_icons and "polaris_logo" in custom_icons:
        self.layout.operator(ImportPolarisTKAnimation.bl_idname, text="Polaris TK Animation (.bin)", icon_value=custom_icons["polaris_logo"].icon_id)
    else:
        self.layout.operator(ImportPolarisTKAnimation.bl_idname, text="Polaris TK Animation (.bin)", icon='ACTION')

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    icon_path = os.path.join(icons_dir, "polaris.png")
    
    if os.path.exists(icon_path):
        custom_icons.load("polaris_logo", icon_path, 'IMAGE')
    else:
        print(f"[Polaris TK] 커스텀 아이콘을 찾을 수 없습니다: {icon_path}")
        
    bpy.utils.register_class(ImportPolarisTKAnimation)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    global custom_icons
    if custom_icons is not None:
        bpy.utils.previews.remove(custom_icons)
        
    bpy.utils.unregister_class(ImportPolarisTKAnimation)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()