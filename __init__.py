bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (0, 6, 0), 
    "blender": (3, 6, 0), 
    "location": "File > Import-Export",
    "description": "Import/Export Polaris & TK7 modular animation data.",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(profiles_tk8)
    importlib.reload(profiles_tk7)
    importlib.reload(core_tk8)
    importlib.reload(core_tk7)
    importlib.reload(export_core)
else:
    import bpy
    from . import profiles_tk8
    from . import profiles_tk7
    from . import core_tk8
    from . import core_tk7
    from . import export_core

import os
import bpy.utils.previews
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Menu

custom_icons = None

# =========================================================
# 1. Polaris (TK8) Import Classes
# =========================================================
class ImportPolarisBase(ImportHelper):
    bl_options = {'REGISTER', 'UNDO'}
    
    armature_format: EnumProperty(
        name="Armature",
        items=[
            ('TK7', "TK7", "Import to Tekken 7 Armature"),
            ('TK8', "TK8", "Import to Polaris (Tekken 8) Armature")
        ],
        default='TK8'
    )
    
    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj: return {'CANCELLED'}
        include_dummy = getattr(self, "include_fullbody_dummy", False)
        
        # TK8 선택 시 A-Pose 보정 활성화
        do_apose = (self.armature_format == 'TK8')
        
        core_tk8.import_tk8_anim(self.filepath, obj, self.anim_type, do_apose, include_dummy)
        return {'FINISHED'}

