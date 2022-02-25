#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""HelperTools."""

import bpy

##########################################
# statics


def format_float(x, precision=6, min=1):
    # inspired by
    # https://stackoverflow.com/a/65721367/574981
    # https://stackoverflow.com/questions/2440692/formatting-floats-without-trailing-zeros
    template_clean = "{{:.{}f}}".format(precision)
    x_clean = template_clean.format(x).rstrip("0").rstrip(".")
    template_min = "{{:.{}f}}".format(min)
    x_min = template_min.format(x)
    return max(x_clean, x_min, key=len)


def apply_parent_inverse(obj):
    # print("apply_parent_inverse", obj)
    if obj.parent:
        # based on
        # https://blender.stackexchange.com/a/28897/16634
        obj_matrix_orig = obj.matrix_world.copy()

        # Reset parent inverse matrix.
        # (relationship created when parenting)
        obj.matrix_parent_inverse.identity()

        # Re-apply the difference between parent/child
        # (this writes directly into the loc/scale/rot) via a matrix.
        obj.matrix_basis = obj.parent.matrix_world.inverted() @ obj_matrix_orig


##########################################
# class


class HelperTools(object):
    """Helper Tools."""

    def __init__(
        self,
        # *,
        # this * notation forces named_properties..
    ):
        """Init."""
        super(HelperTools, self).__init__()

        self.transform_stack = {}
        self.obj_hide_selection_stack = {}

    # transform...
    def transform_backup_and_clear(self, obj):
        # backup
        self.transform_stack[obj.name] = {
            "location": obj.location.copy(),
            # "rotation": obj.rotation_quaternion.copy(),
            "rotation": obj.rotation_euler.copy(),
            # "scale": obj.scale.copy(),
        }
        # print("  obj.location", obj.location)
        # print("  obj.rotation_quaternion", obj.rotation_quaternion)
        # clear
        obj.location.zero()
        # obj.rotation_quaternion.zero()
        obj.rotation_euler.zero()
        # obj.scale.x = 1.0
        # obj.scale.y = 1.0
        # obj.scale.z = 1.0

    def transform_backup_and_clear_recursive(self, obj):
        # print(self.line_indent, "tbac recusive", obj)
        self.transform_backup_and_clear(obj)
        if obj.parent:
            # print(self.line_indent, "tbac parents", obj.parent)
            self.transform_backup_and_clear_recursive(obj.parent)

    def transform_restore(self, obj):
        transform = self.transform_stack.pop(obj.name)
        obj.location = transform["location"]
        # obj.rotation_quaternion = transform["rotation"]
        obj.rotation_euler = transform["rotation"]
        # obj.scale = transform["scale"]

    def transform_restore_recursive(self, obj):
        self.transform_restore(obj)
        if obj.parent:
            self.transform_restore_recursive(obj.parent)

    # selection...
    def select_object(self, obj):
        self.obj_hide_selection_stack[obj.name] = obj.hide_select
        obj.hide_select = False
        obj.select_set(state=True)

    def deselect_object_restore(self, obj):
        obj.select_set(state=False)
        obj.hide_select = self.obj_hide_selection_stack.pop(obj.name)

    def select_objects_recusive(self, obj):
        self.select_object(obj)
        if obj.children:
            for child in obj.children:
                self.select_objects_recusive(child)

    def deselect_objects_recusive(self, obj):
        self.deselect_object_restore(obj)
        if obj.children:
            for child in obj.children:
                self.deselect_objects_recusive(child)

    # visibility / hidden state...
    def collection_hidden_dict_traverse(self, view_layers):
        for vl in view_layers:
            self.collection_hidden_dict[vl.name] = vl.hide_viewport
            self.collection_hidden_dict_traverse(vl.children)

    def collection_hidden_dict_update(self):
        self.collection_hidden_dict = {}
        self.collection_hidden_dict_traverse(
            bpy.context.view_layer.layer_collection.children
        )

    def get_object_visible(self, obj):
        hidden = False
        hidden = hidden or obj.hide_viewport
        hidden = hidden or obj.hide_render
        if isinstance(obj, bpy.types.Collection):
            if obj.name in self.collection_hidden_dict:
                hidden = hidden or self.collection_hidden_dict[obj.name]
        elif isinstance(obj, bpy.types.Object):
            hidden = hidden or obj.hide_get()
        return not hidden


class MagicComments(object):
    def find_and_parse(self, input_text):
        print("find_and_parse...")
        list = []
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
            list.append(magic_comment_dict)
        return list

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
        list = self.find_and_parse(input_text)
        # print("list:")
        # for mc in list:
        #     print(" - {}".format(repr(mc["raw_content"])))
        #     for item in mc["attributes"].items():
        #         print("   - {}".format(item))
        for magic_comment in list:
            input_text = self.magic_comment_handle(magic_comment, input_text)
        return input_text
