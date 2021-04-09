#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Random Helper Functions & Classe for Blender Python Scripting."""

# import re

try:
    import bpy
except ModuleNotFoundError as e:
    print("Blender 'bpy' not available.", e)
    bpy = None


# based on
# https://www.geeksforgeeks.org/print-colors-python-terminal/
# Python program to print
# colored text and background
class colors:
    """
    ASCII Color and Control Characters.

    reset all colors with colors.reset;
    two sub classes
        fg for foreground
        bg for background;
    use as colors.subclass.colorname:
    `colors.fg.red`
    `colors.bg.green`
    the generics
    bold, disable, underline, reverse, strike through, invisible
    work with the main class:
    `colors.bold`
    """

    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class fg:
        """Forderground Colors."""

        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class bg:
        """Background Colors."""

        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'

    @classmethod
    def get_flat_list(cls, obj_dict=None):
        """Get a flattend list of all control characters in dict."""
        result = []
        if obj_dict is None:
            obj_dict = cls.__dict__
        # print("*"*42)
        # print("obj_dict", obj_dict)
        # print("*"*42)
        for attr_name, attr_value in obj_dict.items():
            if not attr_name.startswith("__"):
                # if type(attr_value) is str:
                #     value_str = attr_value.replace("\x1b", "\\x1b")
                # else:
                #     value_str = attr_value
                # print(
                #     "'{}' '{}': {}  "
                #     "".format(
                #         attr_name,
                #         type(attr_value),
                #         value_str,
                #     ),
                #     end=""
                # )
                if type(attr_value) is str:
                    # print(" STRING ")
                    result.append(attr_value)
                elif type(attr_value) is type:
                    # print(" TYPE ")
                    result.extend(
                        cls.get_flat_list(attr_value.__dict__)
                    )
                else:
                    # print(" UNKNOWN ")
                    pass
        # print("*"*42)
        return result


def filter_ASCII_controlls(data):
    """Remove ASCII controll characters."""
    code_list = colors.get_flat_list()
    for el in code_list:
        data = data.replace(el, "")
    return data


def test_filtering():
    """Test for filter_ASCII_controlls."""
    test_string = (
        colors.fg.lightblue +
        "Hello " +
        colors.fg.green +
        "World " +
        colors.fg.orange +
        ":-)" +
        colors.reset
    )
    print("test_string", test_string)
    test_filtered = filter_ASCII_controlls(test_string)
    print("test_filtered", test_filtered)


def print_colored(mode, data, pre_line=""):
    """Print with coloring similar to blenders info area."""
    printcolor = colors.reset
    if mode == {'INFO'}:
        printcolor = colors.fg.lightblue
    elif mode == {'WARNING'}:
        printcolor = colors.fg.orange
    elif mode == {'ERROR'}:
        printcolor = colors.fg.red
    print("{}{}{}{}".format(str(pre_line), printcolor, data, colors.reset))


# https://blender.stackexchange.com/a/142317/16634
def print_blender_console(mode, data, pre_line=""):
    """Print to blenders console area."""
    if bpy:
        message_type = mode.pop()
        if message_type == 'WARNING':
            message_type = 'INFO'
        elif message_type == 'INFO':
            message_type = 'OUTPUT'
        else:
            message_type = 'INFO'
        data = filter_ASCII_controlls(str(data))
        data = filter_ASCII_controlls(str(pre_line)) + data
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'CONSOLE':
                    override = {
                        'window': window,
                        'screen': screen,
                        'area': area
                    }
                    bpy.ops.console.scrollback_append(
                        override, text=data, type=message_type)


def print_console(mode, data, pre_line=""):
    """Multi-Print to blenders console area and system console."""
    print_colored(mode, data, pre_line=pre_line)
    print_blender_console(mode, data, pre_line=pre_line)


def print_multi(*, mode, data, pre_line="", report=None):
    """Multi-Print to blenders console or info area and system console."""
    # print(
    #     "print_multi   "
    #     "mode:'{}' pre_line:'{}'  data:'{}'"
    #     "".format(mode, pre_line,  data)
    # )
    print_colored(mode, data, pre_line)
    if report:
        data = filter_ASCII_controlls(str(data))
        report(mode, data)
    else:
        print_blender_console(mode, data, pre_line)


# def print_blender_info(mode, data):
#     message_type = mode.pop()
#     if message_type is 'WARNING':
#         message_type = 'ERROR'
#     if bpy:
#         data = filter_ASCII_controlls(str(data))
#         for window in bpy.context.window_manager.windows:
#             screen = window.screen
#             for area in screen.areas:
#                 if area.type == 'CONSOLE':
#                     override = {
#                         'window': window,
#                         'screen': screen,
#                         'area': area
#                     }
#                     bpy.ops.console.scrollback_append(
#                         override, text=data, type=message_type)


def purge_block(data_blocks):
    """Remove all unused object blocks."""
    counter = 0
    for block in data_blocks:
        if block.users == 0:
            data_blocks.remove(block)
            counter += 1
    return counter


def purge_all_unused():
    """Remove all unused data blocks."""
    counter = 0
    # keep this order.
    # as the lower things are contained in the higher ones..
    counter += purge_block(bpy.data.objects)
    counter += purge_block(bpy.data.meshes)
    counter += purge_block(bpy.data.materials)
    counter += purge_block(bpy.data.textures)
    counter += purge_block(bpy.data.images)
    return counter
