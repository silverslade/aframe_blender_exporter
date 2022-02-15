#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export scene as a-frame website."""

# import sys
import re
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
        self,
        *,
        scene,
        report=None,  # this * notation forces named_properties..
    ):
        """Init."""
        super(ExportAframe, self).__init__()
        # self.config = {
        #     "filename": None,
        #     "skiphidden": skiphidden,
        #     "report": self.print_report,
        # }
        # print("config", self.config)

        # skiphidden=self.option_skiphidden

        self.report_obj = report
        self.scene = scene

        self.assets = []
        self.entities = []
        self.lights = []
        self.showstats = ""

        self.exported_meshes = []
        self.script_file = None
        self.script_directory = None
        self.lightmap_files = None

        self.typeid_filter_list = [
            "GeoFeature",
            "PartDesign::CoordinateSystem",
        ]

        self.scalefactor = 2

        self.line_indent = "    "
        self.line_indent_level = 0

    @property
    def line_pre(self):
        return self.line_indent * self.line_indent_level

    def line_indent_reset(self):
        self.line_indent = "    "
        self.line_indent_level = 0

    def line_indent_level_in(self):
        self.line_indent_level += 1

    def line_indent_level_out(self):
        self.line_indent_level -= 1

    def report(self, mode, data, pre_line=""):
        """Multi print handling."""
        b_helper.print_multi(
            mode=mode,
            data=data,
            pre_line=pre_line,
            report=self.report_obj,
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
    <script src="https://cdn.jsdelivr.net/gh/donmccurdy/aframe-extras@v6.1.1/dist/aframe-extras.min.js"></script> # noqa
    <script type="text/javascript" src="js/webxr.js"></script>
    <script type="text/javascript" src="js/joystick.js"></script>
    <script type="text/javascript" src="js/camera-cube-env.js"></script>

    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body onload="init();">
<a-scene
    ${stats}
    ${joystick}
    ${render_shadows}
    ${renderer}
>


    <!-- Assets -->
    <a-assets>
${asset}
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
    <a-entity
        light="
            intensity: ${directional_intensity};
            castShadow: ${cast_shadows};
            shadowBias: -0.001;
            shadowCameraFar: 501.02;
            shadowCameraBottom: 12;
            shadowCameraFov: 101.79;
            shadowCameraNear: 0;
            shadowCameraTop: -5;
            shadowCameraRight: 10;
            shadowCameraLeft: -10;
            shadowRadius: 2
        "
        position="1.4 7.2 1"
    ></a-entity>
    <a-entity
        light="
            type: ambient;
            intensity: ${ambient_intensity}
        "
    ></a-entity>

</a-scene>
</body>
</html>
<!-- Generated automatically by AFRAME Exporter for Blender - https://silverslade.itch.io/a-frame-blender-exporter -->
    """
            )

    def create_default_extra_template(self, filename="ascene.php"):
        """extra output php a-frame template."""
        if not bpy.data.texts.get(filename):
            tpl = bpy.data.texts.new(filename)

            tpl.from_string(
                """<!-- Generated automatically by AFRAME Exporter for Blender -->
<!-- https://github.com/s-light/aframe_blender_exporter -->
<a-scene
    initScene
    ${stats}
    ${joystick}
    ${render_shadows}
    ${renderer}
>
    <!-- Assets -->
    <!-- MAGIC-COMMENT src_prepend="<?php echo get_stylesheet_directory_uri(); ?>/" -->
    <a-assets>
        ${asset}
    </a-assets>

    <!-- Entities -->
    ${entity}





    <!-- Camera -->
    <!-- https://github.com/supermedium/superframe/tree/master/components/orbit-controls -->
    <a-entity id="camera"
        camera="
            fov:  60;
            far:  520;
        "
        look-controls="enabled:false"
        orbit-controls="
            target: 0 ${player_height} 0;
            initialPosition: 0 ${player_height} 1.2;
            minPolarAngle: 40;
            maxPolarAngle: 120;
            rotateSpeed: ${player_speed};
            enableZoom: false;
            zoomSpeed: 1;
            minDistance: 0;
            maxDistance: 2.8;
            minZoom: 0;
            enablePan: false;
            autoRotate: true;
            autoRotateSpeed: 0.005;
        "
    >
        <a-entity
            id="cursor"
            cursor="
                fuse: false;
                rayOrigin: mouse;
            "
            position="0 0 -0.5"
            geometry="primitive: circle; radius: 0.0005;"
            material="color: #CCC; shader: flat;"
            raycaster="
                far: 10.0;
                interval: 300.0;
                objects: .clickable,.links;
            "
        >
        <!--
        showLine: true;
        lineColor: red;
        lineOpacity: 0.5
        ${show_raycast}
        -->
        </a-entity>
    </a-entity>
    <!--
    look-controls="pointerLockEnabled: true"
    -->

    <!-- <a-entity id="player"
        position="0 -0.2 0"
        movement-controls="speed: ${player_speed};">
        ${vr_controllers}
    </a-entity> -->






    <!-- Lights -->
    <a-entity
        id="light_ambient"
        light="
            type: ambient;
            intensity: ${ambient_intensity}
        "
    ></a-entity>
    <a-entity
        id="light_sun"
        light="
            type: directional;
            intensity: 2;
            castShadow: true;
            shadowBias: -0.0004;

            shadowMapHeight: 2048;
            shadowMapWidth: 2048;

            shadowCameraNear: 0;
            shadowCameraFar: 50;
            shadowCameraFov: 102;

            shadowCameraBottom: 12;
            shadowCameraTop: -5;
            shadowCameraRight: 10;
            shadowCameraLeft: -10;

            shadowRadius: 2
        "
        position="4 10 10"
    ></a-entity>
    <a-entity
        id="light_room_ceiling"
        light="
            type: point;
            intensity: 3;
            castShadow: true;

            shadowBias: -0.001;

            shadowMapHeight: 512;
            shadowMapWidth: 512;

            shadowCameraNear: 0;
            shadowCameraFar: 50;
            shadowCameraFov: 102;

            shadowCameraBottom: 12;
            shadowCameraTop: -5;
            shadowCameraRight: 10;
            shadowCameraLeft: -10;

            shadowRadius: 2
        "
        position="0 2.5 0"
    ></a-entity>
    <a-entity
        id="light_room_lamp"
        light="
            type: point;
            intensity: 1;
            castShadow: true;

            shadowBias: -0.001;

            shadowMapHeight: 512;
            shadowMapWidth: 512;

            shadowCameraNear: 0;
            shadowCameraFar: 50;
            shadowCameraFov: 102;

            shadowCameraBottom: 12;
            shadowCameraTop: -5;
            shadowCameraRight: 10;
            shadowCameraLeft: -10;

            shadowRadius: 2
        "
        position="2.0 0.8 -2.1"
    ></a-entity>


    <!-- THE END -->
    <noscript>
        <style media="screen">
            a-scene {
                display: block;
                position: absolute;
                height: 0%;
                width: 0%;
                top: 0;
            }
        </style>
    </noscript>
</a-scene>
    """
            )

        return filename

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

    def add_resouce(
        self,
        dest_path,
        filename,
        overwrite,
        include_in,
        add_asset=False,
        copy_source=None,
    ):
        include_set = self.scene.e_ressource_set
        if include_set in include_in:
            SRC_RES = os.path.join(self.script_directory, constants.PATH_RESOURCES)
            source_fullpath = os.path.join(SRC_RES, filename)
            if copy_source:
                source_fullpath = copy_source
            target_fullpath = os.path.join(self.base_path, dest_path, filename)

            if overwrite:
                shutil.copyfile(source_fullpath, target_fullpath)
            else:
                if not os.path.exists(target_fullpath):
                    shutil.copyfile(source_fullpath, target_fullpath)

            if add_asset:
                self.assets.append(
                    "            "
                    '<img id="{id}" src="./{path}/{filename}" crossorigin="anonymous" />'
                    "".format(id=add_asset, path=dest_path, filename=filename)
                )

    def add_resouce_icons(self):
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            [constants.PATH_RESOURCES, "play.png", False, ["default"], "icon-play"],
            [constants.PATH_RESOURCES, "pause.png", False, ["default"], "icon-pause"],
            [
                constants.PATH_RESOURCES,
                "play-skip-back.png",
                False,
                ["default"],
                "icon-play-skip-back",
            ],
            [constants.PATH_RESOURCES, "mute.png", False, ["default"], "icon-mute"],
            [
                constants.PATH_RESOURCES,
                "volume-low.png",
                False,
                ["default"],
                "icon-volume-low",
            ],
            [
                constants.PATH_RESOURCES,
                "volume-high.png",
                False,
                ["default"],
                "icon-volume-high",
            ],
        ]
        for resource in _resources:
            self.add_resouce(*resource)

    def add_resouce_enviroment(self):
        """add environment box."""
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            # [constants.PATH_ENVIRONMENT, "negx.jpg", True, ["default"], "negx"],
            # [constants.PATH_ENVIRONMENT, "negy.jpg", True, ["default"], "negy"],
            # [constants.PATH_ENVIRONMENT, "negz.jpg", True, ["default"], "negz"],
            # [constants.PATH_ENVIRONMENT, "posx.jpg", True, ["default"], "posx"],
            # [constants.PATH_ENVIRONMENT, "posy.jpg", True, ["default"], "posy"],
            # [constants.PATH_ENVIRONMENT, "posz.jpg", True, ["default"], "posz"],
            [constants.PATH_ENVIRONMENT, "negx.jpg", True, ["default"], False],
            [constants.PATH_ENVIRONMENT, "negy.jpg", True, ["default"], False],
            [constants.PATH_ENVIRONMENT, "negz.jpg", True, ["default"], False],
            [constants.PATH_ENVIRONMENT, "posx.jpg", True, ["default"], False],
            [constants.PATH_ENVIRONMENT, "posy.jpg", True, ["default"], False],
            [constants.PATH_ENVIRONMENT, "posz.jpg", True, ["default"], False],
        ]

        for resource in _resources:
            self.add_resouce(*resource)

    def add_resouce_example_media(self):
        """add example media."""
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            [constants.PATH_MEDIA, "image1.png", False, ["default"], "image1"],
            [constants.PATH_MEDIA, "image2.png", False, ["default"], "image2"],
        ]

        for resource in _resources:
            self.add_resouce(*resource)

    def add_resouce_basic_html_js(self):
        """Add all things needed for the basic html website."""
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            [".", "favicon.ico", False, ["default", "minimal"], False],
            [".", "style.css", False, ["default", "minimal"], False],
            [
                constants.PATH_JAVASCRIPT,
                "webxr.js",
                True,
                ["default", "minimal"],
                False,
            ],
            [
                constants.PATH_JAVASCRIPT,
                "joystick.js",
                True,
                ["default", "minimal"],
                False,
            ],
            [
                constants.PATH_JAVASCRIPT,
                "camera-cube-env.js",
                True,
                ["default", "minimal"],
                False,
            ],
        ]

        for resource in _resources:
            self.add_resouce(*resource)

    def resouce_handling(self):
        """Add all needed resources."""
        self.add_resouce_basic_html_js()
        self.add_resouce_icons()
        self.add_resouce_enviroment()
        self.add_resouce_example_media()

    ##########################################
    # ...
    def prepare_entity_str(self, entity_attributes):
        # print("prepare_entity_str")
        if not any(item.startswith("id") for item in entity_attributes):
            # only add if no other attribute for shadow is there..
            entity_attributes.append('id="{obj_name}"')
        entity_attributes.append('position="{position}"')
        entity_attributes.append('rotation="{rotation}"')
        entity_attributes.append('scale="{scale}"')
        if not any(item.startswith("shadow") for item in entity_attributes):
            # only add if no other attribute for shadow is there..
            entity_attributes.append('shadow="cast: {shadow_cast}"')
        entity_attributes.append('visible="true"')

        # print("entity_attributes:", "\n".join(entity_attributes))

        # prepare entity lines
        entity_lines = []
        entity_preline_sub = "    "
        entity_lines.append("<a-entity ")
        for item in entity_attributes:
            entity_lines.append("{}{}".format(entity_preline_sub, item))
        entity_lines.append(">")
        # entity_content will be replaced in a second run - so we escape it for the first one..
        entity_lines.append("{{entity_content}}")
        entity_lines.append("</a-entity>")

        # build entity string
        entity_preline_base = "            "
        entity_str = ""
        for item in entity_lines:
            entity_str += "{}{}\n".format(entity_preline_base, item)

        return entity_str

    def get_or_export_mesh(self, obj):
        filename = None
        mesh_name = obj.data.name
        # check if we have exported this mesh already...
        # print("  self.exported_meshes", self.exported_meshes)
        print("  mesh_name", mesh_name)
        if mesh_name not in self.exported_meshes:
            # export as gltf
            # print("obj", obj)
            filename = os.path.join(
                self.base_path, constants.PATH_ASSETS, mesh_name
            )  # + '.glft' )
            print("  filename", filename)
            location = obj.location.copy()
            rotation_euler = obj.rotation_euler.copy()
            # print("  obj.location", obj.location)
            # print("  obj.rotation_euler", obj.rotation_euler)
            bpy.ops.object.location_clear()
            bpy.ops.object.rotation_clear()
            # print("  obj.location", obj.location)
            # print("  obj.rotation_euler", obj.rotation_euler)

            bpy.ops.export_scene.gltf(
                filepath=filename,
                export_format="GLTF_EMBEDDED",
                use_selection=True,
                # export_apply=True,
                export_apply=self.scene.export_apply_modifiers,
            )

            obj.location = location
            obj.rotation_euler = rotation_euler
            # print("  location", location)
            # print("  rotation_euler", rotation_euler)
            # print("  obj.location", obj.location)
            # print("  obj.rotation_euler", obj.rotation_euler)

            self.exported_meshes.append(mesh_name)

            # single line format
            self.assets.append(
                "            <a-asset-item "
                'id="{mesh_name}" '
                'src="./assets/{mesh_name}.gltf" '
                "></a-asset-item>\n"
                "".format(mesh_name=mesh_name)
            )
            # multiline format
            # self.assets.append(
            #     "                <a-asset-item \n"
            #     '                    id="{obj_name}"\n'
            #     '                    src="./assets/{obj_name}.gltf"\n'
            #     "                ></a-asset-item>\n"
            #     "".format(obj_name=obj.name)
            # )
        return mesh_name

    def get_object_coordinates(self, obj):
        actualposition = "0 0 0"
        actualrotation = "0 0 0"
        actualscale = "1 1 1"
        if "rotation_mode" in obj:
            # first reset rotation_mode to QUATERNION (otherwise it can have buggy side-effects)
            obj.rotation_mode = "QUATERNION"
            # force rotation_mode to YXZ to be compatible with our export
            obj.rotation_mode = "YXZ"

            # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
            # bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
            location = obj.location.copy()
            rotation = obj.rotation_euler.copy()

            actualposition = (
                str(location.x) + " " + str(location.z) + " " + str(-location.y)
            )
            actualscale = (
                str(self.scalefactor * bpy.data.objects[obj.name].scale.x)
                + " "
                + str(self.scalefactor * bpy.data.objects[obj.name].scale.y)
                + " "
                + str(self.scalefactor * bpy.data.objects[obj.name].scale.z)
            )
            # https://aframe.io/docs/1.2.0/components/rotation.html#sidebar
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
            actualrotation = (
                str(math.degrees(rotation.x))
                + " "
                + str(math.degrees(rotation.z))
                + " "
                + str(math.degrees(-rotation.y))
            )
            # actualrotation = "0 " + str(math.degrees(rotation.z)) + " 0"

        print("  actualposition", actualposition)
        print("  actualrotation", actualrotation)
        print("  actualscale", actualscale)
        return actualposition, actualrotation, actualscale

    def handle_propertie_video(self, *, prop, obj):
        attributes = []
        video_src_id = "video_src_{}".format(self.videocount)
        video_el_id = "video_{}".format(self.videocount)
        self.assets.append(
            "\n\t\t\t\t<video "
            + 'id="{}" src="./media/{}"'.format(video_src_id, obj[prop])
            + 'loop="true" autoplay="true" '
            + "></video>"
        )
        attributes.append("video")
        attributes.append('id="#{}"'.format(video_el_id))
        attributes.append('src="#{}"'.format(video_src_id))
        attributes.append('width="1"')
        attributes.append('height="1"')
        attributes.append('shadow="cast: false"')
        # attributes.append('material="src:{}"'.format(video_src_id))
        self.videocount = self.videocount + 1
        return attributes

    def handle_propertie_image(self, *, prop, obj):
        attributes = []
        # load prop
        # json_images = '{"1": "image1.jpg", "2": "image2.jpg"}'
        json_images = obj[prop]
        json_dictionary = json.loads(json_images)
        image_src_list = []
        for key in json_dictionary:
            # print(key, ":", json_dictionary[key])
            image_src_id = "image_src_{}_{}".format(self.imagecount, key)
            self.assets.append(
                '\n\t\t\t\t<img id="{}" src="./media/{}"/>'.format(
                    image_src_id, json_dictionary[key]
                )
            )
            image_src_list.append(image_src_id)

        image_el_id = "image_{}".format(self.imagecount)
        attributes.append("image")
        attributes.append('id="#{}"'.format(image_el_id))
        attributes.append("images-handler")
        # TODO: check hwo the images for images-handler have to be added....
        for image_src_id in image_src_list:
            attributes.append('src="#{}"'.format(image_src_id))
        attributes.append('class="clickable"')
        attributes.append('width="1"')
        attributes.append('height="1"')
        attributes.append('shadow="cast: false"')
        # attributes.append('material="src:{}"'.format(video_src_id))
        self.imagecount = self.imagecount + 1
        return attributes

    def handle_custom_propertie(
        self, *, prop, obj, actualscale, actualposition, actualrotation
    ):
        # custom aframe code read from CUSTOM PROPERTIES
        custom_attributes = []
        # print( "\n", K , "-" , obj[K], "\n" )
        if prop == "AFRAME_CUBEMAP" and self.scene.b_cubemap:
            if self.scene.b_camera_cube:
                custom_attributes.append('geometry=""')
                custom_attributes.append(
                    'camera-cube-env="distance: 500; resolution: 512; repeat: true; interval: 400;"'
                )
            else:
                custom_attributes.append(
                    ' geometry="" cube-env-map="path: '
                    + self.scene.s_cubemap_path
                    + "; extension: "
                    + self.scene.s_cubemap_ext
                    + '; reflectivity: 0.99;" '
                )
        elif prop == "AFRAME_ANIMATION":
            custom_attributes.append(' animation= "' + obj[prop] + '" ')
        elif prop == "AFRAME_HTTP_LINK":
            # link = ' link="href: '+obj[K]+'"'
            custom_attributes.append('link-handler="target:{}"'.format(obj[prop]))
            custom_attributes.append('class="clickable"')
        elif prop == "AFRAME_ONCLICK":
            custom_attributes.append('onclick="{}"'.format(obj[prop]))
            custom_attributes.append('class="clickable"')
        elif prop == "AFRAME_VIDEO":
            custom_attributes.extend(self.handle_propertie_video(prop, obj))
        elif prop == "AFRAME_IMAGES":
            custom_attributes.extend(self.handle_propertie_image(prop, obj))
        elif prop == "AFRAME_SHOW_HIDE_OBJECT":
            custom_attributes.append('toggle-handler="target: #{};"'.format(obj[prop]))
            custom_attributes.append('class="clickable"')
        elif prop.startswith("AFRAME_"):
            attr = prop.split("AFRAME_")[1].lower()
            custom_attributes.append(
                '{attr}="{value}"'.format(attr=attr, value=obj[prop])
            )
        return custom_attributes

    def handle_lightmap_things(self, *, obj, entity_attributes):
        #####################
        # handle lightmap things
        # check if baked texture is present on filesystem
        # images = bpy.data.images
        # for img in images:
        #    if obj.name+"_baked" in img.name and img.has_data:
        #       print("ok")
        #       baked = 'light-map-geometry="path: lightmaps/'+img.name+'"'
        print("[LIGHTMAP] Searching Lightmap for object [" + obj.name + "_baked" + "]")
        for file in self.lightmap_files:
            if obj.name + "_baked" in file:
                print("[LIGHTMAP] Found lightmap: " + file)
                entity_attributes.append(
                    'light-map-geometry="path: lightmaps/{}; intensity:{};"'.format(
                        file, self.scene.f_lightMapIntensity
                    )
                )

    def export_object(self, *, obj, entity_attributes):
        print("export_object", obj)
        # prepare export
        mesh_name = ""
        if not any(item.startswith(("image", "video")) for item in entity_attributes):
            self.handle_lightmap_things(obj=obj, entity_attributes=entity_attributes)
            #####################
            # handle mesh
            mesh_name = self.get_or_export_mesh(obj)
            entity_attributes.append(
                'gltf-model="#{mesh_name}"\n'.format(mesh_name=mesh_name)
            )
        return entity_attributes

    def export_entity_prepare(self, *, obj, entity_attributes=[]):
        actualposition, actualrotation, actualscale = self.get_object_coordinates(obj)

        for prop in obj.keys():
            if prop not in "_RNA_UI":
                prop_custom_attributes = []
                prop_custom_attributes = self.handle_custom_propertie(
                    prop=prop,
                    obj=obj,
                    actualscale=actualscale,
                    actualposition=actualposition,
                    actualrotation=actualrotation,
                )
                entity_attributes.extend(prop_custom_attributes)
        shadow_cast = "false"
        if self.scene.b_cast_shadows:
            shadow_cast = "true"

        entity_str = self.prepare_entity_str(entity_attributes)
        # replace placeholders with values
        entity_str = entity_str.format(
            obj_name=obj.name,
            position=actualposition,
            rotation=actualrotation,
            scale="1 1 1",
            shadow_cast=shadow_cast,
        )
        return entity_str

    def export_entity_finalise(self, *, entity_str, entity_content=""):
        entity_str = entity_str.format(
            entity_content=entity_content,
        )
        return entity_str

    def export_prepare(self):
        self.exported_obj = 0
        self.videocount = 0
        self.imagecount = 0

        self.lightmap_files = os.listdir(
            os.path.join(self.base_path, constants.PATH_LIGHTMAPS)
        )
        for file in self.lightmap_files:
            print("[LIGHTMAP] Found Lightmap file: " + file)

    ##########################################
    # traverse collection and object tree
    def traverse_object(self, obj):
        print("traverse_object", obj)
        lines = []

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(state=True)
        bpy.context.view_layer.objects.active = obj

        # prepare
        entity_attributes = []
        entity_content = ""

        if (obj.type == "MESH") or (obj.type == "ARMATURE"):
            lines.append(self.line_pre + "export_object '{}'".format(obj.name))
            if not self.print_only:
                self.export_object(obj=obj, entity_attributes=entity_attributes)
        elif obj.type == "EMPTY":
            lines.append(self.line_pre + "empty '{}'".format(obj.name))
            # check for children
            if obj.children:
                self.line_indent_level_in()
                entity_content_temp, lines_temp = self.traverse_objects(obj.children)
                lines.extend(lines_temp)
                entity_content += entity_content_temp
                self.line_indent_level_out()
        else:
            msg = (
                b_helper.colors.fg.red
                + (
                    "object '{}' of type '{}' currently not implemented. "
                    "we have only created a empty placeholder."
                    "".format(obj.name, obj.type)
                )
                + b_helper.colors.reset
            )
            print(msg)
            lines.append(msg)

        print("traverse_object - about ready...")
        print("traverse_object - entity_attributes:", entity_attributes)
        # all things prepared. convert to string...
        entity_str = self.export_entity_prepare(
            obj=obj,
            entity_attributes=entity_attributes,
        )
        entity_str = self.export_entity_finalise(
            entity_str=entity_str,
            entity_content=entity_content,
        )
        print("traverse_object - entity_str", entity_str)
        # deselect object
        obj.select_set(state=False)
        return entity_str, lines

    def traverse_objects(self, objects):
        exclusion_obj_types = ["CAMERA", "LIGHT"]
        entity_content = ""
        lines = []
        for obj in objects:
            msg = self.line_pre + "object '{}' ".format(obj.name)
            # ignore non direct childs
            if not obj.parent:
                if obj.type not in exclusion_obj_types:
                    if not obj.hide_viewport and not obj.hide_render:
                        msg += "export.."
                        print(msg)
                        lines.append(msg)

                        self.line_indent_level_in()
                        entity_content_temp, lines_temp = self.traverse_object(obj)
                        lines.extend(lines_temp)
                        entity_content += entity_content_temp
                        self.line_indent_level_out()

                        self.exported_obj += 1
                    else:
                        msg += "ignored: not visible"
                        print(msg)
                        lines.append(msg)
                else:
                    msg = (
                        b_helper.colors.fg.yellow
                        + msg
                        + "ignored: not exportable / not implemented"
                        + b_helper.colors.reset
                    )
                    print(msg)
                    lines.append(msg)
            else:
                msg += "ignored: has parent."
                print(msg)
                lines.append(msg)
        bpy.ops.object.select_all(action="DESELECT")
        return entity_content, lines

    def traverse_collection(self, collection):
        # create a entity as grouping element
        # and traverse all objects belonging to this collection

        # prepare
        lines = []
        # entity_attributes = []
        entity_content = ""

        # create entity for collection
        entity_str = self.export_entity_prepare(
            obj=collection,
            # entity_attributes=entity_attributes,
        )
        # self.print_only

        # handle sub collections
        if len(collection.children) > 0:
            # recusvie traversing..
            self.line_indent_level_in()
            entity_content_temp, lines_temp = self.traverse_collections(
                collection.children
            )
            lines.extend(lines_temp)
            entity_content += entity_content_temp
            self.line_indent_level_out()

        # now add direct child objects
        self.line_indent_level_in()
        entity_content_temp, lines_temp = self.traverse_objects(collection.objects)
        lines.extend(lines_temp)
        entity_content += entity_content_temp
        self.line_indent_level_out()

        # all things prepared.
        # print("-- traverse_collection '{}' - prepare final..".format(collection.name))
        # print("traverse_collection entity_content", entity_content)
        # set entitty content
        entity_str = self.export_entity_finalise(
            entity_str=entity_str,
            entity_content=entity_content,
        )
        self.exported_obj += 1
        return entity_str, lines

    def traverse_collections(self, collections):
        lines = []
        entity_str = ""
        for collection in collections:
            msg = self.line_pre + "collection '{}' ".format(collection.name)
            if not collection.hide_viewport and not collection.hide_render:
                lines.append(msg)
                print(msg)
                entity_str, lines_temp = self.traverse_collection(collection)
                lines.extend(lines_temp)
            else:
                msg += "ignored: not visible"
                lines.append(msg)
                print(msg)
        return entity_str, lines

    def traverse_collection_and_object_tree(self, print_only=False):
        # new approach: traverse collection tree
        self.print_only = print_only
        self.line_indent_reset()
        entity_str, lines = self.traverse_collections(
            bpy.context.scene.collection.children
        )
        if not self.print_only:
            self.entities.append(entity_str)
        print("")
        print("#" * 42)
        print("")
        print("exported objects: ")
        print("\n".join(lines))
        print("")
        print("#" * 42)
        print("")

    ##########################################
    # print collection and object tree
    def print_tree_object(self, obj, line_pre=""):
        lines = []
        if (obj.type == "MESH") or (obj.type == "ARMATURE"):
            lines.append(self.line_pre + "export_object '{}'".format(obj.name))
        elif obj.type == "EMPTY":
            lines.append(self.line_pre + "empty '{}'".format(obj.name))
            if obj.children:
                self.line_indent_level_in()
                lines.extend(self.print_tree_objects(obj.children))
                self.line_indent_level_out()
        else:
            lines.append(
                line_pre
                + b_helper.colors.fg.red
                + "object '{}' of type '{}' currently not implemented. ".format(
                    obj.name, obj.type
                )
                + b_helper.colors.reset
            )
        return lines

    def print_tree_objects(self, objects):
        exclusion_obj_types = ["CAMERA", "LIGHT"]
        lines = []
        for obj in objects:
            msg = self.line_pre + "object '{}' ".format(obj.name)
            # ignore non direct childs
            if not obj.parent:
                if obj.type not in exclusion_obj_types:
                    if not obj.hide_viewport and not obj.hide_render:
                        lines.extend(self.print_tree_object(obj))
                    else:
                        lines.append(msg + "ignored: not visible")
                else:
                    lines.append(
                        b_helper.colors.fg.yellow
                        + msg
                        + "ignored: not exportable / not implemented"
                        + b_helper.colors.reset
                    )
            else:
                lines.append(msg + "ignored for now - has parent.")
        return lines

    def print_tree_collection(self, collection):
        lines = []
        # check for sub collections
        if len(collection.children) > 0:
            # recusvie traversing..
            self.line_indent_level_in()
            lines.extend(self.print_tree_collections(collection.children))
            self.line_indent_level_out()
        # handle direct objects
        self.line_indent_level_in()
        lines.extend(self.print_tree_objects(collection.objects))
        self.line_indent_level_out()
        return lines

    def print_tree_collections(self, collections):
        lines = []
        for collection in collections:
            msg = self.line_pre + "collection '{}' ".format(collection.name)
            if not collection.hide_viewport and not collection.hide_render:
                lines.append(msg)
                lines.extend(self.print_tree_collection(collection))
            else:
                lines.append(msg + "ignored: not visible")
        return lines

    def print_collection_and_object_tree(self):
        # new approach: traverse collection tree
        self.line_indent = "    "
        self.line_indent_level = 0
        lines = self.print_tree_collections(bpy.context.scene.collection.children)
        print("")
        print("#" * 42)
        print("")
        print("print_collection_and_object_tree: ")
        print("\n".join(lines))
        print("")
        print("#" * 42)
        print("")

    ##########################################
    # magic comments
    def magic_comments_find_and_parse(self, input_text):
        print("magic_comments_find_and_parse...")
        magic_comments_list = []
        # <!-- MAGIC-COMMENT src_prepend="<?php echo get_stylesheet_directory_uri(); ?>/" -->
        # <!-- MAGIC-COMMENT replace_search="src=\"./" replace_with="src=\"~assets/" -->
        # <!-- MAGIC-COMMENT test="src=\"<?php echo x ?>" -->
        regex_find_magic_comment = re.compile(r"<!--\s*MAGIC-COMMENT\s*?(.*?)\s*?-->")
        magic_comments = regex_find_magic_comment.findall(input_text)
        # print("magic_comments", magic_comments)
        for magic_comment in magic_comments:
            magic_comment = magic_comment.strip()
            # magic_comment = magic_comment.decode()
            # print(
            #     'magic_comment "{}" → r"""{}""" '.format(
            #         magic_comment, repr(magic_comment)
            #     )
            # )
            # print("magic_comment {}".format(repr(magic_comment)))
            magic_comment_dict = {
                "raw_content": magic_comment,
                "attributes": {},
            }
            # example:
            # >>> magic_comment = r"""replace_search="src=\"./" replace_with="src=\\"~assets/" """
            # >>> magic_comment
            # 'replace_search="src=\\"./" replace_with="src=\\\\"~assets/" '
            # >>> magic_comment = r"""test="src=\"<?php echo x ?>" """
            # regex_split_attributes = re.compile(r"""\s*?(\S+)="([\S<>\?]+)"\s*?""")
            # regex_split_attributes = re.compile(r"""(\S+)(?<==")(.*)(?=")""")
            # regex based on https://www.metaltoad.com/blog/regex-quoted-string-escapable-quotes
            regex_split_attributes = re.compile(
                r"""(\S+)=((?<![\\])['"])((?:.(?!(?<![\\])\2))*.?)\2"""
            )
            mc_attribute_groups = regex_split_attributes.findall(magic_comment)
            # print("mc_attribute_groups", mc_attribute_groups)
            for item_name, item_quote, item_value in mc_attribute_groups:
                # print("* item_name:'{}'  item_value:'{}'".format(item_name, item_value))
                # decode escape sequences like \" to "
                item_name = item_name.encode().decode("unicode-escape")
                # print(" → item_name", item_name)
                item_value = item_value.encode().decode("unicode-escape")
                # print(" → item_value", item_value)
                magic_comment_dict["attributes"][item_name] = item_value
            magic_comments_list.append(magic_comment_dict)
        return magic_comments_list

    def magic_comment_handle__src_prepend(self, mc_attributes, input_text):
        print("magic_comment_handle__src_prepend:")
        src_prepend = mc_attributes["src_prepend"]
        print("  src_prepend = ", repr(src_prepend))
        result_text = input_text.replace('src="', 'src="{}'.format(src_prepend))
        return result_text

    def magic_comment_handle__replace_search(self, mc_attributes, input_text):
        print("magic_comment_handle__replace_search:")
        replace_search = mc_attributes["replace_search"]
        replace_with = mc_attributes["replace_with"]
        print("  replace_search = ", repr(replace_search))
        print("  replace_with = ", repr(replace_with))

        # test text
        # input_text = """<a-asset-item id="Cube" src="./assets/Cube.gltf" ></a-asset-item>"""
        result_text = input_text.replace(replace_search, replace_with)
        print("  → replaced {} occurrences".format(input_text.count(replace_search)))
        return result_text

    def magic_comment_handle(self, magic_comment, input_text):
        result_text = input_text
        mc_attributes = magic_comment["attributes"]
        # print("mc_attributes = {}".format(repr(mc_attributes)))
        if len(mc_attributes) > 0:
            if "src_prepend" in mc_attributes:
                result_text = self.magic_comment_handle__src_prepend(
                    mc_attributes, input_text
                )
            elif "replace_search" in mc_attributes:
                result_text = self.magic_comment_handle__replace_search(
                    mc_attributes, input_text
                )
            else:
                print("attribute names '{}' not implemented.".format(mc_attributes))
        else:
            print("empty MAGIC-COMMENT.")
        return result_text

    def handle_magic_comment(self, input_text):
        magic_comments_list = self.magic_comments_find_and_parse(input_text)
        # print("magic_comments_list:")
        # for mc in magic_comments_list:
        #     print(" - {}".format(repr(mc["raw_content"])))
        #     for item in mc["attributes"].items():
        #         print("   - {}".format(item))
        for magic_comment in magic_comments_list:
            input_text = self.magic_comment_handle(magic_comment, input_text)
        return input_text

    ##########################################

    def get_shadow(self):
        showcast_shadows = "false"
        template_render_shadows = 'shadow="type: basic; autoUpdate: false;"'
        if self.scene.b_cast_shadows:
            showcast_shadows = "true"
            template_render_shadows = 'shadow="type: pcfsoft; autoUpdate: true;"'
        return showcast_shadows, template_render_shadows

    def handle_sky(self):
        id = "sky"
        if self.scene.b_show_env_sky:
            self.entities.append(
                "        "
                '<a-sky src="#{id}" material="" geometry="" rotation="0 90 0"></a-sky>'
                "".format(id=id)
            )
            filename = "sky.jpg"
            full_filepath = "."
            try:
                env_texture = bpy.data.worlds["World"].node_tree.nodes[
                    "Environment Texture"
                ]
                full_filepath = env_texture.image.filepath_from_user()
                filename = env_texture.image.name
            except Exception as e:
                self.report({"ERROR"}, e)

            # TODO: if image is packed - unpack
            dest_path = constants.PATH_ENVIRONMENT
            overwrite = False
            include_in = ["default", "minimal", "external"]
            add_asset = id
            copy_source = full_filepath
            self.add_resouce(
                dest_path,
                filename,
                overwrite,
                include_in,
                add_asset,
                copy_source,
            )
        else:
            self.entities.append(
                "        " '<a-sky id="#{id}" color="#ECECFF"></a-sky>'.format(id=id)
            )

    def get_raycaster_showvr(self):
        raycaster = ""
        if self.scene.b_raycast:
            raycaster = (
                'raycaster = "far: '
                + str(self.scene.f_raycast_length)
                + "; interval: "
                + str(self.scene.f_raycast_interval)
                + '; objects: .clickable,.links"'
            )

        showvr_controllers = ""
        # vr_controllers
        if self.scene.b_vr_controllers:
            showvr_controllers = (
                '<a-entity id="leftHand" oculus-touch-controls="hand: left" vive-controls="hand: left"></a-entity>\n'  # noqa
                + '\t\t\t\t\t<a-entity id="rightHand" laser-controls oculus-touch-controls="hand: right" vive-controls="hand: right" '  # noqa
                + raycaster
                + "></a-entity>"
            )
        return raycaster, showvr_controllers

    def get_renderer(self):
        showrenderer = (
            'renderer="\n            '
            "antialias: "
            + str(self.scene.b_aa).lower()
            + ";\n            "
            + "colorManagement: "
            + str(self.scene.b_colorManagement).lower()
            + ";\n            "
            + "physicallyCorrectLights: "
            + str(self.scene.b_physicallyCorrectLights).lower()
            + ";\n            "
            + "maxCanvasWidth: "
            + str(self.scene.b_maxCanvasWidth)
            + ";\n            "
            + "maxCanvasHeight: "
            + str(self.scene.b_maxCanvasHeight)
            + ";\n        "
            + '"'
        )
        return showrenderer

    def get_light(self):
        light_directional_intensity = "1.0"
        light_ambient_intensity = "1.0"
        if self.scene.b_use_lightmapper:
            # if use bake, the light should have intensity near zero
            light_directional_intensity = "0"
            light_ambient_intensity = "0.1"
        return light_directional_intensity, light_ambient_intensity

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
        showstats = ""
        if self.scene.b_stats:
            showstats = "stats"

        # joystick
        showjoystick = ""
        if self.scene.b_joystick:
            showjoystick = "joystick"

        raycaster, showvr_controllers = self.get_raycaster_showvr()

        showcast_shadows, template_render_shadows = self.get_shadow()

        light_directional_intensity, light_ambient_intensity = self.get_light()

        showrenderer = self.get_renderer()

        self.create_default_template()
        t = Template(bpy.data.texts["index.html"].as_string())
        s = ""
        try:
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
                directional_intensity=light_directional_intensity,
                ambient_intensity=light_ambient_intensity,
                render_shadows=template_render_shadows,
                renderer=showrenderer,
            )
        except KeyError as e:
            self.report(
                {"ERROR"},
                "Template substitute error in '{}': no value for Key {}.".format(
                    "index.html", e
                ),
            )
        s2 = None
        if self.scene.s_extra_output_file:
            self.create_default_extra_template(self.scene.s_extra_output_file)
            t2 = Template(bpy.data.texts[self.scene.s_extra_output_file].as_string())
            try:
                s2 = t2.substitute(
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
                    directional_intensity=light_directional_intensity,
                    ambient_intensity=light_ambient_intensity,
                    render_shadows=template_render_shadows,
                    renderer=showrenderer,
                )
            except KeyError as e:
                self.report(
                    {"ERROR"},
                    "Template substitute error in '{}': no value for Key {}.".format(
                        self.scene.s_extra_output_file, e
                    ),
                )
            print("search and handle MAGIC-COMMENT")
            s2 = self.handle_magic_comment(s2)
        return s, s2

    # ##########################################
    # main

    def export(self):
        print("\n\n\n")
        print("[AFRAME EXPORTER] Exporting project...")

        self.assets = []
        self.entities = []
        self.lights = []
        self.exported_meshes = []

        self.scene.s_output = "exporting..."
        self.script_file = os.path.realpath(__file__)
        # print("self.script_file dir = "+self.script_file)
        self.script_directory = os.path.dirname(self.script_file)
        self.script_directory = os.path.join(self.script_directory, "../")
        self.script_directory = os.path.normpath(self.script_directory)

        # Destination base path
        self.base_path = os.path.join(self.scene.export_path, self.scene.s_project_name)

        if __name__ == "__main__":
            print("inside blend file")
            # print(os.path.dirname(self.script_directory))
            self.script_directory = os.path.dirname(self.script_directory)

        print("[AFRAME EXPORTER] ressources path = " + self.script_directory)
        print("[AFRAME EXPORTER] target path     = " + self.base_path)

        self.create_diretories()

        self.resouce_handling()

        self.export_prepare()

        self.print_collection_and_object_tree()

        self.traverse_collection_and_object_tree()

        self.handle_sky()

        print("entities handling finished.")
        print("---")

        html_site_content, extra_output_content = self.fill_template()
        # writing the output files
        with open(os.path.join(self.base_path, constants.PATH_INDEX), "w") as file:
            file.write(html_site_content)
        if extra_output_content:
            extra_output_target_file = self.scene.s_extra_output_file
            if self.scene.s_extra_output_target:
                extra_output_target_file = self.scene.s_extra_output_target
            extra_output_full_path = os.path.join(
                self.base_path,
                extra_output_target_file,
            )
            print(
                "[AFRAME EXPORTER] extra_output target path     = "
                + extra_output_full_path
            )
            with open(extra_output_full_path, "w") as file:
                file.write(extra_output_content)

        message = str(self.exported_obj) + " objects exported"
        self.scene.s_output = message
        self.report({"INFO"}, message)
        return {"FINISHED"}
