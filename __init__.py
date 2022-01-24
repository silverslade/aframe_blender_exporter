"""
AFRAME Exporter for Blender
Copyright (c) 2021 Alessandro Schillaci

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.


In collaboration with Andrea Rotondo, VR Expert since 1998
http://virtual-art.it - rotondo.andrea@gmail.com
https://www.facebook.com/wox76
https://www.facebook.com/groups/134106979989778/


USAGE:
    - create new Blender project
    - install this addon get it here https://silverslade.itch.io/a-frame-blender-exporter
    - open the addon and set your configuration
    - add a CUSTOM PROPERTY (if needed)
    - click on "Export A-Frame Project" button
    - your project will be saved in the export directory
    - launch "Start Serving" + "Open Preview" (to open a local browser)
    - You can use others web server: eg. live-server" (install it with "npm install -g live-server") or "python -m SimpleHTTPServer"

AVAILABLE CUSTOM_PROPERTIES:
    - AFRAME_CUBEMAP: if present, set reflections on to the mesh object (metal -> 1, rough -> 0)
    - AFRAME_ANIMATION:  aframe animation tag. Samples:
        - property: rotation; to: 0 360 0; loop: true; dur: 10000;
        - property: position; to: 1 8 -10; dur: 2000; easing: linear; loop: true;
    - AFRAME_HTTP_LINK: html link when click on object
    - AFRAME_VIDEO: target=mp4 video to show
    - AFRAME_IMAGES: click to swap images e.g: {"1": "image1.jpg", "2": "image2.jpg"}
    - AFRAME_SHOW_HIDE_OBJECT: click to show or hide another 3d object

THIRD PARTY SOFTWARE:
    This Addon Uses the following 3rdParty software (or their integration/modification):
    - Aframe Joystick - https://github.com/mrturck/aframe-joystick
    - Aframe Components - https://github.com/colinfizgig/aframe_Components
    - Icons - https://ionicons.com/
"""


import os
import bpy
import shutil
import http.server
import urllib.request
import socketserver
import threading

from . import constants
from . import export_aframe

bl_info = {
    "name": "Import-Export: a-frame webvr exporter",
    "author": "Alessandro Schillaci",
    "description": "Blender Exporter to AFrame WebVR application",
    "blender": (2, 83, 0),
    "version": (0, 0, 10),
    "location": "View3D",
    "warning": "",
    "category": "3D View",
}

script_version = "v" + ".".join([str(x) for x in bl_info["version"]])


# Need to subclass SimpleHTTPRequestHandler so we can serve cache-busting headers
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_my_headers()
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")


class Server(threading.Thread):
    instance = None
    folder = ""
    should_stop = False

    def set_folder(self, folder):
        self.folder = folder

    def run(self):
        Handler = MyHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", constants.PORT), Handler) as httpd:
            os.chdir(self.folder)
            while True:
                if self.should_stop:
                    httpd.server_close()
                    break
                httpd.handle_request()

    def stop(self):
        self.should_stop = True
        # Consume the last handle_request call that's still pending
        with urllib.request.urlopen(f"http://localhost:{constants.PORT}/") as response:
            html = response.read()


class AframeExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "AFRAME_EXPORT_PT_Panel"
    bl_label = "Aframe Exporter ({})".format(script_version)
    bl_category = "Aframe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, content):
        scene = content.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        # col = layout.column(align=False)
        # col = layout.column(align=True)
        # row = col.row()
        # col.label(text="Exporter Settings", icon='NONE')
        row = layout.row(align=True)
        row.prop(
            scene,
            "b_settings",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_settings") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="A-Frame", icon="NONE")
        if scene.b_settings:
            row = layout.row(align=True)
            box = row.box()
            # box.alignment = 'EXPAND'
            box.prop(scene, "s_aframe_version")
            box.prop(scene, "b_stats")
            box.prop(scene, "b_joystick")
            box.prop(scene, "b_vr_controllers")
            # col.prop(scene, "b_hands")
            box.prop(scene, "b_cubemap")
            box.prop(scene, "b_camera_cube")
            box.prop(scene, "b_show_env_sky")
            box.prop(scene, "b_cubemap_background")
            box.prop(scene, "s_cubemap_path")
            box.prop(scene, "s_cubemap_ext")
            # col.prop(scene, "b_blender_lights")
            box.prop(scene, "b_cast_shadows")
            box.prop(scene, "b_use_default_lights")
            box.separator()
        row = layout.row(align=True)
        row.prop(
            scene,
            "b_renderer",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_renderer") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Renderer", icon="NONE")
        if scene.b_renderer:
            row = layout.row(align=True)
            box = row.box()
            box.prop(scene, "b_aa")
            box.prop(scene, "b_colorManagement")
            box.prop(scene, "b_physicallyCorrectLights")
            box.prop(scene, "b_maxCanvasWidth")
            box.prop(scene, "b_maxCanvasHeight")
            box.separator()
        row = layout.row(align=True)
        row.prop(
            scene,
            "b_player",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_player") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Player", icon="NONE")
        if scene.b_player:
            row = layout.row(align=True)
            box = row.box()
            box.prop(scene, "b_raycast")
            box.prop(scene, "f_raycast_length")
            box.prop(scene, "f_raycast_interval")
            box.prop(scene, "f_player_height")
            box.prop(scene, "f_player_speed")
            box.separator()
        row = layout.row(align=True)
        row.prop(
            scene,
            "b_interactive",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_interactive") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Interactive / Action", icon="NONE")
        if scene.b_interactive:
            row = layout.row(align=True)
            box = row.box()
            box.label(text="Add interactive or action to selected", icon="NONE")
            box.operator("aframe.cubemap")
            box.operator("aframe.rotation360")
            box.operator("aframe.images")

            row = box.column_flow(columns=2, align=False)
            row.operator("aframe.show_hide_object")
            row.prop(scene, "s_showhide_object", text="")

            row = box.column_flow(columns=2, align=False)
            row.operator("aframe.toggle_object")
            row.prop(scene, "s_toggle_object", text="")

            row = box.column_flow(columns=2, align=False)
            row.operator("aframe.linkurl")
            row.prop(scene, "s_link", text="")

            row = box.column_flow(columns=2, align=False)
            row.operator("aframe.onclick")
            row.prop(scene, "s_eventhandler", text="")

            row = box.column_flow(columns=2, align=False)
            row.operator("aframe.videoplay")
            row.prop(scene, "s_video", text="")
        row = layout.row(align=True)

        row.prop(
            scene,
            "b_bake",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_bake") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Bake", icon="NONE")
        if scene.b_bake:
            row = layout.row(align=True)
            box = row.box()
            # box.separator()
            box.operator("aframe.delete_lightmap", text="0 Delete All lightmaps")
            box.operator("aframe.prepare", text="1 Prepare Selection for Lightmapper")
            box.operator("aframe.bake", text="2 Bake with Lightmapper")
            box.operator("aframe.savelm", text="3 Save Lightmaps")
            box.operator("aframe.clean", text="4 Clean Lightmaps")
            # box.separator()
        row = layout.row(align=True)

        row.prop(
            scene,
            "b_bake_lightmap",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_bake_lightmap") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Create Lightmaps", icon="NONE")
        if scene.b_bake_lightmap:
            row = layout.row(align=True)
            box = row.box()
            # box.separator()
            box.label(text="Enable github.com/Naxela/The_Lightmapper", icon="NONE")
            box.prop(scene, "b_use_lightmapper")
            box.prop(scene, "f_lightMapIntensity")
            box.operator("aframe.delete_lightmap", text="0 Delete All lightmaps")
            box.operator("aframe.prepare", text="1 Prepare Selection for Lightmapper")
            box.operator("aframe.bake", text="2 Bake with Lightmapper")
            box.operator("aframe.savelm", text="3 Save Lightmaps")
            box.operator("aframe.clean", text="4 Clean Lightmaps")
            # box.separator()
        row = layout.row(align=True)

        row.prop(
            scene,
            "b_export",
            text="",
            icon="TRIA_DOWN" if getattr(scene, "b_export") else "TRIA_RIGHT",
            icon_only=False,
            emboss=False,
        )
        row.label(text="Exporter", icon="NONE")
        if scene.b_export:
            row = layout.row(align=True)
            box = row.box()
            box.prop(scene, "s_project_name")
            box.prop(scene, "export_path")
            box.prop(scene, "b_export_single_model")
            box.prop(scene, "export_apply_modifiers")
            box.prop(scene, "s_extra_output_file")
            box.prop(scene, "s_extra_output_target")
            box.prop(scene, "e_ressource_set")
            box.operator("aframe.clear_asset_dir", text="Clear Assets Directory")

        row = layout.row(align=True)
        row = layout.row(align=True)
        row.operator("aframe.export", text="Export A-Frame Project")
        row = layout.row(align=True)
        serve_label = "Stop Serving" if Server.instance else "Start Serving"
        row.operator("aframe.serve", text=serve_label)
        row = layout.row(align=True)
        if Server.instance:
            row.operator(
                "wm.url_open", text="Open Preview"
            ).url = f"http://localhost:{constants.PORT}"
            row = layout.row(align=True)
        row.label(text=scene.s_output, icon="INFO")


class AframeClean_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clean"
    bl_label = "Clean"
    bl_description = "Clean"

    def execute(self, content):
        # TODO checkout is add-on is present
        bpy.ops.tlm.clean_lightmaps("INVOKE_DEFAULT")
        print("cleaning baked lightmaps")
        return {"FINISHED"}


class AframeBake_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.bake"
    bl_label = "Bake"
    bl_description = "Bake"

    def execute(self, content):
        # TODO checkout is add-on is present
        bpy.ops.tlm.build_lightmaps("INVOKE_DEFAULT")
        print("internal bake")
        return {"FINISHED"}


class AframeClearAsset_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clear_asset_dir"
    bl_label = "Crear Asset Directory"
    bl_description = "Crear Asset Directory"

    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join(scene.export_path, scene.s_project_name)

        # Clear existing "assests" directory
        assets_dir = os.path.join(DEST_RES, constants.PATH_ASSETS)
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)
        return {"FINISHED"}


