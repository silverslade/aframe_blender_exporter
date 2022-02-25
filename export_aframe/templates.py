#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Templates."""

import bpy


def create_default():
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


def create_default_extra(filename="ascene.php"):
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
