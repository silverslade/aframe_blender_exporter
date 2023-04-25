#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""HelperTools."""

import bpy
import math

##########################################
# statics


def to_hex(c):
    return "#%02x%02x%02x" % (int(c.r * 255), int(c.g * 255), int(c.b * 255))


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


def get_object_coordinates(obj, *, scalefactor, precision=6, min=1):
    transforms = {
        "location": "0 0 0",
        "rotation": "0 0 0",
        "scale": "1 1 1",
    }
    if hasattr(obj, "location"):
        apply_parent_inverse(obj)

        # bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
        # bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY")
        location = obj.location.copy()
        transforms["location"] = "{x} {z} {y}".format(
            x=format_float(location.x, precision, min),
            z=format_float(location.z, precision, min),
            y=format_float(-location.y, precision, min),
        )

        transforms["scale"] = "{x} {z} {y}".format(
            x=format_float(scalefactor * obj.scale.x, precision, min),
            z=format_float(scalefactor * obj.scale.z, precision, min),
            y=format_float(scalefactor * obj.scale.y, precision, min),
        )
        # print(self.line_indent + "* scale calculation:")
        # print(self.line_indent + "  - scalefactor: {}".format(self.scalefactor))
        # print(self.line_indent + "  - scale.x: {}".format(obj.scale.x))

        # first reset rotation_mode to QUATERNION (otherwise it can have buggy side-effects)
        obj.rotation_mode = "QUATERNION"
        # force rotation_mode to YXZ to be compatible with our export
        obj.rotation_mode = "YXZ"
        rotation = obj.rotation_euler.copy()
        # https://aframe.io/docs/1.2.0/components/rotation.html#sidebar
        # pi = 22.0/7.0
        transforms["rotation"] = "{x} {z} {y}".format(
            x=format_float(math.degrees(rotation.x), precision, min),
            z=format_float(math.degrees(rotation.z), precision, min),
            y=format_float(math.degrees(-rotation.y), precision, min),
        )

    # print(self.line_indent + "* transforms[location]", transforms["location"])
    # print(self.line_indent + "* transforms[scale]", transforms["scale"])
    # print(self.line_indent + "* transforms[rotation]", transforms["rotation"])
    return transforms


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
