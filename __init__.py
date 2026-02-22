bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (0, 1, 0), 
    "blender": (3, 6, 0), 
    "location": "File > Import-Export",
    "description": "Import Polaris (.bin) modular animation data.",
    "category": "Import-Export",
}

import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, EnumProperty
from bpy.types import Operator
from .core import execute_import

class ImportPolarisTKAnimation(Operator, ImportHelper):
    bl_idname = "import_anim.polaris_tk"
    bl_label = "Import Polaris TK Anim"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})

    # [수정됨] 6가지 카테고리 완벽 반영
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

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "뷰포트에서 캐릭터의 Armature(뼈대)를 선택해주세요.")
            return {'CANCELLED'}

        missing_bones = execute_import(self.filepath, obj, self.anim_type)

        if missing_bones:
            missing_msg = f"일부 뼈대를 찾지 못해 건너뛰었습니다 ({len(missing_bones)}개). 시스템 콘솔을 확인하세요."
            self.report({'WARNING'}, missing_msg)
            print(f"[*] 미구현/누락 뼈대 목록: {', '.join(missing_bones)}")
            
        self.report({'INFO'}, f"Polaris [{self.anim_type}] Animation Import DONE!")
        return {'FINISHED'}

# 커스텀 아이콘을 저장할 글로벌 변수
custom_icons = None

def menu_func_import(self, context):
    global custom_icons
    # 내장 아이콘은 icon='...'을 쓰지만, 커스텀은 icon_value=...를 씁니다!
    self.layout.operator(
        ImportPolarisTKAnimation.bl_idname, 
        text="Polaris TK Animation (.bin)", 
        icon_value=custom_icons["polaris_logo"].icon_id
    )

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    
    # 현재 스크립트(__init__.py) 경로를 기준으로 icons 폴더 찾기
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    
    # 'polaris_logo'라는 이름으로 my_icon.png 파일 로드
    custom_icons.load("polaris_logo", os.path.join(icons_dir, "polaris.png"), 'IMAGE')
    
    bpy.utils.register_class(ImportPolarisTKAnimation)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    global custom_icons
    # 블렌더 메모리 누수 방지를 위해 해제 필수!
    bpy.utils.previews.remove(custom_icons)
    
    bpy.utils.unregister_class(ImportPolarisTKAnimation)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()