'''
AFRAME Exporter for Blender
Copyright (c) 2020 Alessandro Schillaci

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
'''

'''
In collaboration with Andrea Rotondo, VR Expert since 1998
informations and contacs:
http://virtual-art.it - rotondo.andrea@gmail.com
https://www.facebook.com/wox76
https://www.facebook.com/groups/134106979989778/
'''

'''
USAGE:
    - create new Blender project
    - install this addon
    - add a right managed CUSTOM PROPERTY
    - open the addon and set your configuration
    - click on "Export A-Frame Project" button
    - your project will be saved in the export directory
    - launch "live-server" (install it with "npm install -g live-server") or "python -m SimpleHTTPServer"

AVAILABLE CUSTOM_PROPERTIES:
    - AFRAME_CUBEMAP: if present, set reflections on to the mesh object (metal -> 1, rough -> 0)
    - AFRAME_ANIMATION:  aframe animation tag. Samples:
        - property: rotation; to: 0 360 0; loop: true; dur: 10000;
        - property: position; to: 1 8 -10; dur: 2000; easing: linear; loop: true;
    - AFRAME_HTTP_LINK: html link when click on object       
    - AFRAME_VIDEO: target=mp4 video to show
    - AFRAME_IMAGES: click to swap images e.g: {"1": "image1.jpg", "2": "image2.jpg"}

THIRD PARTY SOFTWARE:
    This Addon Uses the following 3rdParty software (or their integration/modification):
    - Aframe Joystick - https://github.com/mrturck/aframe-joystick
    - Aframe Components - https://github.com/colinfizgig/aframe_Components
    - Icons - https://ionicons.com/
'''


bl_info = {
    "name" : "Import-Export: a-frame webvr exporter",
    "author" : "Alessandro Schillaci",
    "description" : "Blender Exporter to AFrame WebVR application",
    "blender" : (2, 83, 0),
    "version" : (0, 0, 5),
    "location" : "View3D",
    "warning" : "",
    "category" : "3D View"
}

import os
import bpy
import shutil
import math
from string import Template
import http.server
import urllib.request
import socketserver
import threading
import json

PORT = 8001

# Constants
PATH_INDEX = "index.html"
PATH_ASSETS = "assets/"
PATH_RESOURCES = "resources/"
PATH_MEDIA = "media/"
PATH_ENVIRONMENT = "env/"
PATH_LIGHTMAPS = "lightmaps/"
PATH_JAVASCRIPT = "js/"
AFRAME_ENABLED = "AFRAME_ENABLED"
AFRAME_HTTP_LINK = "AFRAME_HTTP_LINK"
AFRAME_ANIMATION = "AFRAME_ANIMATION"
AFRAME_VIDEO = "AFRAME_VIDEO"
AFRAME_IMAGES = "AFRAME_IMAGES"
AFRAME_DOWNLOAD = "AFRAME_DOWNLOAD"
AFRAME_VIDEO_AUTOPLAY = "AFRAME_VIDEO_AUTOPLAY"
AFRAME_VIDEO_STREAM = "AFRAME_VIDEO_STREAM"

assets = []
entities = []
lights = []
showstats = ""

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
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            os.chdir(self.folder)
            while True:
                if self.should_stop:
                    httpd.server_close()
                    break
                httpd.handle_request()

    def stop(self):
        self.should_stop = True
        # Consume the last handle_request call that's still pending
        with urllib.request.urlopen(f'http://localhost:{PORT}/') as response:
            html = response.read()