class AframePrepare_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.prepare"
    bl_label = "Prepare for Ligthmapper"
    bl_description = "Prepare Lightmapper"

    def execute(self, content):
        # DEST_RES = os.path.join(content.scene.export_path, content.scene.s_project_name)
        bpy.context.scene.TLM_SceneProperties.tlm_mode = "GPU"
        view_layer = bpy.context.view_layer
        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action="SELECT")
        bpy.context.view_layer.objects.active = obj_active
        for obj in selection:
            obj.select_set(True)
            # some exporters only use the active object
            view_layer.objects.active = obj
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_use = True
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = "256"

        return {"FINISHED"}


class AframeClear_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.delete_lightmap"
    bl_label = "Delete generated lightmaps"
    bl_description = "Delete Lightmaps"

    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join(scene.export_path, scene.s_project_name)

        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("[CLEAR] delete image " + img.name)
                bpy.data.images.remove(img)

        # for material in bpy.data.materials:
        #    material.user_clear()
        #    bpy.data.materials.remove(material)

        for filename in os.listdir(os.path.join(DEST_RES, constants.PATH_LIGHTMAPS)):
            os.remove(os.path.join(DEST_RES, constants.PATH_LIGHTMAPS) + filename)

        # if os.path.exists(os.path.join(DEST_RES, constants.PATH_LIGHTMAPS)):
        #    shutil.rmtree(os.path.join(DEST_RES,constants.PATH_LIGHTMAPS))
        # bpy.ops.tlm.build_lightmaps()

        return {"FINISHED"}