class ImportPolarisFullbody(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_fullbody"; bl_label = "Import Fullbody (.bin)"; filename_ext = ".bin"; filter_glob: StringProperty(default="*.bin", options={'HIDDEN'}); anim_type = 'FULLBODY'
class ImportPolarisHand(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_hand"; bl_label = "Import Hand (.anmhd)"; filename_ext = ".anmhd"; filter_glob: StringProperty(default="*.anmhd", options={'HIDDEN'}); anim_type = 'HAND'
class ImportPolarisFacial(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_facial"; bl_label = "Import Facial (.anmfa)"; filename_ext = ".anmfa"; filter_glob: StringProperty(default="*.anmfa", options={'HIDDEN'}); anim_type = 'FACIAL'; include_fullbody_dummy: BoolProperty(name="Include fullbody dummy", default=False)
class ImportPolarisSwing(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_swing"; bl_label = "Import Swing (.anmsw)"; filename_ext = ".anmsw"; filter_glob: StringProperty(default="*.anmsw", options={'HIDDEN'}); anim_type = 'SWING'
class ImportPolarisCamera(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_camera"; bl_label = "Import Camera (.anmca)"; filename_ext = ".anmca"; filter_glob: StringProperty(default="*.anmca", options={'HIDDEN'}); anim_type = 'CAMERA'
class ImportPolarisExtra(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_extra"; bl_label = "Import Extra (.anmex)"; filename_ext = ".anmex"; filter_glob: StringProperty(default="*.anmex", options={'HIDDEN'}); anim_type = 'EXTRA'

# =========================================================
# 2. TK7 Import Classes
# =========================================================
class ImportTK7Fullbody(Operator, ImportHelper):
    bl_idname = "import_anim.tk7_fullbody"
    bl_label = "Import TK7 Fullbody (.bin)"
    filename_ext = ".bin"
    filter_glob: StringProperty(default="*.bin", options={'HIDDEN'})
    
    armature_format: EnumProperty(
        name="Armature",
        items=[
            ('TK7', "TK7", "Import to Tekken 7 Armature"),
            ('TK8', "TK8", "Import to Polaris (Tekken 8) Armature")
        ],
        default='TK7'
    )
    
    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj: return {'CANCELLED'}
        
        do_apose = (self.armature_format == 'TK8')
        core_tk7.import_tk7_anim(self.filepath, obj, 'TK7_FULLBODY', do_apose)
        return {'FINISHED'}

# =========================================================
# 3. Polaris (TK8) Export Classes 
# =========================================================
class ExportPolarisBase(ExportHelper):
    bl_options = {'REGISTER'}

    apply_apose_offset: BoolProperty(
        name="Revert A-Pose Offset",
        description="Reverts A-Pose offsets back to TK8 engine format.",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        obj = context.view_layer.objects.active
        include_dummy = getattr(self, "include_fullbody_dummy", False)
        
        export_core.execute_export(self.filepath, obj, self.anim_type, self.apply_apose_offset, include_dummy)
        self.report({'INFO'}, f"Polaris [{self.anim_type}] Export Completed! -> {os.path.basename(self.filepath)}")
        return {'FINISHED'}

class ExportPolarisFullbody(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_fullbody"; bl_label = "Export Fullbody (.bin)"; filename_ext = ".bin"; filter_glob: StringProperty(default="*.bin", options={'HIDDEN'}); anim_type = 'FULLBODY'
class ExportPolarisHand(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_hand"; bl_label = "Export Hand (.anmhd)"; filename_ext = ".anmhd"; filter_glob: StringProperty(default="*.anmhd", options={'HIDDEN'}); anim_type = 'HAND'
class ExportPolarisFacial(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_facial"; bl_label = "Export Facial (.anmfa)"; filename_ext = ".anmfa"; filter_glob: StringProperty(default="*.anmfa", options={'HIDDEN'}); anim_type = 'FACIAL'; include_fullbody_dummy: BoolProperty(name="Include fullbody dummy", default=False)
class ExportPolarisSwing(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_swing"; bl_label = "Export Swing (.anmsw)"; filename_ext = ".anmsw"; filter_glob: StringProperty(default="*.anmsw", options={'HIDDEN'}); anim_type = 'SWING'
class ExportPolarisExtra(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_extra"; bl_label = "Export Extra (.anmex)"; filename_ext = ".anmex"; filter_glob: StringProperty(default="*.anmex", options={'HIDDEN'}); anim_type = 'EXTRA'

# =========================================================
# 4. UI Menus
# =========================================================
class IMPORT_MT_polaris_tk(Menu):
    bl_idname = "IMPORT_MT_polaris_tk"
    bl_label = "Polaris TK Animation"
    def draw(self, context):
        layout = self.layout
        layout.operator(ImportPolarisFullbody.bl_idname, text="Fullbody Animation (.bin)")
        layout.operator(ImportPolarisHand.bl_idname, text="Hand Animation (.anmhd)")
        layout.operator(ImportPolarisFacial.bl_idname, text="Facial Animation (.anmfa)")
        layout.operator(ImportPolarisSwing.bl_idname, text="Swing Animation (.anmsw)")
        layout.separator()
        layout.operator(ImportPolarisCamera.bl_idname, text="Camera Animation (.anmca)")
        layout.separator()
        layout.operator(ImportPolarisExtra.bl_idname, text="Extra Animation (.anmex)")

class IMPORT_MT_tk7_anim(Menu):
    bl_idname = "IMPORT_MT_tk7_anim"
    bl_label = "TK7 Animation"
    def draw(self, context):
        self.layout.operator(ImportTK7Fullbody.bl_idname, text="Fullbody Animation (.bin)")

class EXPORT_MT_polaris_tk(Menu):
    bl_idname = "EXPORT_MT_polaris_tk"
    bl_label = "Polaris TK Animation"
    def draw(self, context):
        layout = self.layout
        layout.operator(ExportPolarisFullbody.bl_idname, text="Fullbody Animation (.bin)")
        layout.operator(ExportPolarisHand.bl_idname, text="Hand Animation (.anmhd)")
        layout.operator(ExportPolarisFacial.bl_idname, text="Facial Animation (.anmfa)")
        layout.operator(ExportPolarisSwing.bl_idname, text="Swing Animation (.anmsw)")
        layout.separator()
        layout.operator(ExportPolarisExtra.bl_idname, text="Extra Animation (.anmex)")

def menu_func_import(self, context):
    global custom_icons
    icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0
    tk7_id = custom_icons["tk7_logo"].icon_id if custom_icons and "tk7_logo" in custom_icons else 0
    self.layout.menu(IMPORT_MT_polaris_tk.bl_idname, icon_value=icon_id)
    self.layout.menu(IMPORT_MT_tk7_anim.bl_idname, icon_value=tk7_id)

def menu_func_export(self, context):
    global custom_icons
    icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0
    self.layout.menu(EXPORT_MT_polaris_tk.bl_idname, icon_value=icon_id)

classes = (
    ImportPolarisFullbody, ImportPolarisHand, ImportPolarisFacial, ImportPolarisSwing, ImportPolarisCamera, ImportPolarisExtra, ImportTK7Fullbody,
    ExportPolarisFullbody, ExportPolarisHand, ExportPolarisFacial, ExportPolarisSwing, ExportPolarisExtra,
    IMPORT_MT_polaris_tk, IMPORT_MT_tk7_anim, EXPORT_MT_polaris_tk
)

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    
    p_icon = os.path.join(icons_dir, "polaris.png")
    if os.path.exists(p_icon): custom_icons.load("polaris_logo", p_icon, 'IMAGE')
    t_icon = os.path.join(icons_dir, "TekkenGame.png")
    if os.path.exists(t_icon): custom_icons.load("tk7_logo", t_icon, 'IMAGE')
        
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    global custom_icons
    if custom_icons is not None:
        bpy.utils.previews.remove(custom_icons)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()