# Index html a-frame template
t = Template('''
<!-- Generated automatically by AFRAME Exporter for Blender - https://silverslade.itch.io/a-frame-blender-exporter -->
<html>
    <head>
        <title>WebXR Application</title>
        <link rel="icon" type="image/png" href="favicon.ico"/>
        <meta name="description" content="3D Application">
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://aframe.io/releases/${aframe_version}/aframe.min.js"></script>
        <script src="https://cdn.jsdelivr.net/gh/donmccurdy/aframe-extras@v6.1.0/dist/aframe-extras.min.js"></script>
        <script type="text/javascript" src="js/webxr.js"></script>
        <script type="text/javascript" src="js/joystick.js"></script>
        <script type="text/javascript" src="js/camera-cube-env.js"></script>
        
        <link rel="stylesheet" type="text/css" href="style.css">
    </head>
    <body onload="init();">
        <a-scene ${stats} ${joystick} ${render_shadows}>
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
                        <a-entity id="cursor" cursor="fuse: false;" animation__click="property: scale; startEvents: click; easing: easeInCubic; dur: 50; from: 	0.1 0.1 0.1; to: 1 1 1"
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
''')


class AframeExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "AFRAME_EXPORT_PT_Panel"
    bl_label = "Aframe Exporter (v 0.0.5)"
    bl_category = "Aframe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, content):
        scene = content.scene
        layout = self.layout
        col = layout.column(align=False)
        row = col.row()
        #col.label(text="Exporter Settings", icon='NONE')
        col.prop(scene, "s_aframe_version")
        col.prop(scene, "b_stats")
        col.prop(scene, "b_joystick")
        col.prop(scene, "b_vr_controllers")
        #col.prop(scene, "b_hands")

        #col.separator()
        col.prop(scene, "b_cubemap")
        if scene.b_cubemap:
            box = col.box()
            box.prop(scene, "b_camera_cube")
            box.prop(scene, "b_show_env_sky")                  
            box.prop(scene, "b_cubemap_background")
            box.prop(scene, "s_cubemap_path")
            box.prop(scene, "s_cubemap_ext")      
        #col.prop(scene, "b_blender_lights")
        col.prop(scene, "b_cast_shadows")
        col.prop(scene, "b_raycast")
        if scene.b_raycast:
            box = col.box()
            box.prop(scene, "f_raycast_length")
            box.prop(scene, "f_raycast_interval")
        #col.prop(scene, "b_lightmaps")
        col.separator()
        col.prop(scene, "f_player_height")
        col.prop(scene, "f_player_speed")
        col.separator()
        col.prop(scene, "s_project_name")
        col.prop(scene, "export_path")
        col.prop(scene, "b_use_lightmapper")
        if scene.b_use_lightmapper:
            box = col.box()
            #box.label(text="Use Lightmapper for bake lightmaps", icon='INFO')
            box.label(text="1. Select items -> click 'Prepare Selection for Lightmapper'", icon='NONE')                        
            box.label(text="2. Lightmapper Add-on -> click 'Bake Lightmaps'", icon='NONE')            
            box.label(text="3. 'Save Lightmaps' to save to 'Lightmaps' dir", icon='NONE')            
            box.label(text="4. Lightmapper Add-on ->click 'Clean Lightmaps'", icon='NONE')                        
            box.label(text="5. 'Export A-Frame Project' as usual", icon='NONE')              
            box.label(text="6. 'Clear All LIghtmaps' if you change the bake", icon='NONE')                          
            box.operator('aframe.prepare', text='Prepare Selection for Lightmapper')
            box.operator('aframe.clear', text='Clear All lightmaps')        
            box.operator('aframe.savelm', text='Save Lightmaps')
                        
        #col.separator()
        #col.label(text="Export to a-frame project", icon='NONE')
#        col.operator('aframe.loadlm', text='Load lightmaps')
        col.operator('aframe.clear_asset_dir', text='Crear Assets Directory')
        col.operator('aframe.export', text='Export A-Frame Project')
        serve_label = "Stop Serving" if Server.instance else "Start Serving"
        col.operator('aframe.serve', text=serve_label)
        if Server.instance:
            col.operator("wm.url_open", text="Open Preview").url = f'http://localhost:{PORT}'
        col.label(text=scene.s_output, icon='INFO')

