bl_info = {
    "name": "Polaris TKAnimation",
    "author": "UMIN",
    "version": (1, 5, 0),
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
import re
import shutil
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import bpy.utils.previews
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator, Menu

custom_icons = None

_RIG_FILE_ID      = "1SHMQgMCYcJQdhoijfjaNTqneeYpijQAa"
# confirm=t skips Drive's "can't scan this file for viruses" page, which Drive serves
# instead of the file for anything it can't scan (polaris_base.blend is zstd-compressed).
_RIG_DOWNLOAD_URL = f"https://drive.usercontent.google.com/download?id={_RIG_FILE_ID}&export=download&confirm=t"
_RIG_SHARE_URL    = f"https://drive.google.com/file/d/{_RIG_FILE_ID}/view"
_RIG_MIN_SIZE     = 1 << 20   # the real file is ~39 MB; Drive's warning/error pages are a few KB
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

def _asset_ok():
    # Cheap enough for panel redraws. Older versions saved Drive's ~2 KB warning page
    # as polaris_base.blend; treat that as missing so the Download button comes back.
    try:
        return os.path.getsize(_asset_path()) >= _RIG_MIN_SIZE
    except OSError:
        return False

def _require_asset(operator):
    if _asset_ok():
        return True
    if os.path.exists(_asset_path()):
        operator.report({'ERROR'}, "polaris_base.blend is broken (not the real file). Use 'Download Requirements' again.")
    else:
        operator.report({'ERROR'}, f"Asset file not found: {_asset_path()}")
    return False

_BLEND_MAGIC_RAW  = b"BLENDER"
_BLEND_MAGIC_ZSTD = b"\x28\xb5\x2f\xfd"   # Blender 3.0+ compressed .blend
_BLEND_MAGIC_GZIP = b"\x1f\x8b"           # Blender 2.x compressed .blend

def _looks_like_blend(head):
    return head.startswith((_BLEND_MAGIC_RAW, _BLEND_MAGIC_ZSTD, _BLEND_MAGIC_GZIP))

def _check_blend_file(path):
    """Raise RuntimeError with a readable message if path is not a usable .blend."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(1 << 16)
    if not _looks_like_blend(head):
        raise RuntimeError(f"downloaded data is not a .blend file (starts with {head[:8]!r}).")
    if size < _RIG_MIN_SIZE:
        raise RuntimeError(f"downloaded file is only {size} bytes, the real file is about 39 MB.")
    if head.startswith(_BLEND_MAGIC_ZSTD):
        # Decompress the first bytes when the zstandard module is available
        # (bundled with most Blender builds); otherwise the zstd magic has to do.
        try:
            import zstandard
        except ImportError:
            return
        try:
            inner = zstandard.ZstdDecompressor().decompressobj().decompress(head)
        except zstandard.ZstdError as e:
            raise RuntimeError(f"downloaded .blend is corrupt ({e}).")
        if not inner.startswith(_BLEND_MAGIC_RAW):
            raise RuntimeError("downloaded file is zstd data but not a .blend.")

def _drive_retry_url(html):
    """Build the 'Download anyway' URL from Drive's warning page, or None."""
    m = re.search(r'<form[^>]*id="download-form"[^>]*action="([^"]+)"(.*?)</form>', html, re.S)
    if not m:
        return None
    fields = dict(re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', m.group(2)))
    if "id" not in fields:
        return None
    return m.group(1) + "?" + urllib.parse.urlencode(fields)

def _html_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    return m.group(1).strip() if m else "no title"

def _fetch_blend(url, part_path, allow_retry=True):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        first = resp.read(1 << 16)
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type or not _looks_like_blend(first):
            # Drive answered with a web page (virus-scan warning, quota exceeded, sign-in, ...).
            html = (first + resp.read(1 << 20)).decode("utf-8", "replace")
            retry = _drive_retry_url(html) if allow_retry else None
            if retry:
                resp.close()
                return _fetch_blend(retry, part_path, allow_retry=False)
            raise RuntimeError(
                f"Google Drive returned a web page instead of the file ('{_html_title(html)}'). "
                f"The link may have hit Drive's download quota or no longer be public. "
                f"Try again later, or download it from {_RIG_SHARE_URL} "
                f"and save it as {_asset_path()}")

        expected = resp.headers.get("Content-Length")
        written = 0
        with open(part_path, "wb") as f:
            chunk = first
            while chunk:
                f.write(chunk)
                written += len(chunk)
                chunk = resp.read(1 << 16)
        if expected and expected.isdigit() and written != int(expected):
            raise RuntimeError(f"download was cut off ({written} of {expected} bytes).")

def _do_download(url, dest):
    # Download into a .part file and only replace dest once the file checks out,
    # so a failed re-download keeps the existing working asset.
    part = dest + ".part"
    try:
        _fetch_blend(url, part)
        _check_blend_file(part)
        os.replace(part, dest)
        _download_state["done"] = True
    except urllib.error.HTTPError as e:
        _download_state["error"] = (f"Google Drive answered HTTP {e.code} ({e.reason}). "
                                    f"The file may have been removed or made private: {_RIG_SHARE_URL}")
    except urllib.error.URLError as e:
        _download_state["error"] = f"could not reach Google Drive ({e.reason}). Check your internet connection."
    except Exception as e:
        _download_state["error"] = str(e)
    finally:
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass
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
        asset_path = _asset_path()
        if not _require_asset(self):
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
        asset_path = _asset_path()
        if not _require_asset(self):
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
        elif not _asset_ok():
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