class AframeSavelm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.savelm"
    bl_label = "Save lightmaps"
    bl_description = "Save Lightmaps"

    def execute(self, content):
        images = bpy.data.images
        scene = content.scene
        original_format = scene.render.image_settings.file_format
        settings = scene.render.image_settings
        settings.file_format = "PNG"
        DEST_RES = os.path.join(scene.export_path, scene.s_project_name)
        for img in images:
            if "_baked" in img.name and img.has_data:
                ext = ".png"
                # ext = "."+img.file_format
                # img.filepath = image_dir_path+img.name+ext
                # print( os.path.join ( DEST_RES, constants.PATH_LIGHTMAPS, img.name+ext ) )
                img.file_format = "PNG"
                img.save_render(
                    os.path.join(DEST_RES, constants.PATH_LIGHTMAPS, img.name + ext)
                )
                print("[SAVE LIGHTMAPS] Save image " + img.name)
        return {"FINISHED"}


class AframeLoadlm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.loadlm"
    bl_label = "load lightmaps"
    bl_description = "Load Lightmaps"

    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join(scene.export_path, scene.s_project_name)

        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("delete: " + img.name)
                bpy.data.images.remove(img)

        for filename in os.listdir(os.path.join(DEST_RES, constants.PATH_LIGHTMAPS)):
            bpy.data.images.load(
                os.path.join(DEST_RES, constants.PATH_LIGHTMAPS) + filename
            )
        return {"FINISHED"}


class AframeServe_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.serve"
    bl_label = "Serve Aframe Preview"
    bl_description = "Serve AFrame"

    def execute(self, content):
        if Server.instance:
            Server.instance.stop()
            Server.instance = None
            return {"FINISHED"}
        scene = content.scene
        Server.instance = Server()
        Server.instance.set_folder(
            os.path.join(scene.export_path, scene.s_project_name)
        )
        Server.instance.start()

        return {"FINISHED"}


class AframeExport_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.export"
    bl_label = "Export to Aframe Project"
    bl_description = "Export AFrame\n only possible in Object Mode"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, content):
        my_exporter = export_aframe.ExportAframe(
            scene=content.scene,
            report=self.report,
        )
        return my_exporter.export()