class AframeClearAsset_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clear_asset_dir"
    bl_label = "Crear Asset Directory"
    bl_description = "Crear Asset Directory"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )

        # Clear existing "assests" directory
        assets_dir = os.path.join ( DEST_RES, PATH_ASSETS )
        if os.path.exists( assets_dir ):
            shutil.rmtree( assets_dir )
        return {'FINISHED'}

class AframePrepare_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.prepare"
    bl_label = "Prepare for Ligthmapper"
    bl_description = "Prepare Lightmapper"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        bpy.context.scene.TLM_SceneProperties.tlm_mode = 'GPU'
        view_layer = bpy.context.view_layer
        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action='SELECT')
        bpy.context.view_layer.objects.active = obj_active
        for obj in selection:
            obj.select_set(True)
            # some exporters only use the active object
            view_layer.objects.active = obj
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_use = True
            bpy.context.object.TLM_ObjectProperties.tlm_mesh_lightmap_resolution = '256'
        
        return {'FINISHED'}

class AframeClear_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.clear"
    bl_label = "Clear generated lightmaps"
    bl_description = "Clear Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("[CLEAR] delete image "+img.name)
                bpy.data.images.remove(img)
        
        #for material in bpy.data.materials:
        #    material.user_clear()
        #    bpy.data.materials.remove(material)
        
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            os.remove(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        
        #if os.path.exists(os.path.join(DEST_RES, PATH_LIGHTMAPS)):
        #    shutil.rmtree(os.path.join(DEST_RES,PATH_LIGHTMAPS))
        
        return {'FINISHED'}

class AframeSavelm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.savelm"
    bl_label = "Save lightmaps"
    bl_description = "Save Lightmaps"
    
    def execute(self, content):
        images = bpy.data.images
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        for img in images:
            if "_baked" in img.name and img.has_data:
                ext = ".png"
                #ext = "."+img.file_format
                #img.filepath = image_dir_path+img.name+ext         
                #print( os.path.join ( DEST_RES, PATH_LIGHTMAPS, img.name+ext ) )      
                img.file_format = 'PNG'
                img.save_render(os.path.join ( DEST_RES, PATH_LIGHTMAPS, img.name+ext ) )
                print("[SAVE LIGHTMAPS] Save image "+img.name)
        return {'FINISHED'}
    
class AframeLoadlm_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.loadlm"
    bl_label = "load lightmaps"
    bl_description = "Load Lightmaps"
    
    def execute(self, content):
        scene = content.scene
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )
        
        # delete all _baked textures
        images = bpy.data.images
        for img in images:
            if "_baked" in img.name:
                print("delete: "+img.name)
                bpy.data.images.remove(img)
                
        for filename in os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS)):
            bpy.data.images.load(os.path.join ( DEST_RES, PATH_LIGHTMAPS) + filename)
        return {'FINISHED'}    
        
class AframeServe_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.serve"
    bl_label = "Serve Aframe Preview"
    bl_description = "Serve AFrame"
    
    def execute(self, content):
        if (Server.instance):
            Server.instance.stop()
            Server.instance = None
            return {'FINISHED'}
        scene = content.scene
        Server.instance = Server()
        Server.instance.set_folder(os.path.join ( scene.export_path, scene.s_project_name ))
        Server.instance.start()
        
        return {'FINISHED'}

