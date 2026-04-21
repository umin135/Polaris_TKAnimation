bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (1, 3, 0),
    "blender": (3, 6, 0),
    "location": "File > Import-Export",
    "description": "Import/Export Polaris (Tekken 8) animation data.",
    "category": "Import-Export",
}

if "bpy" in locals():
    import importlib
    importlib.reload(profiles_tk8)
    importlib.reload(core_tk8)
    importlib.reload(export_core)
else:
    import bpy
    from . import profiles_tk8
    from . import core_tk8
    from . import export_core

import os
import shutil
import tempfile
import threading
import urllib.request
import bpy.utils.previews
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Menu

custom_icons = None

_RIG_DOWNLOAD_URL = "https://drive.usercontent.google.com/u/0/uc?id=1SHMQgMCYcJQdhoijfjaNTqneeYpijQAa&export=download"
_download_state   = {"running": False, "done": False, "error": None}

# =========================================================
# 1. Polaris (TK8) Import Classes
# =========================================================
class ImportPolarisBase(ImportHelper):
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.view_layer.objects.active
        if not obj: return {'CANCELLED'}
        include_dummy = getattr(self, "include_fullbody_dummy", False)
        core_tk8.import_tk8_anim(self.filepath, obj, self.anim_type, True, include_dummy)
        return {'FINISHED'}