# ------------------------------------------- REGISTER / UNREGISTER
_props = [
    ("str", "s_aframe_version", "A-Frame version", "A-Frame version", "1.0.4"),
    ("bool", "b_stats", "Show Stats", "Enable rendering stats in game"),
    (
        "bool",
        "b_vr_controllers",
        "Enable VR Controllers (HTC,Quest)",
        "Enable HTC/Quest Controllers in game",
        True,
    ),
    (
        "bool",
        "b_hands",
        "Use Hands Models",
        "Use hands models instead of controllers",
        True,
    ),
    ("bool", "b_joystick", "Show Joystick", "Add a joystick on screen"),
    ("bool", "b_cubemap", "Cube Env Map", "Enable Cube Map component"),
    ("str", "s_cubemap_path", "Path", "Cube Env Path", "/env/"),
    ("bool", "b_cubemap_background", "Enable Background", "Enable Cube Map Background"),
    ("str", "s_cubemap_ext", "Ext", "Image file extension", "jpg"),
    (
        "bool",
        "b_blender_lights",
        "Export Blender Lights",
        "Export Blenedr Lights or use Aframe default ones",
    ),
    ("bool", "b_cast_shadows", "Cast Shadows", "Cast and Receive Shadows"),
    (
        "bool",
        "b_use_default_lights",
        "Don't export Blender lights",
        "Use Default Lights - don't export blender lights",
    ),
    (
        "bool",
        "b_lightmaps",
        "Use Lightmaps as Occlusion (GlTF Settings)",
        "GLTF Models don't have lightmaps: "
        + "turn on this option will save lightmaps to Ambient Occlusion in the GLTF models",
    ),
    ("float", "f_player_speed", "Player Speed", "Player Speed", 0.1),
    (
        "float",
        "f_raycast_length",
        "Raycast Length",
        "Raycast lenght to interact with objects",
        10.0,
    ),
    (
        "float",
        "f_raycast_interval",
        "Raycast Interval",
        "Raycast Interval to interact with objects",
        1500.0,
    ),
    (
        "str",
        "export_path",
        "Export To",
        "Path to the folder containing the files to import",
        "C:/Temp/",
        "FILE_PATH",
    ),
    (
        "bool",
        "b_export_single_model",
        "Export to a single glTF model",
        "Export to a single glTF model",
    ),
    (
        "bool",
        "export_apply_modifiers",
        "apply modifiers",
        "apply modifieres - this way shapekeys do not work..",
    ),
    ("str", "s_project_name", "Name", "Project's name", "aframe-prj"),
    (
        "str",
        "s_extra_output_file",
        "Extra Output Template File",
        "Export aframe scene to a seccond extra File - specify file name for template here",
        "ascene.php",
    ),
    (
        "str",
        "s_extra_output_target",
        "Extra Output target",
        "Export aframe scene to a seccond extra File - specify target folder & name here. "
        "This is Relative to the base export_path.",
        "./ascene.php",
        "FILE_PATH",
    ),
    (
        "enum",
        # prop
        "e_ressource_set",
        # items,
        # [(identifier, name, description, icon, number), ...].
        [
            ("default", "default", "all ressources"),
            ("minimal", "minimal", "only the minimal needed ressources"),
            (
                "external",
                "external",
                "js & other things defined external - only copy files created or embedded",
            ),
        ],
        # name
        "resources set",
        # description=""
        "define set of resources to copy to output folder",
        # default=None,
        "default",
    ),
    ("str", "s_output", "output", "output export", "output"),
    (
        "bool",
        "b_use_lightmapper",
        "Use Lightmapper Add-on",
        "Use Lightmapper for baking",
    ),
    ("bool", "b_camera_cube", "Camera Cube Env", "Enable Camera Cube Env component"),
    ("float", "f_player_height", "Player Height", "Player Height", 1.7),
    ("bool", "b_raycast", "Enable Raycast", "Enable Raycast"),
    ("bool", "b_show_env_sky", "Show Environment Sky", "Show Environment Sky"),
    (
        "int",
        "b_skySegmentsHeight",
        "Sky geometry Segments Height",
        "geometry segments height",
        20,
        0,
        500,
        0,
        2000,
    ),
    (
        "int",
        "b_skySegmentsWidth",
        "Sky geometry Segments Width",
        "geometry segments width",
        64,
        0,
        500,
        0,
        2000,
    ),
    ("bool", "b_settings", "A-Frame settings", "b_settings"),
    ("bool", "b_player", "Player settings", "b_player"),
    ("bool", "b_interactive", "Interactive", "b_interactive"),
    ("bool", "b_export", "Exporter settings", "b_export"),
    ("bool", "b_bake", "Bake settings", "b_bake"),
    ("bool", "b_bake_lightmap", "Bake settings", "b_bake_lightmap"),
    ("float", "f_lightMapIntensity", "LightMap Intensity", "LightMap Intensity", 2.0),
    ("str", "s_link", "Link Url", "Link Url", "https://www.google.it/"),
    (
        "str",
        "s_eventhandler",
        "js event handler",
        "js event handler",
        "console.log('event', event)",
    ),
    ("str", "s_video", "Video File Name", "Video File Name", "video.mp4"),
    (
        "str",
        "s_showhide_object",
        "Show Hide Object",
        "Show Hide Object: insert object id \ne.g. Cube.001",
        "Cube.001",
    ),
    (
        "str",
        "s_toggle_object",
        "Toggle Objects",
        "Insert n id objects in JSON format e.g.\n"
        + '{"1": "Cube.001", "2": "Cube.002"}, "3": "Cube.003"}',
        '{"1": "Cube.001", "2": "Cube.002"}',
    ),
    ("bool", "b_renderer", "Renderer Settings", "A-Frame Renderer Settings"),
    ("bool", "b_aa", "Antialiasing", "Antialiasing"),
    ("bool", "b_colorManagement", "Color Management", "ColorManagement"),
    (
        "bool",
        "b_physicallyCorrectLights",
        "Physically Correct Lights",
        "PhysicallyCorrectLights",
    ),
    (
        "int",
        "b_maxCanvasWidth",
        "Max Canvas Width",
        "-1 = unlimited",
        1024,
        -1,
        1920 * 16,
        -1,
        1920,
    ),
    (
        "int",
        "b_maxCanvasHeight",
        "Max Canvas Height",
        "-1 = unlimited",
        1024,
        -1,
        1920 * 16,
        -1,
        1920,
    ),
]


