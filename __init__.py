bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (0, 2, 0), 
    "blender": (3, 6, 0), 
    "location": "File > Import-Export",
    "description": "Import Polaris modular animation data by category.",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(profiles)
    importlib.reload(core)
else:
    import bpy
    from . import profiles
    from . import core

import os
import bpy.utils.previews
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Menu

custom_icons = None

# =========================================================
# 1. 임포트 마스터 클래스 (중복 코드 방지용 Base Class)
# =========================================================
class ImportPolarisBase(ImportHelper):
    bl_options = {'REGISTER', 'UNDO'}

    # 💡 옵션 이름과 설명 영문화. 기본값은 True 유지.
    apply_apose_offset: BoolProperty(
        name="Import to Polaris Armature",
        description="Applies A-Pose offsets suitable for Polaris Armature.",
        default=True,
    )

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj:
            self.report({'ERROR'}, "Please select an object in the viewport.")
            return {'CANCELLED'}

        # 카테고리별 오브젝트 검증
        if self.anim_type == 'CAMERA':
            if obj.type != 'CAMERA':
                self.report({'ERROR'}, "Camera animation (.anmca) requires a 'Camera' object to be selected.")
                return {'CANCELLED'}
        else:
            if obj.type != 'ARMATURE':
                self.report({'ERROR'}, f"{self.anim_type} animation requires an 'Armature' object to be selected.")
                return {'CANCELLED'}

        missing_bones = core.execute_import(self.filepath, obj, self.anim_type, self.apply_apose_offset)

        if missing_bones:
            missing_msg = f"Skipped {len(missing_bones)} missing bones."
            self.report({'WARNING'}, missing_msg)
            print(f"[*] Missing bones: {', '.join(missing_bones)}")
            
        self.report({'INFO'}, f"Polaris [{self.anim_type}] Animation Import DONE!")
        return {'FINISHED'}

# =========================================================
# 2. 카테고리별 개별 임포터 (확장자 필터링)
# =========================================================
class ImportPolarisFullbody(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_fullbody"
    bl_label = "Import Fullbody (.bin)"
    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})
    anim_type = 'FULLBODY'

class ImportPolarisHand(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_hand"
    bl_label = "Import Hand (.anmhd)"
    filename_ext = ".anmhd"
    filter_glob: StringProperty(default="*.anmhd", options={'HIDDEN'})
    anim_type = 'HAND'

class ImportPolarisFacial(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_facial"
    bl_label = "Import Facial (.anmfa)"
    filename_ext = ".anmfa"
    filter_glob: StringProperty(default="*.anmfa", options={'HIDDEN'})
    anim_type = 'FACIAL'

class ImportPolarisWing(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_wing"
    bl_label = "Import Wing (.anmwg)"
    filename_ext = ".anmwg"
    filter_glob: StringProperty(default="*.anmwg", options={'HIDDEN'})
    anim_type = 'WING'

class ImportPolarisCamera(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_camera"
    bl_label = "Import Camera (.anmca)"
    filename_ext = ".anmca"
    filter_glob: StringProperty(default="*.anmca", options={'HIDDEN'})
    anim_type = 'CAMERA'

class ImportPolarisExtra(Operator, ImportPolarisBase):
    bl_idname = "import_anim.polaris_extra"
    bl_label = "Import Extra (.anmex)"
    filename_ext = ".anmex"
    filter_glob: StringProperty(default="*.anmex", options={'HIDDEN'})
    anim_type = 'EXTRA'

# =========================================================
# 3. UI 서브 메뉴 구성 (깔끔한 정리)
# =========================================================
class IMPORT_MT_polaris_tk(Menu):
    bl_idname = "IMPORT_MT_polaris_tk"
    bl_label = "Polaris TK Animation"

    def draw(self, context):
        layout = self.layout
        layout.operator(ImportPolarisFullbody.bl_idname, text="Fullbody Animation (.bin)")
        layout.operator(ImportPolarisHand.bl_idname, text="Hand Animation (.anmhd)")
        layout.operator(ImportPolarisFacial.bl_idname, text="Facial Animation (.anmfa)")
        layout.operator(ImportPolarisWing.bl_idname, text="Wing Animation (.anmwg)")
        layout.separator()
        layout.operator(ImportPolarisCamera.bl_idname, text="Camera Animation (.anmca)")
        layout.separator()
        layout.operator(ImportPolarisExtra.bl_idname, text="Extra Animation (.anmex)")

def menu_func_import(self, context):
    global custom_icons
    icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0
    self.layout.menu(IMPORT_MT_polaris_tk.bl_idname, icon_value=icon_id)

# =========================================================
# 4. 등록 (Register)
# =========================================================
classes = (
    ImportPolarisFullbody,
    ImportPolarisHand,
    ImportPolarisFacial,
    ImportPolarisWing,
    ImportPolarisCamera,
    ImportPolarisExtra,
    IMPORT_MT_polaris_tk,
)

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    icon_path = os.path.join(icons_dir, "polaris.png")
    
    if os.path.exists(icon_path):
        custom_icons.load("polaris_logo", icon_path, 'IMAGE')
        
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    global custom_icons
    if custom_icons is not None:
        bpy.utils.previews.remove(custom_icons)
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()