class ImportPolarisFullbody(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_fullbody"; bl_label = "Import Fullbody (.bin)"; filename_ext = ".bin"; filter_glob: StringProperty(default="*.bin", options={'HIDDEN'}); anim_type = 'FULLBODY'
class ImportPolarisHand(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_hand"; bl_label = "Import Hand (.anmhd)"; filename_ext = ".anmhd"; filter_glob: StringProperty(default="*.anmhd", options={'HIDDEN'}); anim_type = 'HAND'
class ImportPolarisFacial(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_facial"; bl_label = "Import Facial (.anmfa)"; filename_ext = ".anmfa"; filter_glob: StringProperty(default="*.anmfa", options={'HIDDEN'}); anim_type = 'FACIAL'; include_fullbody_dummy: BoolProperty(name="Include fullbody dummy", default=False)
class ImportPolarisSwing(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_swing"; bl_label = "Import Swing (.anmsw)"; filename_ext = ".anmsw"; filter_glob: StringProperty(default="*.anmsw", options={'HIDDEN'}); anim_type = 'SWING'
class ImportPolarisCamera(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_camera"; bl_label = "Import Camera (.anmca)"; filename_ext = ".anmca"; filter_glob: StringProperty(default="*.anmca", options={'HIDDEN'}); anim_type = 'CAMERA'
class ImportPolarisExtra(Operator, ImportPolarisBase): bl_idname = "import_anim.polaris_extra"; bl_label = "Import Extra (.anmex)"; filename_ext = ".anmex"; filter_glob: StringProperty(default="*.anmex", options={'HIDDEN'}); anim_type = 'EXTRA'

# =========================================================
# 2. Polaris (TK8) Export Classes
# =========================================================
class ExportPolarisBase(ExportHelper):
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        obj = context.view_layer.objects.active
        include_dummy = getattr(self, "include_fullbody_dummy", False)
        export_core.execute_export(self.filepath, obj, self.anim_type, True, include_dummy)
        self.report({'INFO'}, f"Polaris [{self.anim_type}] Export Completed! -> {os.path.basename(self.filepath)}")
        return {'FINISHED'}

class ExportPolarisFullbody(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_fullbody"; bl_label = "Export Fullbody (.bin)"; filename_ext = ".bin"; filter_glob: StringProperty(default="*.bin", options={'HIDDEN'}); anim_type = 'FULLBODY'
class ExportPolarisHand(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_hand"; bl_label = "Export Hand (.anmhd)"; filename_ext = ".anmhd"; filter_glob: StringProperty(default="*.anmhd", options={'HIDDEN'}); anim_type = 'HAND'
class ExportPolarisFacial(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_facial"; bl_label = "Export Facial (.anmfa)"; filename_ext = ".anmfa"; filter_glob: StringProperty(default="*.anmfa", options={'HIDDEN'}); anim_type = 'FACIAL'; include_fullbody_dummy: BoolProperty(name="Include fullbody dummy", default=False)
class ExportPolarisSwing(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_swing"; bl_label = "Export Swing (.anmsw)"; filename_ext = ".anmsw"; filter_glob: StringProperty(default="*.anmsw", options={'HIDDEN'}); anim_type = 'SWING'
class ExportPolarisExtra(Operator, ExportPolarisBase): bl_idname = "export_anim.polaris_extra"; bl_label = "Export Extra (.anmex)"; filename_ext = ".anmex"; filter_glob: StringProperty(default="*.anmex", options={'HIDDEN'}); anim_type = 'EXTRA'

# =========================================================
# 3. N-Panel Sidebar
# =========================================================
def _open_template_copy(operator, filename):
    template_path = os.path.join(os.path.dirname(__file__), "template", filename)
    if not os.path.exists(template_path):
        operator.report({'ERROR'}, f"Template not found: {template_path}")
        return {'CANCELLED'}
    tmp_dir = tempfile.mkdtemp(prefix="polaris_")
    tmp_path = os.path.join(tmp_dir, filename)
    shutil.copy2(template_path, tmp_path)
    bpy.ops.wm.open_mainfile(filepath=tmp_path)
    return {'FINISHED'}

class POLARIS_OT_open_template(Operator):
    bl_idname = "polaris.open_template_blend"
    bl_label = "Open Polaris Blend (without IK)"
    bl_description = "Open the bundled Polaris template .blend file (no IK rig)"

    def execute(self, context):
        return _open_template_copy(self, "polaris_template.blend")

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

class POLARIS_OT_open_template_ik(Operator):
    bl_idname = "polaris.open_template_blend_ik"
    bl_label = "Open Polaris Blend (with IK)"
    bl_description = "Open the bundled Polaris IK template .blend file"

    def execute(self, context):
        return _open_template_copy(self, "polaris_template_IK.blend")

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

_ASSET_OBJECT_NAMES    = {"SINGLE-P1-ARMATURE",    "SINGLE-P1-MESH",    "Single_P1_Plane"}
_ASSET_OBJECT_NAMES_IK = {"SINGLE-P1-ARMATURE-IK", "SINGLE-P1-MESH-IK", "Single_P1_Plane-IK"}

def _asset_path():
    return os.path.join(os.path.dirname(__file__), "assets", "polaris_base.blend")

def _do_download(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(dest, "wb") as f:
            while True:
                chunk = resp.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        _download_state["done"] = True
    except Exception as e:
        _download_state["error"] = str(e)
        if os.path.exists(dest):
            os.remove(dest)
    finally:
        _download_state["running"] = False

class POLARIS_OT_download_rig(Operator):
    bl_idname  = "polaris.download_rig"
    bl_label   = "Download Requirements"
    bl_description = "Download Requirements"

    _timer = None

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        if not _download_state["running"]:
            context.window_manager.event_timer_remove(self._timer)
            if _download_state["error"]:
                self.report({'ERROR'}, f"Download failed: {_download_state['error']}")
                return {'CANCELLED'}
            self.report({'INFO'}, "polaris_base.blend downloaded successfully.")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        if _download_state["running"]:
            self.report({'WARNING'}, "Download already in progress.")
            return {'CANCELLED'}

        os.makedirs(os.path.dirname(_asset_path()), exist_ok=True)
        _download_state["running"] = True
        _download_state["done"]    = False
        _download_state["error"]   = None

        threading.Thread(
            target=_do_download,
            args=(_RIG_DOWNLOAD_URL, _asset_path()),
            daemon=True,
        ).start()

        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class POLARIS_OT_append_assets(Operator):
    bl_idname = "polaris.append_assets"
    bl_label = "Create Polaris Single Rig"
    bl_description = "Append the Polaris armature and mesh into the current scene"

    def execute(self, context):
        asset_path = os.path.join(os.path.dirname(__file__), "assets", "polaris_base.blend")
        if not os.path.exists(asset_path):
            self.report({'ERROR'}, f"Asset file not found: {asset_path}")
            return {'CANCELLED'}

        n = 1
        while f"SINGLE-P{n}-ARMATURE" in bpy.data.objects:
            n += 1

        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name in _ASSET_OBJECT_NAMES]

        appended = []
        for obj in data_to.objects:
            if obj is None:
                continue
            obj.name = obj.name.replace("P1", f"P{n}")
            if obj.data:
                obj.data.name = obj.data.name.replace("P1", f"P{n}")
            context.collection.objects.link(obj)
            appended.append(obj.name)

        if appended:
            self.report({'INFO'}, f"Appended: {', '.join(appended)}")
        else:
            self.report({'WARNING'}, "No matching objects found in asset file")
        return {'FINISHED'}

class POLARIS_OT_append_assets_ik(Operator):
    bl_idname = "polaris.append_assets_ik"
    bl_label = "Create Polaris Single Rig (IK)"
    bl_description = "Append the Polaris IK armature and mesh into the current scene"

    def execute(self, context):
        asset_path = os.path.join(os.path.dirname(__file__), "assets", "polaris_base.blend")
        if not os.path.exists(asset_path):
            self.report({'ERROR'}, f"Asset file not found: {asset_path}")
            return {'CANCELLED'}

        n = 1
        while f"SINGLE-P{n}-ARMATURE-IK" in bpy.data.objects:
            n += 1

        with bpy.data.libraries.load(asset_path, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name in _ASSET_OBJECT_NAMES_IK]

        appended = []
        for obj in data_to.objects:
            if obj is None:
                continue
            obj.name = obj.name.replace("P1", f"P{n}")
            if obj.data:
                obj.data.name = obj.data.name.replace("P1", f"P{n}")
            context.collection.objects.link(obj)
            appended.append(obj.name)

        if appended:
            self.report({'INFO'}, f"Appended: {', '.join(appended)}")
        else:
            self.report({'WARNING'}, "No matching objects found in asset file")
        return {'FINISHED'}

class POLARIS_PT_sidebar(bpy.types.Panel):
    bl_label = "Polaris TK Anim"
    bl_idname = "POLARIS_PT_sidebar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Polaris"

    def draw(self, context):
        layout = self.layout
        global custom_icons
        icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0

        if _download_state["running"]:
            layout.label(text="Downloading...", icon='SORTTIME')
        elif not os.path.exists(_asset_path()):
            layout.operator(POLARIS_OT_download_rig.bl_idname, icon='IMPORT')
        else:
            layout.operator(POLARIS_OT_append_assets.bl_idname,    icon_value=icon_id)
            layout.operator(POLARIS_OT_append_assets_ik.bl_idname, icon_value=icon_id)
            layout.separator()
            layout.operator(POLARIS_OT_download_rig.bl_idname, text="Re-download Assets", icon='FILE_REFRESH')

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
        # layout.operator(ImportPolarisFacial.bl_idname, text="Facial Animation (.anmfa)")
        # layout.operator(ImportPolarisSwing.bl_idname, text="Swing Animation (.anmsw)")
        # layout.separator()
        # layout.operator(ImportPolarisCamera.bl_idname, text="Camera Animation (.anmca)")
        # layout.separator()
        # layout.operator(ImportPolarisExtra.bl_idname, text="Extra Animation (.anmex)")

class EXPORT_MT_polaris_tk(Menu):
    bl_idname = "EXPORT_MT_polaris_tk"
    bl_label = "Polaris TK Animation"
    def draw(self, context):
        layout = self.layout
        layout.operator(ExportPolarisFullbody.bl_idname, text="Fullbody Animation (.bin)")
        layout.operator(ExportPolarisHand.bl_idname, text="Hand Animation (.anmhd)")
        # layout.operator(ExportPolarisFacial.bl_idname, text="Facial Animation (.anmfa)")
        # layout.operator(ExportPolarisSwing.bl_idname, text="Swing Animation (.anmsw)")
        # layout.separator()
        # layout.operator(ExportPolarisExtra.bl_idname, text="Extra Animation (.anmex)")

def menu_func_import(self, context):
    global custom_icons
    icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0
    self.layout.menu(IMPORT_MT_polaris_tk.bl_idname, icon_value=icon_id)

def menu_func_export(self, context):
    global custom_icons
    icon_id = custom_icons["polaris_logo"].icon_id if custom_icons and "polaris_logo" in custom_icons else 0
    self.layout.menu(EXPORT_MT_polaris_tk.bl_idname, icon_value=icon_id)

classes = (
    ImportPolarisFullbody, ImportPolarisHand, ImportPolarisFacial, ImportPolarisSwing, ImportPolarisCamera, ImportPolarisExtra,
    ExportPolarisFullbody, ExportPolarisHand, ExportPolarisFacial, ExportPolarisSwing, ExportPolarisExtra,
    IMPORT_MT_polaris_tk, EXPORT_MT_polaris_tk,
    POLARIS_OT_open_template, POLARIS_OT_open_template_ik,
    POLARIS_OT_download_rig, POLARIS_OT_append_assets, POLARIS_OT_append_assets_ik, POLARIS_PT_sidebar,
)

def register():
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    p_icon = os.path.join(icons_dir, "polaris.png")
    if os.path.exists(p_icon): custom_icons.load("polaris_logo", p_icon, 'IMAGE')

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
