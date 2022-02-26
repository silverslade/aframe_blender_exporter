#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export scene as a-frame website."""

# import sys
# import time

from string import Template
import json
import os
import bpy

# import mathutils
# from mathutils import Vector

# import pprint

from .. import blender_helper as b_helper

from .. import constants

from . import helper
from .resources import Resources
from . import templates
from . import magic_comments

# from . import guidata
# from .material import MaterialManager


##########################################
# class


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
        self.debug = False

        self.report_obj = report
        self.scene = scene

        self.assets = []
        self.entities = []
        self.lights = []
        self.showstats = ""

        self.exported_gltf_objects = []
        self.script_file = None
        self.script_directory = None
        self.lightmap_files = None

        self.typeid_filter_list = [
            "GeoFeature",
            "PartDesign::CoordinateSystem",
        ]

        self.scalefactor = 1

        self.line_indent_spacer = "    "
        self.line_indent_level = 0

        self.helper = helper.HelperTools()
        # self.float_precision_max = 6
        # self.float_precision_min = 1
        # if hasattr(scene, "b_float_precision_max"):
        #     self.float_precision_max = scene.b_float_precision_max
        # if hasattr(scene, "b_float_precision_min"):
        #     self.float_precision_min = scene.b_float_precision_min

    ##########################################
    # debug output handling
    @property
    def line_indent(self):
        return self.line_indent_spacer * self.line_indent_level

    def line_indent_reset(self):
        self.line_indent_spacer = "    "
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

    ##########################################
    # helper
    def get_object_coordinates(self, obj):
        return helper.get_object_coordinates(
            obj,
            scalefactor=self.scalefactor,
            precision=self.scene.b_float_precision_max,
            min=self.scene.b_float_precision_min,
        )

    ##########################################
    # lightmap
    def lightmap_files_prepare(self):
        self.lightmap_files = os.listdir(
            os.path.join(self.base_path, constants.PATH_LIGHTMAPS)
        )
        print(self.line_indent + "[LIGHTMAP] Found Lightmap files: ")
        self.line_indent_level_in()
        if len(self.lightmap_files) < 0:
            for file in self.lightmap_files:
                print(self.line_indent + "- '{}'".format(file))
        else:
            print(self.line_indent + "- no files found.")
        self.line_indent_level_out()

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
        entity_preline_sub = self.line_indent_spacer
        entity_lines.append("<a-entity ")
        for item in entity_attributes:
            entity_lines.append("{}{}".format(entity_preline_sub, item))
        entity_lines.append(">")
        # entity_content will be replaced in a second run - so we escape it for the first one..
        entity_lines.append("{{entity_content}}")
        entity_lines.append("</a-entity>")

        # build entity string
        entity_str = ""
        for item in entity_lines:
            entity_str += "{}{}\n".format(self.line_indent, item)

        return entity_str

    def export_selection_as_gltf(self, filename):
        print(b_helper.colors.fg.lightblue)
        bpy.ops.export_scene.gltf(
            filepath=filename,
            export_format="GLTF_EMBEDDED",
            use_selection=True,
            export_animations=True,
            export_nla_strips=True,
            export_force_sampling=True,
            export_frame_range=False,
            # export_apply=True,
            export_apply=self.scene.export_apply_modifiers,
            # export_lights=True
        )
        print(b_helper.colors.reset, end="")

    def get_or_export_obj(self, obj, mesh_name=None):
        filename = None
        gltf_name = obj.name
        if mesh_name:
            gltf_name = mesh_name
        # check if we have exported this already...
        # print("  self.exported_gltf_objects", self.exported_gltf_objects)
        print(self.line_indent + "* gltf_name", gltf_name)
        if gltf_name not in self.exported_gltf_objects:
            # export as gltf
            # print("obj", obj)
            filename = os.path.join(
                self.base_path, constants.PATH_ASSETS, gltf_name
            )  # + '.glft' )
            print("{}* filename {}.gltf".format(self.line_indent, filename))

            # clear location and position so the model is exported at the world-origin.
            # handle obj and parent objects recusive
            self.helper.transform_backup_and_clear_recursive(obj)

            self.export_selection_as_gltf(filename)

            # restore all transforms...
            self.helper.transform_restore_recursive(obj)

            self.exported_gltf_objects.append(gltf_name)

            # single line format
            self.assets.append(
                "            <a-asset-item "
                'id="{gltf_name}" '
                'src="./assets/{gltf_name}.gltf" '
                "></a-asset-item>"
                "".format(gltf_name=gltf_name)
            )
            # multiline format
            # self.assets.append(
            #     "                <a-asset-item \n"
            #     '                    id="{obj_name}"\n'
            #     '                    src="./assets/{obj_name}.gltf"\n'
            #     "                ></a-asset-item>\n"
            #     "".format(obj_name=obj.name)
            # )
        return gltf_name

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

    def handle_custom_propertie(self, *, prop, obj):
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
        obj_lightmap = "{obj_name}_baked".format(obj_name=obj.name)
        print(
            "{line_indent}* searching Lightmap '{obj_lightmap}'".format(
                line_indent=self.line_indent,
                obj_lightmap=obj_lightmap,
            )
        )
        self.line_indent_level_in()
        for file in self.lightmap_files:
            if obj_lightmap in file:
                print(
                    "{line_indent}- found lightmap: '{file}'".format(
                        line_indent=self.line_indent,
                        file=file,
                    )
                )
                entity_attributes.append(
                    'light-map-geometry="path: lightmaps/{}; intensity:{};"'.format(
                        file,
                        self.scene.f_lightMapIntensity,
                    )
                )
        self.line_indent_level_out()

    def export_object(self, *, obj, entity_attributes, mesh_name=None):
        # print(self.line_indent + "* export_object", obj.name)
        # prepare export
        gltf_name = ""
        if not any(item.startswith(("image", "video")) for item in entity_attributes):
            self.handle_lightmap_things(obj=obj, entity_attributes=entity_attributes)
            #####################
            # handle gltf export
            gltf_name = self.get_or_export_obj(obj, mesh_name)
            entity_attributes.append(
                'gltf-model="#{gltf_name}"'.format(gltf_name=gltf_name)
            )
        return gltf_name

    def export_type_MESH(self, obj, entity_attributes, transforms, lines):
        entity_content = ""
        if not self.print_only:
            # print(self.line_indent + "entity_attributes:", entity_attributes)
            gltf_name = self.export_object(
                obj=obj,
                entity_attributes=entity_attributes,
                mesh_name=obj.data.name,
            )
            # print(self.line_indent + "entity_attributes:", entity_attributes)
        lines.append(self.line_indent + "MESH  gltf_name:'{}'".format(gltf_name))
        return entity_content

    def export_type_ARMATURE(self, obj, entity_attributes, transforms, lines):
        lines.append(self.line_indent + "ARMATURE")
        entity_content = ""
        follow_constraints = None
        follow_constraints_enabled_backup = None
        if obj.constraints:
            # constraints = iter(obj.constraints)
            # while (constraint := next(constraints, None)) is not None:
            for constraint in obj.constraints:
                if constraint.type == "FOLLOW_PATH":
                    follow_constraints = constraint
        if follow_constraints:
            # reset transforms -
            # the FOLLOW_PATH constraints means some tweaks here...
            # or at least we hope that the path was baked to an action..
            # transforms["location"] = "0 0 0"
            # transforms["rotation"] = "0 0 0"
            # transforms["scale"] = "1 1 1"
            # get target transforms
            follow_path_transforms = self.get_object_coordinates(
                follow_constraints.target
            )
            # use this - this way all
            transforms["location"] = follow_path_transforms["location"]
            transforms["rotation"] = follow_path_transforms["rotation"]
            transforms["scale"] = follow_path_transforms["scale"]

            # disable influcense
            follow_constraints_enabled_backup = follow_constraints.enabled
            follow_constraints.enabled = False

            # clear transforms - maybe they are alterd by the animation system...
            obj.location.zero()
            obj.rotation_euler.zero()

        # gltf_name = self.export_object(
        #     obj=obj,
        #     entity_attributes=entity_attributes,
        #     mesh_name=obj.name,
        # )
        # if obj.animation_data:
        #     gltf_name = self.export_object(
        #         obj=obj,
        #         entity_attributes=entity_attributes,
        #         mesh_name=obj.name,
        #     )
        if obj.children:
            lines.append(self.line_indent + "process ARMATURE childs..")
            # print(self.line_indent + " PING")
            self.line_indent_level_in()
            self.helper.select_objects_recusive(obj)
            gltf_name = self.export_object(
                obj=obj,
                entity_attributes=entity_attributes,
                mesh_name=obj.name,
            )
            self.helper.deselect_objects_recusive(obj)
            lines.append(self.line_indent + "gltf: '{}'".format(gltf_name))
            # entity_content_temp, lines_temp = self.traverse_objects(
            #     obj.children,
            #     allow_childs=True,
            # )
            # lines.extend(lines_temp)
            # entity_content += entity_content_temp
            self.line_indent_level_out()

        if follow_constraints:
            # restore influcense
            follow_constraints.enabled = follow_constraints_enabled_backup
        return entity_content

    def export_type_EMPTY(self, obj, entity_attributes, transforms, lines):
        lines.append(self.line_indent + "empty '{}'".format(obj.name))
        entity_content = ""
        if obj.animation_data:
            if not self.print_only:
                gltf_name = self.export_object(
                    obj=obj,
                    entity_attributes=entity_attributes,
                    mesh_name=obj.name,
                )
                lines.append(self.line_indent + "gltf: '{}'".format(gltf_name))
        # check for children
        if obj.children:
            self.line_indent_level_in()
            entity_content_temp, lines_temp = self.traverse_objects(
                obj.children,
                allow_childs=True,
            )
            lines.extend(lines_temp)
            entity_content += entity_content_temp
            self.line_indent_level_out()
        elif obj.instance_type is not None:
            lines.append(self.line_indent + "EMPTY - instance")
            if not self.print_only:
                self.export_object(obj=obj, entity_attributes=entity_attributes)
        return entity_content

    def export_type_LIGHT(self, obj, entity_attributes, transforms, lines):
        lines.append(self.line_indent + "light '{}'".format(obj.name))
        entity_content = ""

        print(
            self.line_indent + "  → ",
            obj.name,
            obj.data.type,
            obj.data.color,
            obj.data.distance,
            obj.data.cutoff_distance,
        )
        # distance = str(obj.data.distance)
        color_hex = helper.to_hex(obj.data.color)
        print("color = " + color_hex)
        # default light type
        light_type = "directional"
        if obj.data.type == "POINT":
            light_type = "point"
        elif obj.data.type == "SUN":
            light_type = "directional"
        elif obj.data.type == "SPOT":
            light_type = "spot"
        cutoff_distance = str(obj.data.cutoff_distance)
        intensity = str(1.0)
        if self.scene.b_cast_shadows:
            cast_shadows = "true"
        else:
            cast_shadows = "false"
        entity_attributes.append(
            'light="'
            "castShadow:{cast_shadows}; "
            "color:{color}; "
            "cutoff_distance:{cutoff_distance}; "
            "light_type:{light_type}; "
            "intensity:{intensity}; "
            "shadowBias: -0.001; "
            "shadowCameraFar: 501.02; "
            "shadowCameraBottom: 12; "
            "shadowCameraFov: 101.79; "
            "shadowCameraNear: 0; "
            "shadowCameraTop: -5; "
            "shadowCameraRight: 10; "
            "shadowCameraLeft: -10; "
            "shadowRadius: 2;"
            '"'
            "".format(
                cast_shadows=cast_shadows,
                color=color_hex,
                cutoff_distance=cutoff_distance,
                light_type=light_type,
                intensity=intensity,
            )
        )

        return entity_content

    def export_entity_prepare(self, *, obj, entity_attributes, transforms):
        # print(
        #     self.line_indent + "'export_entity_prepare' - entity_attributes:",
        #     entity_attributes,
        # )

        for prop in obj.keys():
            if prop not in "_RNA_UI":
                prop_custom_attributes = []
                prop_custom_attributes = self.handle_custom_propertie(
                    prop=prop,
                    obj=obj,
                )
                entity_attributes.extend(prop_custom_attributes)
        shadow_cast = "false"
        if self.scene.b_cast_shadows:
            shadow_cast = "true"
        obj_name = obj.name
        # if we have a colleciton we need to make the name unique
        if isinstance(obj, bpy.types.Collection):
            obj_name = "collection__" + obj_name
        entity_str = self.prepare_entity_str(entity_attributes)
        # replace placeholders with values
        entity_str = entity_str.format(
            obj_name=obj_name,
            position=transforms["location"],
            rotation=transforms["rotation"],
            # scale=transforms["scale"],
            scale="1 1 1",
            # TODO: Why is there a fixed scale of 1?
            # is there any place the object scale factore is really used?
            shadow_cast=shadow_cast,
        )
        return entity_str

    def export_entity_finalise(self, *, entity_str, entity_content=""):
        entity_str = entity_str.format(
            entity_content=entity_content,
        )
        return entity_str

    ##########################################
    # traverse collection and object tree
    def traverse_object(self, obj):
        # print(self.line_indent + "* traverse_object", obj)
        lines = []

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(state=True)
        # main selection
        bpy.context.view_layer.objects.active = obj

        # prepare
        entity_attributes = []
        entity_content = ""
        transforms = self.get_object_coordinates(obj)

        if obj.type == "MESH":
            entity_content += self.export_type_MESH(
                obj, entity_attributes, transforms, lines
            )
        elif obj.type == "ARMATURE":
            entity_content += self.export_type_ARMATURE(
                obj, entity_attributes, transforms, lines
            )
        elif obj.type == "EMPTY":
            entity_content += self.export_type_EMPTY(
                obj, entity_attributes, transforms, lines
            )
        elif obj.type == "LIGHT":
            if not self.scene.b_use_default_lights:
                entity_content += self.export_type_LIGHT(
                    obj, entity_attributes, transforms, lines
                )
        else:
            msg = (
                self.line_indent
                + b_helper.colors.fg.red
                + (
                    "object '{}' of type '{}' currently not implemented. "
                    "we have only created a empty placeholder."
                    "".format(obj.name, obj.type)
                )
                + b_helper.colors.reset
            )
            print(msg)
            lines.append(msg)

        # print(
        #     self.line_indent + "* traverse_object - entity_attributes:",
        #     entity_attributes,
        # )
        entity_str = self.export_entity_prepare(
            obj=obj,
            entity_attributes=entity_attributes,
            transforms=transforms,
        )
        # all things prepared. convert to string...
        entity_str = self.export_entity_finalise(
            entity_str=entity_str,
            entity_content=entity_content,
        )
        # print(self.line_indent + "traverse_object - entity_str", entity_str)
        # deselect object
        obj.select_set(state=False)
        return entity_str, lines

    def traverse_objects(self, objects, allow_childs=False):
        entity_content = ""
        lines = []
        for obj in objects:
            msg = self.line_indent + "object '{}' ({}) ".format(obj.name, obj.type)
            if self.helper.get_object_visible(obj):
                # ignore non direct childs
                if not (obj.parent and not allow_childs):
                    msg += "export.."
                    print(msg)
                    lines.append(msg)

                    self.line_indent_level_in()
                    entity_content_temp, lines_temp = self.traverse_object(obj)
                    lines.extend(lines_temp)
                    entity_content += entity_content_temp
                    self.line_indent_level_out()

                    self.entities_created += 1
                else:
                    if self.debug:
                        msg += "ignored: has parent."
                        print(msg)
                        lines.append(msg)
            else:
                msg += "ignored: not visible"
                print(msg)
                lines.append(msg)
        # bpy.ops.object.select_all(action="DESELECT")
        return entity_content, lines

    def traverse_collection(self, collection):
        # create a entity as grouping element
        # and traverse all objects belonging to this collection

        # prepare
        lines = []
        entity_attributes = []
        entity_content = ""
        transforms = self.get_object_coordinates(collection)

        # create entity for collection
        print(self.line_indent + "create entity for collection: prepare")
        entity_str = self.export_entity_prepare(
            obj=collection,
            entity_attributes=entity_attributes,
            transforms=transforms,
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
        # print(self.line_indent + "traverse_collection entity_content", entity_content)
        # set entitty content
        entity_str = self.export_entity_finalise(
            entity_str=entity_str,
            entity_content=entity_content,
        )
        self.entities_created += 1
        return entity_str, lines

    def traverse_collections(self, collections):
        lines = []
        entity_str = ""
        for collection in collections:
            msg = self.line_indent + "collection '{}' ".format(collection.name)
            if self.helper.get_object_visible(collection):
                lines.append(msg)
                print(msg)
                entity_str_temp, lines_temp = self.traverse_collection(collection)
                entity_str += entity_str_temp
                lines.extend(lines_temp)
            else:
                msg += "ignored: not visible"
                lines.append(msg)
                print(msg)
        return entity_str, lines

    def traverse_prepare_things(self):
        # clean up / reset everything..
        self.line_indent_reset()
        self.transform_stack = {}
        self.entities_created = 0
        self.videocount = 0
        self.imagecount = 0

    def traverse_collection_and_object_tree(self, print_only=False):
        # new approach: traverse collection tree
        self.print_only = print_only
        self.traverse_prepare_things()
        self.helper.collection_hidden_dict_update()
        print("")
        print("#" * 42)
        print("")
        self.lightmap_files_prepare()
        entity_str, lines = self.traverse_collections(
            bpy.context.scene.collection.children
        )
        if not self.print_only:
            self.entities.append(entity_str)
        print("")
        print("#" * 42)
        print("")
        print("project tree: ")
        print("\n".join(lines))
        print("")
        print("#" * 42)
        print("")

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
            self.resources.add_resource(
                dest_path,
                filename,
                overwrite,
                include_in,
                add_asset,
                copy_source,
            )
        else:
            self.entities.append(
                self.line_indent
                + '<a-sky id="#{id}" color="#ECECFF"></a-sky>'.format(id=id)
            )

    def handle_default_lights(self):
        if self.scene.b_use_default_lights:
            self.entities.append(
                """
                    <a-entity
                        light="
                            type: directional;
                            intensity: ${directional_intensity};;
                            castShadow: ${cast_shadows};
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
                        position="1.4 7.2 1"
                    ></a-entity>
                    <a-entity
                        light="
                            type: ambient;
                            intensity: ${ambient_intensity}
                        "
                    ></a-entity>
                """
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
            all_assets += x + "\n"

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

        templates.create_default()
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
            templates.create_default_extra(self.scene.s_extra_output_file)
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
            s2 = magic_comments.run(s2)
        return s, s2

    # ##########################################
    # main

    def export(self):
        print("\n\n\n")
        print("[AFRAME EXPORTER] Exporting project...")

        self.assets = []
        self.entities = []
        self.exported_gltf_objects = []

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

        self.resources = Resources(
            scene=self.scene,
            assets=self.assets,
            base_path=self.base_path,
            script_directory=self.script_directory,
        )
        self.resources.create_diretories()
        self.resources.handle_resources()

        self.traverse_collection_and_object_tree()

        self.handle_sky()
        self.handle_default_lights()

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

        message = (
            "Export done.\n"
            "  entities created: {}\n"
            "  gltf exports: {} "
            "".format(
                self.entities_created,
                len(self.exported_gltf_objects),
            )
        )
        self.scene.s_output = message
        self.report({"INFO"}, message)
        return {"FINISHED"}