class AframeExport_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.export"
    bl_label = "Export to Aframe Project"
    bl_description = "Export AFrame"

    def execute(self, content):
        assets = []
        entities = []
        lights = []
        print("[AFRAME EXPORTER] Exporting project...")
        scene = content.scene
        scene.s_output = "exporting..."
        script_file = os.path.realpath(__file__)
        #print("script_file dir = "+script_file)
        directory = os.path.dirname(script_file)

        # Destination base path
        DEST_RES = os.path.join ( scene.export_path, scene.s_project_name )


        if __name__ == "__main__":
            #print("inside blend file")
            #print(os.path.dirname(directory))
            directory = os.path.dirname(directory)

        print("[AFRAME EXPORTER] Target Dir = "+directory)

        ALL_PATHS = [ ".", PATH_ASSETS, PATH_RESOURCES, PATH_MEDIA, PATH_ENVIRONMENT, PATH_JAVASCRIPT, PATH_LIGHTMAPS ]
        for p in ALL_PATHS:
            dp = os.path.join ( DEST_RES, p )
            print ( "--- DEST [%s] [%s] {%s}" % ( DEST_RES, dp, p ) )
            os.makedirs ( dp, exist_ok=True )

        #check if addon or script for correct path
        _resources = [
            [ ".", "favicon.ico" ],
            [ ".", "style.css" ],
            [ PATH_RESOURCES, "sky.jpg" ],
            [ PATH_RESOURCES, "play.png" ],
            [ PATH_RESOURCES, "pause.png" ],
            [ PATH_RESOURCES, "play-skip-back.png" ],
            [ PATH_RESOURCES, "mute.png" ],
            [ PATH_RESOURCES, "volume-low.png" ],
            [ PATH_RESOURCES, "volume-high.png" ],
            [ PATH_JAVASCRIPT, "webxr.js" ],
            [ PATH_JAVASCRIPT, "joystick.js" ],
            [ PATH_JAVASCRIPT, "camera-cube-env.js" ],
            [ PATH_ENVIRONMENT, "negx.jpg" ],
            [ PATH_ENVIRONMENT, "negy.jpg" ],
            [ PATH_ENVIRONMENT, "negz.jpg" ],
            [ PATH_ENVIRONMENT, "posx.jpg" ],
            [ PATH_ENVIRONMENT, "posy.jpg" ],
            [ PATH_ENVIRONMENT, "posz.jpg" ],
        ]

        SRC_RES = os.path.join ( directory, PATH_RESOURCES )
        for dest_path, fname in _resources:
            shutil.copyfile ( os.path.join ( SRC_RES, fname ), os.path.join ( DEST_RES, dest_path, fname ) )

        # Loop 3D entities
        exclusion_obj_types = ['CAMERA','LAMP','ARMATURE']
        exported_obj = 0
        videocount=0
        imagecount=0
        scalefactor = 2
        lightmap_files = os.listdir(os.path.join ( DEST_RES, PATH_LIGHTMAPS))
        for file in lightmap_files:
            print("[LIGHTMAP] Found Lightmap file: "+file)

        for obj in bpy.data.objects:
            if obj.type not in exclusion_obj_types:
                print("[AFRAME EXPORTER] loop object "+ obj.name)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
                #bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                location = obj.location.copy()
                rotation = obj.rotation_euler.copy()
                
                bpy.ops.object.location_clear()
                actualposition = str(location.x)+" "+str(location.z)+" "+str(-location.y)
                actualscale = str(scalefactor*bpy.data.objects[obj.name].scale.x)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.y)+" "+str(scalefactor*bpy.data.objects[obj.name].scale.z)
                #pi = 22.0/7.0
                #actualrotation = str(((bpy.data.objects[obj.name].rotation_euler.x) / (2 * pi) * 360) - 90) +" " + str(((bpy.data.objects[obj.name].rotation_euler.z) / (2 * pi) * 360)-0) + " " + str(((bpy.data.objects[obj.name].rotation_euler.y) / (2 * pi) * 360)+90)
                #actualrotation = str(bpy.data.objects[obj.name].rotation_euler.x) +" " + str(bpy.data.objects[obj.name].rotation_euler.z)+ " " + str(bpy.data.objects[obj.name].rotation_euler.y)
                #actualrotation = str(math.degrees(-89.99+bpy.data.objects[obj.name].rotation_euler.x)) +" " + str(90+math.degrees(bpy.data.objects[obj.name].rotation_euler.y))+ " " + str(-90+math.degrees(bpy.data.objects[obj.name].rotation_euler.z))
                #actualrotation = str(math.degrees(rotation.x))+" "+str(math.degrees(rotation.z))+" "+str(math.degrees(-rotation.y))    
                actualrotation = "0 "+str(math.degrees(rotation.z))+" 0"    
                    
                # custom aframe code read from CUSTOM PROPERTIES
                reflections = ""
                animation = ""
                link = ""
                baked = ""
                video = False
                image = False

                # export gltf
                if obj.type == 'MESH':
                    #print(obj.name,"custom properties:")
                    for K in obj.keys():
                        if K not in '_RNA_UI':
                            #print( "\n", K , "-" , obj[K], "\n" )
                            if K == "AFRAME_CUBEMAP" and scene.b_cubemap:
                                if scene.b_camera_cube:
                                    reflections = ' geometry="" camera-cube-env="distance: 500; resolution: 512; repeat: true; interval: 400" '
                                else:
                                    reflections = ' geometry="" cube-env-map="path: '+scene.s_cubemap_path+'; extension: '+scene.s_cubemap_ext+'; reflectivity: 0.99;" '
                            if K == "AFRAME_ANIMATION":
                                animation = ' animation= "'+obj[K]+'" '
                            if K == "AFRAME_HTTP_LINK":
                                #link = ' link="href: '+obj[K]+'" class="clickable" '
                                link = ' link-handler="target: '+obj[K]+'" class="clickable" '
                            if K == "AFRAME_VIDEO":
                                #print("--------------- pos " + actualposition)
                                #print("--------------- rot " + actualrotation)
                                #print("--------------- scale " + actualscale)                                
                                #filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glft' )
                                #bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                                #assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="./assets/'+obj.name + '.gltf'+'"></a-asset-item>')                                
                                assets.append('\n\t\t\t\t<video id="video_'+str(videocount)+'" loop="true" autoplay="true" src="./media/'+obj[K]+'"></video>')
                                entities.append('\n\t\t\t<a-video id="#v_'+str(videocount)+'" src="#video_'+str(videocount)+'" width="1" height="1" scale="'+actualscale+'" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false" '+animation+link+'></a-video>')
                                #entities.append('\n\t\t\t<a-video id="#v_'+str(videocount)+'" src="#video_'+str(videocount)+'" width="'+str(bpy.data.objects[obj.name].scale.x)+'" height="'+str(bpy.data.objects[obj.name].scale.y)+'" scale="1 1 1" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false" '+animation+link+'></a-video>')
                                #entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" gltf-model="#'+obj.name+'" material="src: #video_'+str(videocount)+'" scale="'+actualscale+'" rotation="'+actualrotation+'" position="'+actualposition+'"></a-entity>')
                                video = True
                                videocount = videocount +1
                            if K == "AFRAME_IMAGES":
                                #print(".....images")
                                image = True
                                imagecount = imagecount +1
                                #load K
                                #json_images = '{"1": "image1.jpg", "2": "image2.jpg"}'
                                json_images = obj[K]
                                json_dictionary = json.loads(json_images)
                                for key in json_dictionary:
                                    #print(key, ":", json_dictionary[key])
                                    assets.append('\n\t\t\t\t<img id="image_'+key+'" src="./media/'+json_dictionary[key]+'"></img>')
                                entities.append('\n\t\t\t<a-image images-handler id="#i_'+str(imagecount)+'" src="#image_'+key+'" class="clickable" width="1" height="1" scale="'+actualscale+'" position="'+actualposition+'" rotation="'+actualrotation+'" visible="true" shadow="cast: false"></a-image>')

                    if video == False and image == False:                        
                        # check if baked texture is present on filesystem
                        #images = bpy.data.images
                        #for img in images:
                        #    if obj.name+"_baked" in img.name and img.has_data:
                        #       print("ok")
                        #       baked = 'light-map-geometry="path: lightmaps/'+img.name+'"'
                        print("[LIGHTMAP] Searching Lightmap for object ["+obj.name+"_baked"+"]")                        
                        for file in lightmap_files:
                            if obj.name+"_baked" in file:
                                print("[LIGHTMAP] Found lightmap: "+file)
                                baked = 'light-map-geometry="path: lightmaps/'+file+'"'
                            
                        filename = os.path.join ( DEST_RES, PATH_ASSETS, obj.name ) # + '.glft' )
                        bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                        assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="./assets/'+obj.name + '.gltf'+'"></a-asset-item>')
                        if scene.b_cast_shadows:
                            entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" gltf-model="#'+obj.name+'" scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: true" '+reflections+animation+link+'></a-entity>')
                        else:
                            entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" '+baked+' gltf-model="#'+obj.name+'" scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: false" '+reflections+animation+link+'></a-entity>')
                # deselect object
                obj.location = location
                obj.select_set(state=False)
                exported_obj+=1

        bpy.ops.object.select_all(action='DESELECT')

        # Templating ------------------------------
        #print(assets)
        all_assets = ""
        for x in assets:
            all_assets += x

        all_entities = ""
        for y in entities:
            all_entities += y

        # scene
        if scene.b_stats:
            showstats = "stats"
        else:
            showstats = ""

        # joystick
        if scene.b_joystick:
            showjoystick = "joystick"
        else:
            showjoystick = ""

        if scene.b_raycast:
            raycaster='raycaster = "far: '+str(scene.f_raycast_length)+'; interval: '+str(scene.f_raycast_interval)+'; objects: .clickable,.links"'
        else:
            raycaster=""

        #vr_controllers
        if scene.b_vr_controllers:
            showvr_controllers = '<a-entity id="leftHand" oculus-touch-controls="hand: left" vive-controls="hand: left"></a-entity>\n\t\t\t\t\t<a-entity id="rightHand" laser-controls oculus-touch-controls="hand: right" vive-controls="hand: right" '+raycaster+'></a-entity>'
        else:
            showvr_controllers = ""

        #shadows
        if scene.b_cast_shadows:
            showcast_shadows = "true"
            template_render_shadows = 'shadow="type: pcfsoft; autoUpdate: true;"'            
        else:
            showcast_shadows = "false"
            template_render_shadows = 'shadow="type: basic; autoUpdate: false;"'            

        # Sky
        if scene.b_show_env_sky:
            show_env_sky = '<a-sky src="#sky" material="" geometry="" rotation="0 90 0"></a-sky>'                              
        else:
            show_env_sky = '<a-sky color="#ECECEC"></a-sky>'

        # if use bake, the light should have intensity near zero
        if scene.b_use_lightmapper:
            light_directional_intensity = "0"
            light_ambient_intensity = "0.1"
        else:
            light_directional_intensity = "1.0"
            light_ambient_intensity = "1.0"

        s = t.substitute(
            asset=all_assets,
            entity=all_entities,
            stats=showstats,
            aframe_version=scene.s_aframe_version,
            joystick=showjoystick,
            vr_controllers=showvr_controllers,
            cast_shadows=showcast_shadows,
            player_height=scene.f_player_height,
            player_speed=scene.f_player_speed,
            show_raycast=raycaster,
            sky=show_env_sky,
            directional_intensity=light_directional_intensity,
            ambient_intensity=light_ambient_intensity,
            render_shadows=template_render_shadows)


        #print(s)

        # Saving the main INDEX FILE
        with open( os.path.join ( DEST_RES, PATH_INDEX ), "w") as file:
            file.write(s)

        scene.s_output = str(exported_obj)+" meshes exported"
        return {'FINISHED'}


