#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""resources."""

import os
import shutil
from .. import constants


##########################################
# resources
class Resources(object):
    """docstring for Resources."""

    def __init__(
        self,
        *,
        scene,
        assets,
        base_path,
        script_directory,
    ):
        super(Resources, self).__init__()
        self.scene = scene
        self.assets = assets
        self.base_path = base_path
        self.script_directory = script_directory

    ##########################################
    # output preparations
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

    ##########################################
    # output preparations
    def add_resource(
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

    def add_resource_icons(self):
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            [
                constants.PATH_RESOURCES,
                "play.png",
                False,
                ["default"],
                "icon-play",
            ],
            [
                constants.PATH_RESOURCES,
                "pause.png",
                False,
                ["default"],
                "icon-pause",
            ],
            [
                constants.PATH_RESOURCES,
                "play-skip-back.png",
                False,
                ["default"],
                "icon-play-skip-back",
            ],
            [
                constants.PATH_RESOURCES,
                "mute.png",
                False,
                ["default"],
                "icon-mute",
            ],
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
            self.add_resource(*resource)

    def add_resource_enviroment(self):
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
            self.add_resource(*resource)

    def add_resource_example_media(self):
        """add example media."""
        _resources = [
            # dest_path, filename, overwrite, include_set, add_asset
            [constants.PATH_MEDIA, "image1.png", False, ["default"], "image1"],
            [constants.PATH_MEDIA, "image2.png", False, ["default"], "image2"],
        ]

        for resource in _resources:
            self.add_resource(*resource)

    def add_resource_basic_html_js(self):
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
            self.add_resource(*resource)

    def handle_resources(self):
        """Add all needed resources."""
        self.add_resource_basic_html_js()
        self.add_resource_icons()
        self.add_resource_enviroment()
        self.add_resource_example_media()