# CUSTOM PROPERTY OPERATORS
class ShowHideObject(bpy.types.Operator):
    bl_idname = "aframe.show_hide_object"
    bl_label = "Add Show Hide Object"
    bl_description = "Show and Hide object by clicking this entity"

    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object[
                "AFRAME_SHOW_HIDE_OBJECT"
            ] = scene.s_showhide_object
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class ToogleObjects(bpy.types.Operator):
    bl_idname = "aframe.toggle_object"
    bl_label = "Add Toggle Object"
    bl_description = "Add two toggle objects for selected object"

    def execute(self, context):
        try:
            bpy.context.active_object[
                "AFRAME_TOOGLE_OBJECT"
            ] = '{"1": "id1", "2": "id2"}'
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class Images(bpy.types.Operator):
    bl_idname = "aframe.images"
    bl_label = "Add Toggle Images"
    bl_description = "Add two toggle images for selected object"

    def execute(self, context):
        try:
            bpy.context.active_object[
                "AFRAME_IMAGES"
            ] = '{"1": "image1.png", "2": "image2.png"}'
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class Cubemap(bpy.types.Operator):
    bl_idname = "aframe.cubemap"
    bl_label = "Add Cubemap"
    bl_description = "Add a cubemap for selected object to make it transparent"

    def execute(self, context):
        try:
            bpy.context.active_object["AFRAME_CUBEMAP"] = "1"
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class Rotation360(bpy.types.Operator):
    bl_idname = "aframe.rotation360"
    bl_label = "Add Rotation on Z"
    bl_description = "Rotation Object 360 on Z axis"

    def execute(self, context):
        try:
            bpy.context.active_object[
                "AFRAME_ANIMATION"
            ] = "property: rotation; to: 0 360 0; loop: true; dur: 10000"
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class LinkUrl(bpy.types.Operator):
    bl_idname = "aframe.linkurl"
    bl_label = "Add Link Web"
    bl_description = "Insert URL WEB"

    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_HTTP_LINK"] = scene.s_link
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class Onclick(bpy.types.Operator):
    bl_idname = "aframe.onclick"
    bl_label = "Add OnClick event"
    bl_description = "Insert onclick event handling"

    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_ONCLICK"] = scene.s_eventhandler
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


class VideoPlay(bpy.types.Operator):
    bl_idname = "aframe.videoplay"
    bl_label = "Add Video"
    bl_description = "Insert Video"

    def execute(self, context):
        try:
            scene = context.scene
            bpy.context.active_object["AFRAME_VIDEO"] = scene.s_video
        except Exception as e:
            bpy.ops.wm.popuperror("INVOKE_DEFAULT", e=str(e))
        return {"FINISHED"}


def _reg_bool(scene, prop, name, descr, default=False):
    setattr(
        scene,
        prop,
        bpy.props.BoolProperty(name=name, description=descr, default=default),
    )


def _reg_str(scene, prop, name, descr, default="", subtype=""):
    if subtype:
        setattr(
            scene,
            prop,
            bpy.props.StringProperty(
                name=name, description=descr, default=default, subtype=subtype
            ),
        )
    else:
        setattr(
            scene,
            prop,
            bpy.props.StringProperty(name=name, description=descr, default=default),
        )


def _reg_enum(scene, prop, items, name, descr, default=""):
    # bpy.props.EnumProperty(
    #     items, name="", description="", default=None,
    #     options={'ANIMATABLE'}, update=None, get=None, set=None
    # )
    setattr(
        scene,
        prop,
        bpy.props.EnumProperty(
            items=items,
            name=name,
            description=descr,
            default=default,
        ),
    )