# ------------------------------------------- REGISTER / UNREGISTER
_props = [
    ("str", "s_aframe_version", "A-Frame", "A-Frame version", "1.0.4" ),
    ("bool", "b_stats", "Show Stats", "Enable rendering stats in game" ),
    ("bool", "b_vr_controllers", "Enable VR Controllers (HTC,Quest)", "Enable HTC/Quest Controllers in game", True ),
    ("bool", "b_hands", "Use Hands Models", "Use hands models instead of controllers", True ),
    ("bool", "b_joystick", "Show Joystick", "Add a joystick on screen" ),
    ("bool", "b_cubemap", "Cube Env Map", "Enable Cube Map component" ),
    ("str", "s_cubemap_path", "Path", "Cube Env Path", "/env/" ),
    ("bool", "b_cubemap_background", "Enable Background", "Enable Cube Map Background" ),
    ("str", "s_cubemap_ext", "Ext", "Image file extension", "jpg" ),
    ("bool", "b_blender_lights", "Export Blender Lights", "Export Blenedr Lights or use Aframe default ones" ),
    ("bool", "b_cast_shadows", "Cast Shadows", "Cast and Receive Shadows" ),
    ("bool", "b_lightmaps", "Use Lightmaps as Occlusion (GlTF Settings)", "GLTF Models don\'t have lightmaps: turn on this option will save lightmaps to Ambient Occlusion in the GLTF models" ),
    ("float", "f_player_speed", "Player Speed", "Player Speed", 0.1 ),
    ("float", "f_raycast_length", "Raycast Length","Raycast lenght to interact with objects", 20.0 ),
    ("float", "f_raycast_interval", "Raycast Interval","Raycast Interval to interact with objects", 1500.0 ),
    ("str", "export_path", "Export To","Path to the folder containing the files to import", "C:/Temp/", 'FILE_PATH'),
    ("str", "s_project_name", "Name", "Project's name","aframe-prj"),
    ("str", "s_output", "output","output export","output"),
    ("bool", "b_use_lightmapper", "Use Lightmapper Add-on for bake lightmaps","Use Lightmapper for baking" ),
    ("bool", "b_camera_cube", "Camera Cube Env","Enable Camera Cube Env component"),
    ("float", "f_player_height", "Player Height","Player Height", 1.7),
    ("bool", "b_raycast", "Enable Raycast","Enable Raycast"),
    ("bool", "b_show_env_sky", "Show Environment Sky","Show Environment Sky"),
]


