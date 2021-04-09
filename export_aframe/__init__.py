#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export scene as a-frame website."""

# import sys
import shutil
import math
from string import Template
import json
import os
import bpy

# import pprint

from .. import blender_helper as b_helper

from .. import constants

# from . import guidata
# from .material import MaterialManager


class ExportAframe(object):
    """Export Scene to A-Frame Website."""

    def __init__(
        self, *, skiphidden=True, report=None  # this forces named_properties..
    ):
        """Init."""
        super(ExportAframe, self).__init__()
        self.config = {
            "filename": None,
            "skiphidden": skiphidden,
            "report": self.print_report,
        }

        self.report = report

        print("config", self.config)

        self.assets = []
        self.entities = []
        self.lights = []
        self.showstats = ""

        self.scene = None
        self.script_file = None
        self.script_directory = None
        self.lightmap_files = None

        self.typeid_filter_list = [
            "GeoFeature",
            "PartDesign::CoordinateSystem",
        ]

        self.scalefactor = 2

    def print_report(self, mode, data, pre_line=""):
        """Multi print handling."""
        b_helper.print_multi(
            mode=mode, data=data, pre_line=pre_line, report=self.report,
        )

    def create_default_template(self):
        """Index html a-frame template."""
        if not bpy.data.texts.get("index.html"):
            tpl = bpy.data.texts.new("index.html")

            tpl.from_string(
                """<!doctype html>
    <html lang="en">
        <!--
            Generated automatically by AFRAME Exporter for Blender -
            https://silverslade.itch.io/a-frame-blender-exporter
        -->
        <head>
            <title>WebXR Application</title>
            <link rel="icon" type="image/png" href="favicon.ico"/>
            <meta name="description" content="3D Application">
            <meta charset="utf-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://aframe.io/releases/${aframe_version}/aframe.min.js"></script>
            <script src="https://cdn.jsdelivr.net/gh/donmccurdy/aframe-extras@v6.1.0/dist/aframe-extras.min.js"></script> # noqa
            <script type="text/javascript" src="js/webxr.js"></script>
            <script type="text/javascript" src="js/joystick.js"></script>
            <script type="text/javascript" src="js/camera-cube-env.js"></script>

            <link rel="stylesheet" type="text/css" href="style.css">
        </head>
        <body onload="init();">
            <a-scene ${stats} ${joystick} ${render_shadows} ${renderer}>
                <!-- Assets -->
                <a-assets>${asset}
                    <img id="sky"                 src="./resources/sky.jpg">
                    <img id="icon-play"           src="./resources/play.png">
                    <img id="icon-pause"          src="./resources/pause.png">
                    <img id="icon-play-skip-back" src="./resources/play-skip-back.png">
                    <img id="icon-mute"           src="./resources/mute.png">
                    <img id="icon-volume-low"     src="./resources/volume-low.png">
                    <img id="icon-volume-high"    src="./resources/volume-high.png">
                </a-assets>

                <!-- Entities -->
                ${entity}

                <!-- Camera -->
                <a-entity id="player"
                    position="0 -0.2 0"
                    movement-controls="speed: ${player_speed};">
                    <a-entity id="camera"
                        camera="near: 0.001"
                        position="0 ${player_height} 0"
                        look-controls="pointerLockEnabled: true">
                            <a-entity id="cursor"
                                cursor="fuse: false;"
                                animation__click="
                                    property: scale;
                                    startEvents: click;
                                    easing: easeInCubic;
                                    dur: 50;
                                    from: 	0.1 0.1 0.1;
                                    to: 1 1 1
                                "
                                position="0 0 -0.1"
                                geometry="primitive: circle; radius: 0.001;"
                                material="color: #CCC; shader: flat;"
                                ${show_raycast}>
                            </a-entity>
                    </a-entity>
                        ${vr_controllers}
                </a-entity>

                <!-- Lights -->
                <a-entity light="intensity: ${directional_intensity}; castShadow: ${cast_shadows}; shadowBias: -0.001; shadowCameraFar: 501.02; shadowCameraBottom: 12; shadowCameraFov: 101.79; shadowCameraNear: 0; shadowCameraTop: -5; shadowCameraRight: 10; shadowCameraLeft: -10; shadowRadius: 2" position="1.36586 7.17965 1"></a-entity>
                <a-entity light="type: ambient; intensity: ${ambient_intensity}"></a-entity>

                <!-- Sky -->
                ${sky}
            </a-scene>
        </body>
    </html>
    <!-- Generated automatically by AFRAME Exporter for Blender - https://silverslade.itch.io/a-frame-blender-exporter -->
    """
            )

    def create_diretories(self):
        ALL_PATHS = [
            ".",
            constants.PATH_ASSETS,
            constants.PATH_RESOURCES,
            constants.PATH_MEDIA,
            constants.PATH_ENVIRONMENT,
            constants.PATH_JAVASCRIPT,
            constants.PATH_LIGHTMAPS,
        ]
        for p in ALL_PATHS:
            dp = os.path.join(self.base_path, p)
            print("--- DEST [%s] [%s] {%s}" % (self.base_path, dp, p))
            os.makedirs(dp, exist_ok=True)

    def resouce_handling(self):
        """Check if addon or script for correct path."""
        _resources = [
            [".", "favicon.ico", True],
            [".", "style.css", True],
            [constants.PATH_RESOURCES, "sky.jpg", False],
            [constants.PATH_RESOURCES, "play.png", False],
            [constants.PATH_RESOURCES, "pause.png", False],
            [constants.PATH_RESOURCES, "play-skip-back.png", False],
            [constants.PATH_RESOURCES, "mute.png", False],
            [constants.PATH_RESOURCES, "volume-low.png", False],
            [constants.PATH_RESOURCES, "volume-high.png", False],
            [constants.PATH_MEDIA, "image1.png", False],
            [constants.PATH_MEDIA, "image2.png", False],
            [constants.PATH_JAVASCRIPT, "webxr.js", True],
            [constants.PATH_JAVASCRIPT, "joystick.js", True],
            [constants.PATH_JAVASCRIPT, "camera-cube-env.js", True],
            [constants.PATH_ENVIRONMENT, "negx.jpg", True],
            [constants.PATH_ENVIRONMENT, "negy.jpg", True],
            [constants.PATH_ENVIRONMENT, "negz.jpg", True],
            [constants.PATH_ENVIRONMENT, "posx.jpg", True],
            [constants.PATH_ENVIRONMENT, "posy.jpg", True],
            [constants.PATH_ENVIRONMENT, "posz.jpg", True],
        ]

        SRC_RES = os.path.join(self.script_directory, constants.PATH_RESOURCES)
        for dest_path, fname, overwrite in _resources:
            if overwrite:
                shutil.copyfile(
                    os.path.join(SRC_RES, fname),
                    os.path.join(self.base_path, dest_path, fname),
                )
            else:
                if not os.path.exists(os.path.join(self.base_path, dest_path, fname)):
                    shutil.copyfile(
                        os.path.join(SRC_RES, fname),
                        os.path.join(self.base_path, dest_path, fname),
                    )

    def handle_custom_propertie(
        self, *, K, obj, actualscale, actualposition, actualrotation
    ):
        # custom aframe code read from CUSTOM PROPERTIES
        reflections = ""
        animation = ""
        link = ""
        custom = ""
        toggle = ""
        video = False
        image = False
        # print( "\n", K , "-" , obj[K], "\n" )
        if K == "AFRAME_CUBEMAP" and self.scene.b_cubemap:
            if self.scene.b_camera_cube:
                reflections = (
                    ' geometry="" '
                    + 'camera-cube-env="distance: 500; resolution: 512; '
                    + 'repeat: true; interval: 400;" '
                )
            else:
                reflections = (
                    ' geometry="" cube-env-map="path: '
                    + self.scene.s_cubemap_path
                    + "; extension: "
                    + self.scene.s_cubemap_ext
                    + '; reflectivity: 0.99;" '
                )
        elif K == "AFRAME_ANIMATION":
            animation = ' animation= "' + obj[K] + '" '
        elif K == "AFRAME_HTTP_LINK":
            # link = ' link="href: '+obj[K]+'" class="clickable" '
            link = ' link-handler="target: ' + obj[K] + '" class="clickable" '
        elif K == "AFRAME_VIDEO":
            # print("--------------- pos " + actualposition)
            # print("--------------- rot " + actualrotation)
            # print("--------------- scale " + actualscale)
            # filename = os.path.join(
            #     base_path, constants.PATH_ASSETS, obj.name
            # )  # + '.glft' )
            # bpy.ops.export_scene.gltf(
            #     filepath=filename,
            #     export_format="GLTF_EMBEDDED",
            #     use_selection=True,
            # )
            # assets.append(
            #     '\n\t\t\t\t<a-asset-item id="'
            #     + obj.name
            #     + '" src="./assets/'
            #     + obj.name
            #     + ".gltf"
            #     + '"></a-asset-item>'
            # )
            self.assets.append(
                '\n\t\t\t\t<video id="video_'
                + str(self.videocount)
                + '" loop="true" autoplay="true" src="./media/'
                + obj[K]
                + '"></video>'
            )
            self.entities.append(
                '\n\t\t\t<a-video id="#v_'
                + str(self.videocount)
                + '" src="#video_'
                + str(self.videocount)
                + '" width="1" height="1" scale="'
                + actualscale
                + '" position="'
                + actualposition
                + '" rotation="'
                + actualrotation
                + '" visible="true" shadow="cast: false" '
                + animation
                + link
                + "></a-video>"
            )
            # self.entities.append(
            #     '\n\t\t\t<a-video id="#v_'
            #     + str(self.videocount)
            #     + '" src="#video_'
            #     + str(self.videocount)
            #     + '" width="'
            #     + str(bpy.data.objects[obj.name].scale.x)
            #     + '" height="'
            #     + str(bpy.data.objects[obj.name].scale.y)
            #     + '" scale="1 1 1" position="'
            #     + actualposition
            #     + '" rotation="'
            #     + actualrotation
            #     + '" visible="true" shadow="cast: false" '
            #     + animation
            #     + link
            #     + "></a-video>"
            # )
            # self.entities.append(
            #     '\n\t\t\t<a-entity id="#'
            #     + obj.name
            #     + '" gltf-model="#'
            #     + obj.name
            #     + '" material="src: #video_'
            #     + str(self.videocount)
            #     + '" scale="'
            #     + actualscale
            #     + '" rotation="'
            #     + actualrotation
            #     + '" position="'
            #     + actualposition
            #     + '"></a-entity>'
            # )
            video = True
            self.videocount = self.videocount + 1
        elif K == "AFRAME_IMAGES":
            # print(".....images")
            image = True
            self.imagecount = self.imagecount + 1
            # load K
            # json_images = '{"1": "image1.jpg", "2": "image2.jpg"}'
            json_images = obj[K]
            json_dictionary = json.loads(json_images)
            for key in json_dictionary:
                # print(key, ":", json_dictionary[key])
                self.assets.append(
                    '\n\t\t\t\t<img id="image_'
                    + key
                    + '" src="./media/'
                    + json_dictionary[key]
                    + '"></img>'
                )
            self.entities.append(
                '\n\t\t\t<a-image images-handler id="#i_'
                + str(self.imagecount)
                + '" src="#image_'
                + key
                + '" class="clickable" width="1" height="1" scale="'
                + actualscale
                + '" position="'
                + actualposition
                + '" rotation="'
                + actualrotation
                + '" visible="true" shadow="cast: false"></a-image>'
            )
        elif K == "AFRAME_SHOW_HIDE_OBJECT":
            toggle = ' toggle-handler="target: #' + obj[K] + ';" class="clickable" '
        elif K.startswith("AFRAME_"):
            attr = K.split("AFRAME_")[1].lower()
            custom = custom + " " + attr + '="' + str(obj[K]) + '"'
        other_attributes = reflections + animation + link + custom + toggle
        return video, image, other_attributes

    def handle_custom_properties(
        self, *, obj, actualscale, actualposition, actualrotation
    ):
        for K in obj.keys():
            if K not in "_RNA_UI":
                video, image, other_attributes = self.handle_custom_propertie(
                    K, obj, actualscale, actualposition, actualrotation
                )

        if video is False and image is False:
            baked = ""
            # check if baked texture is present on filesystem
            # images = bpy.data.images
            # for img in images:
            #    if obj.name+"_baked" in img.name and img.has_data:
            #       print("ok")
            #       baked = 'light-map-geometry="path: lightmaps/'+img.name+'"'
            print(
                "[LIGHTMAP] Searching Lightmap for object [" + obj.name + "_baked" + "]"
            )
            for file in self.lightmap_files:
                if obj.name + "_baked" in file:
                    print("[LIGHTMAP] Found lightmap: " + file)
                    baked = (
                        'light-map-geometry="path: lightmaps/'
                        + file
                        + "; intensity: "
                        + str(self.scene.f_lightMapIntensity)
                        + '"'
                    )

            filename = os.path.join(
                self.base_path, constants.PATH_ASSETS, obj.name
            )  # + '.glft' )
            bpy.ops.export_scene.gltf(
                filepath=filename, export_format="GLTF_EMBEDDED", use_selection=True,
            )
            self.assets.append(
                '\n\t\t\t\t<a-asset-item id="'
                + obj.name
                + '" src="./assets/'
                + obj.name
                + ".gltf"
                + '"></a-asset-item>'
            )
            if self.scene.b_cast_shadows:
                shadow_cast = "true"
            else:
                shadow_cast = "false"
            self.entities.append(
                '\n\t\t\t<a-entity id="#'
                + obj.name
                + '" '
                + baked
                + ' gltf-model="#'
                + obj.name
                + '" scale="1 1 1" position="'
                + actualposition
                + '" visible="true" '
                + 'shadow="cast: {}" '.format(shadow_cast)
                + other_attributes
                + "></a-entity>"
            )

    def export_object(self, obj, scalefactor):
        print("[AFRAME EXPORTER] loop object " + obj.name)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(state=True)
        bpy.context.view_layer.objects.active = obj
        # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
        location = obj.location.copy()
        rotation = obj.rotation_euler.copy()

        bpy.ops.object.location_clear()
        actualposition = (
            str(location.x) + " " + str(location.z) + " " + str(-location.y)
        )
        actualscale = (
            str(scalefactor * bpy.data.objects[obj.name].scale.x)
            + " "
            + str(scalefactor * bpy.data.objects[obj.name].scale.y)
            + " "
            + str(scalefactor * bpy.data.objects[obj.name].scale.z)
        )
        # pi = 22.0/7.0
        # actualrotation = (
        #     str(
        #         ((bpy.data.objects[obj.name].rotation_euler.x) / (2 * pi) * 360)
        #         - 90
        #     )
        #     + " "
        #     + str(
        #         ((bpy.data.objects[obj.name].rotation_euler.z) / (2 * pi) * 360)
        #         - 0
        #     )
        #     + " "
        #     + str(
        #         ((bpy.data.objects[obj.name].rotation_euler.y) / (2 * pi) * 360)
        #         + 90
        #     )
        # )
        # actualrotation = (
        #     str(bpy.data.objects[obj.name].rotation_euler.x)
        #     + " "
        #     + str(bpy.data.objects[obj.name].rotation_euler.z)
        #     + " "
        #     + str(bpy.data.objects[obj.name].rotation_euler.y)
        # )
        # actualrotation = (
        #     str(
        #         math.degrees(
        #             -89.99 + bpy.data.objects[obj.name].rotation_euler.x
        #         )
        #     )
        #     + " "
        #     + str(
        #         90 + math.degrees(bpy.data.objects[obj.name].rotation_euler.y)
        #     )
        #     + " "
        #     + str(
        #         -90 + math.degrees(bpy.data.objects[obj.name].rotation_euler.z)
        #     )
        # )
        # actualrotation = (
        #     str(math.degrees(rotation.x))
        #     + " "
        #     + str(math.degrees(rotation.z))
        #     + " "
        #     + str(math.degrees(-rotation.y))
        # )
        actualrotation = "0 " + str(math.degrees(rotation.z)) + " 0"

        # export gltf
        if obj.type == "MESH":
            # print(obj.name,"custom properties:")
            self.handle_custom_properties(
                obj, actualscale, actualposition, actualrotation
            )
        # deselect object
        obj.location = location
        obj.select_set(state=False)

    def export_objects(self):
        # Loop 3D entities
        exclusion_obj_types = ["CAMERA", "LAMP", "ARMATURE"]
        self.exported_obj = 0
        self.videocount = 0
        self.imagecount = 0

        self.lightmap_files = os.listdir(
            os.path.join(self.base_path, constants.PATH_LIGHTMAPS)
        )
        for file in self.lightmap_files:
            print("[LIGHTMAP] Found Lightmap file: " + file)

        for obj in bpy.data.objects:
            if obj.type not in exclusion_obj_types:
                if obj.visible_get():
                    self.export_object(obj)
                    self.exported_obj += 1
                else:
                    print(
                        "[AFRAME EXPORTER] loop object "
                        + obj.name
                        + " ignored: not visible"
                    )
            else:
                print(
                    "[AFRAME EXPORTER] loop object "
                    + obj.name
                    + " ignored: not exportable"
                )

        bpy.ops.object.select_all(action="DESELECT")

    def fill_template(self):
        # Templating ------------------------------
        # print(self.assets)
        all_assets = ""
        for x in self.assets:
            all_assets += x

        all_entities = ""
        for y in self.entities:
            all_entities += y

        # scene
        if self.scene.b_stats:
            showstats = "stats"
        else:
            showstats = ""

        # joystick
        if self.scene.b_joystick:
            showjoystick = "joystick"
        else:
            showjoystick = ""

        if self.scene.b_raycast:
            raycaster = (
                'raycaster = "far: '
                + str(self.scene.f_raycast_length)
                + "; interval: "
                + str(self.scene.f_raycast_interval)
                + '; objects: .clickable,.links"'
            )
        else:
            raycaster = ""

        # vr_controllers
        if self.scene.b_vr_controllers:
            showvr_controllers = (
                '<a-entity id="leftHand" oculus-touch-controls="hand: left" vive-controls="hand: left"></a-entity>\n'  # noqa
                + '\t\t\t\t\t<a-entity id="rightHand" laser-controls oculus-touch-controls="hand: right" vive-controls="hand: right" '  # noqa
                + raycaster
                + "></a-entity>"
            )
        else:
            showvr_controllers = ""

        # shadows
        if self.scene.b_cast_shadows:
            showcast_shadows = "true"
            template_render_shadows = 'shadow="type: pcfsoft; autoUpdate: true;"'
        else:
            showcast_shadows = "false"
            template_render_shadows = 'shadow="type: basic; autoUpdate: false;"'

        # Sky
        if self.scene.b_show_env_sky:
            show_env_sky = (
                '<a-sky src="#sky" material="" geometry="" rotation="0 90 0"></a-sky>'
            )
        else:
            show_env_sky = '<a-sky color="#ECECEC"></a-sky>'

        # if use bake, the light should have intensity near zero
        if self.scene.b_use_lightmapper:
            light_directional_intensity = "0"
            light_ambient_intensity = "0.1"
        else:
            light_directional_intensity = "1.0"
            light_ambient_intensity = "1.0"

        # Renderer
        showrenderer = (
            'renderer="antialias: '
            + str(self.scene.b_aa).lower()
            + "; colorManagement: "
            + str(self.scene.b_colorManagement).lower()
            + "; physicallyCorrectLights: "
            + str(self.scene.b_physicallyCorrectLights).lower()
            + ';"'
        )

        self.create_default_template()
        t = Template(bpy.data.texts["index.html"].as_string())
        s = t.substitute(
            asset=all_assets,
            entity=all_entities,
            stats=showstats,
            aframe_version=self.scene.s_aframe_version,
            joystick=showjoystick,
            vr_controllers=showvr_controllers,
            cast_shadows=showcast_shadows,
            player_height=self.scene.f_player_height,
            player_speed=self.scene.f_player_speed,
            show_raycast=raycaster,
            sky=show_env_sky,
            directional_intensity=light_directional_intensity,
            ambient_intensity=light_ambient_intensity,
            render_shadows=template_render_shadows,
            renderer=showrenderer,
        )
        return s

    # ##########################################
    # main

    def export(self, content):
        print("[AFRAME EXPORTER] Exporting project...")

        self.assets = []
        self.entities = []
        self.lights = []

        self.scene = content.scene
        self.scene.s_output = "exporting..."
        self.script_file = os.path.realpath(__file__)
        # print("self.script_file dir = "+self.script_file)
        self.script_directory = os.path.dirname(self.script_file)

        # Destination base path
        self.base_path = os.path.join(self.scene.export_path, self.scene.s_project_name)

        if __name__ == "__main__":
            # print("inside blend file")
            # print(os.path.dirname(self.script_directory))
            self.script_directory = os.path.dirname(self.script_directory)

        print("[AFRAME EXPORTER] Target Dir = " + self.script_directory)

        self.create_diretories()

        self.resouce_handling()

        self.export_objects()

        html_site_content = self.fill_template()

        # print(s)

        # Saving the main INDEX FILE
        with open(os.path.join(self.base_path, constants.PATH_INDEX), "w") as file:
            file.write(html_site_content)

        self.scene.s_output = str(self.exported_obj) + " meshes exported"
        # self.report({'INFO'}, str(exported_obj)+" meshes exported")
        return {"FINISHED"}