def _reg_float(scene, prop, name, descr, default=0.0):
    setattr(
        scene,
        prop,
        bpy.props.FloatProperty(name=name, description=descr, default=default),
    )


def _reg_int(
    scene, prop, name, descr, default=1, min=0, max=100, soft_min=0, soft_max=10
):
    # https://docs.blender.org/api/blender_python_api_current/bpy.props.html#bpy.props.IntProperty
    setattr(
        scene,
        prop,
        bpy.props.IntProperty(
            name=name,
            description=descr,
            default=default,
            min=min,
            max=max,
            soft_min=soft_min,
            soft_max=soft_max,
        ),
    )


def register():
    scn = bpy.types.Scene

    bpy.utils.register_class(AframeExportPanel_PT_Panel)
    bpy.utils.register_class(AframeBake_OT_Operator)
    bpy.utils.register_class(AframeClean_OT_Operator)
    bpy.utils.register_class(AframeExport_OT_Operator)
    bpy.utils.register_class(AframeServe_OT_Operator)
    bpy.utils.register_class(AframeSavelm_OT_Operator)
    bpy.utils.register_class(AframeClear_OT_Operator)
    bpy.utils.register_class(AframePrepare_OT_Operator)
    bpy.utils.register_class(AframeClearAsset_OT_Operator)
    bpy.utils.register_class(Rotation360)
    bpy.utils.register_class(LinkUrl)
    bpy.utils.register_class(Onclick)
    bpy.utils.register_class(VideoPlay)
    bpy.utils.register_class(Cubemap)
    bpy.utils.register_class(Images)
    bpy.utils.register_class(ToogleObjects)
    bpy.utils.register_class(ShowHideObject)

    for p in _props:
        if p[0] == "str":
            _reg_str(scn, *p[1:])
        if p[0] == "enum":
            _reg_enum(scn, *p[1:])
        if p[0] == "bool":
            _reg_bool(scn, *p[1:])
        if p[0] == "float":
            _reg_float(scn, *p[1:])
        if p[0] == "int":
            _reg_int(scn, *p[1:])

    # deletes intex.html template embeded file
    # for t in bpy.data.texts:
    #    if (t.name == 'index.html'):
    #        print(t.name)
    #        bpy.data.texts.remove(t)


def unregister():
    bpy.utils.unregister_class(AframeExportPanel_PT_Panel)
    bpy.utils.unregister_class(AframeBake_OT_Operator)
    bpy.utils.unregister_class(AframeClean_OT_Operator)
    bpy.utils.unregister_class(AframeExport_OT_Operator)
    bpy.utils.unregister_class(AframeServe_OT_Operator)
    bpy.utils.unregister_class(AframeSavelm_OT_Operator)
    bpy.utils.unregister_class(AframeClear_OT_Operator)
    bpy.utils.unregister_class(AframePrepare_OT_Operator)
    bpy.utils.unregister_class(AframeClearAsset_OT_Operator)
    bpy.utils.unregister_class(Rotation360)
    bpy.utils.unregister_class(LinkUrl)
    bpy.utils.unregister_class(Onclick)
    bpy.utils.unregister_class(VideoPlay)
    bpy.utils.unregister_class(Cubemap)
    bpy.utils.unregister_class(Images)
    bpy.utils.unregister_class(ToogleObjects)
    bpy.utils.unregister_class(ShowHideObject)

    # for p in _props:
    #     print(" p", p)
    #     print(" bpy.types.Scene[p[1]]", bpy.types.Scene[p[1]])
    #     del bpy.types.Scene[p[1]]

    # deletes intex.html template embeded file
    for t in bpy.data.texts:
        if t.name == "index.html":
            print(t.name)
            bpy.data.texts.remove(t)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()


def to_hex(c):
    return "#%02x%02x%02x" % (int(c.r * 255), int(c.g * 255), int(c.b * 255))