def _reg_bool ( scene, prop, name, descr, default = False ):
    setattr ( scene, prop, bpy.props.BoolProperty ( name = name, description = descr, default = default ) )

def _reg_str ( scene, prop, name, descr, default = "", subtype = "" ):
    if subtype:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default, subtype = subtype ) )
    else:
        setattr ( scene, prop, bpy.props.StringProperty ( name = name, description = descr, default = default ) )


def _reg_float ( scene, prop, name, descr, default = 0.0 ):
    setattr ( scene, prop, bpy.props.FloatProperty ( name = name, description = descr, default = default ) )

def register():
    scn = bpy.types.Scene

    bpy.utils.register_class(AframeExportPanel_PT_Panel)
    bpy.utils.register_class(AframeExport_OT_Operator)
    bpy.utils.register_class(AframeServe_OT_Operator)
    bpy.utils.register_class(AframeSavelm_OT_Operator)
    bpy.utils.register_class(AframeClear_OT_Operator)
    bpy.utils.register_class(AframePrepare_OT_Operator)
    bpy.utils.register_class(AframeClearAsset_OT_Operator)    
    
    
    for p in _props:
        if p [ 0 ] == 'str': _reg_str ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'bool': _reg_bool ( scn, * p [ 1 : ] )
        if p [ 0 ] == 'float': _reg_float ( scn, * p [ 1 : ] )

def unregister():
    bpy.utils.unregister_class(AframeExportPanel_PT_Panel)
    bpy.utils.unregister_class(AframeExport_OT_Operator)
    bpy.utils.unregister_class(AframeServe_OT_Operator)

    for p in _props:
        del bpy.types.Scene [ p [ 1 ] ]

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
