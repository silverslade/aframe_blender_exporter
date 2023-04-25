#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""MagicComments."""

import re


# class MagicComments(object):
#     @classmethod
def find_and_parse(input_text):
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


def handle__src_prepend(mc_attributes, input_text):
    print("handle__src_prepend:")
    src_prepend = mc_attributes["src_prepend"]
    print("  src_prepend = ", repr(src_prepend))
    result_text = input_text.replace('src="', 'src="{}'.format(src_prepend))
    return result_text


def handle__replace_search(mc_attributes, input_text):
    print("handle__replace_search:")
    replace_search = mc_attributes["replace_search"]
    replace_with = mc_attributes["replace_with"]
    print("  replace_search = ", repr(replace_search))
    print("  replace_with = ", repr(replace_with))

    # test text
    # input_text = """<a-asset-item id="Cube" src="./assets/Cube.gltf" ></a-asset-item>"""
    result_text = input_text.replace(replace_search, replace_with)
    print("  → replaced {} occurrences".format(input_text.count(replace_search)))
    return result_text


def handle_single_mc(magic_comment, input_text):
    result_text = input_text
    mc_attributes = magic_comment["attributes"]
    # print("mc_attributes = {}".format(repr(mc_attributes)))
    if len(mc_attributes) > 0:
        if "src_prepend" in mc_attributes:
            result_text = handle__src_prepend(mc_attributes, input_text)
        elif "replace_search" in mc_attributes:
            result_text = handle__replace_search(mc_attributes, input_text)
        else:
            print("attribute names '{}' not implemented.".format(mc_attributes))
    else:
        print("empty MAGIC-COMMENT.")
    return result_text


def run(input_text):
    list = find_and_parse(input_text)
    # print("list:")
    # for mc in list:
    #     print(" - {}".format(repr(mc["raw_content"])))
    #     for item in mc["attributes"].items():
    #         print("   - {}".format(item))
    for magic_comment in list:
        input_text = handle_single_mc(magic_comment, input_text)
    return input_text
