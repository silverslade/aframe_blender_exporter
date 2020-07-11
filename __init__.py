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
    - add a CUSTOM PROPERTY named "AFRAME_CUBEMAP" if you want to add a cube map sky to the mesh
    - open the addon and set your configuration
    - click on "Export A-Frame Project" button
    - your project will be saved in the export directory
    - launch "live-server" (install it with "npm install -g live-server") or "python -m SimpleHTTPServer"
    
CUSTOM_PROPERTIES: 
    AFRAME_CUBEMAP -> if present, set reflections on to the mesh object (metal -> 1, rough -> 0)

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
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "View3D",
    "warning" : "",
    "category" : "3D View"
}

import os
import bpy
import shutil
from string import Template

# Constants
PATH_INDEX = "/index.html"
PATH_ASSETS = "/assets/"
PATH_RESOURCES = "/resources/"
PATH_ENVIRONMENT = "/env/"
PATH_JAVASCRIPT = "/js/"
AFRAME_ENABLED = "AFRAME_ENABLED"
AFRAME_HTTP_LINK = "AFRAME_HTTP_LINK"
AFRAME_ANIM_ROTATE = "AFRAME_ANIM_ROTATE"
AFRAME_DOWNLOAD = "AFRAME_DOWNLOAD"   
AFRAME_VIDEO = "AFRAME_VIDEO"
AFRAME_VIDEO_AUTOPLAY = "AFRAME_VIDEO_AUTOPLAY"
AFRAME_VIDEO_STREAM = "AFRAME_VIDEO_STREAM"   

assets = []
entities = []
lights = []
showstats = ""

# Index html a-frame template
t = Template('\
<!-- Do not edit: generated automatically by AFRAME Exporter -->\n\
<html>\n\
\t<head>\n\
\t\t<title>WebVR Application</title>\n\
\t\t<link rel="icon" type="image/png" href="favicon.ico"/>\n\
\t\t<meta name="description" content="3D Application">\n\
\t\t<meta charset="utf-8">\n\
\t\t<meta http-equiv="X-UA-Compatible" content="IE=edge">\n\
\t\t<meta name="viewport" content="width=device-width, initial-scale=1">\n\
\t\t<script src="https://aframe.io/releases/${aframe_version}/aframe.min.js"></script>\n\
\t\t<script src="https://cdn.jsdelivr.net/gh/donmccurdy/aframe-extras@v6.1.0/dist/aframe-extras.min.js"></script>\n\
\t\t<script type="text/javascript" src="js/joystick.js"></script>\n\
\t\t<script type="text/javascript" src="js/camera-cube-env.js"></script>\n\
\t\t\n\
\t\t<link rel="stylesheet" type="text/css" href="style.css">\n\
\t</head>\n\
\t<body>\n\
\t\t<a-scene ${stats} ${joystick}>\n\
\t\t\t<!-- Assets -->\n\
\t\t\t<a-assets>${asset}\n\
\t\t\t\t<img id="sky" src="./resources/sky.jpg">\n\
\t\t\t</a-assets>\n\
\n\
\t\t\t<!-- Entities -->\
\t\t\t${entity}\n\
\n\
\t\t\t<!-- Camera -->\n\
\n\
\t\t\t<a-entity id="player" position="0 -0.2 0" movement-controls="speed: ${player_speed};">\n\
\t\t\t\t<a-entity id="camera" camera position="0 ${player_height} 0" look-controls="pointerLockEnabled: true"\n\
\t\t\t\t\t<a-entity id="cursor" cursor="fuse: false;" animation__click="property: scale; startEvents: click; easing: easeInCubic; dur: 50; from: 	0.1 0.1 0.1; to: 1 1 1"\n\
\t\t\t\t\t\tposition="0 0 -0.1"\n\
\t\t\t\t\t\tgeometry="primitive: circle; radius: 0.001;"\n\
\t\t\t\t\t\tmaterial="color: #CCC; shader: flat;"\n\
\t\t\t\t\t\t${show_raycast}>\n\
\t\t\t\t\t</a-entity>\n\
\t\t\t\t\t${vr_controllers}\n\
\t\t\t\t</a-entity>\n\
\t\t\t</a-entity>\n\
\n\
\t\t\t<!-- Lights and Skybox -->\
\n\
\t\t\t<a-entity light="intensity: 1; castShadow: ${cast_shadows}; shadowBias: -0.001; shadowCameraFar: 501.02; shadowCameraBottom: 12; shadowCameraFov: 101.79; shadowCameraNear: 0; shadowCameraTop: -5; shadowCameraRight: 10; shadowCameraLeft: -10; shadowRadius: 2" position="1.36586 7.17965 1"></a-entity>\n\
\t\t\t<a-entity light="type: ambient"></a-entity>\n\
\n\
\t\t\t<!-- <a-sky color="#ECECEC"></a-sky> -->\n\
\t\t\t<a-sky src="#sky" material="" geometry="" rotation="0 90 0"></a-sky>\n\
\t\t</a-scene>\n\
\t</body>\n\
</html>\n\
<!-- Do not edit: generated automatically by AFRAME Exporter -->')


class AframeExportPanel_PT_Panel(bpy.types.Panel):
    bl_idname = "AFRAME_EXPORT_PT_Panel"
    bl_label = "Aframe Exporter"
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
            box.prop(scene, "b_cubemap_background")
            box.prop(scene, "s_cubemap_path", text="test")            
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
        col.prop(scene, "b_delete_assets_dir")
        col.separator()
        #col.label(text="Export to a-frame project", icon='NONE')
        col.operator('aframe.export', text='Export A-Frame Project')
        col.label(text=scene.s_output, icon='INFO')

class AframeExport_OT_Operator(bpy.types.Operator):
    bl_idname = "aframe.export"
    bl_label = "Export to Aframe Project"
    bl_description = "Export AFrame"

    def execute(self, content):
        assets = []
        entities = []
        lights = []
        print("exporting...")
        scene = content.scene
        scene.s_output = "exporting..."
        script_file = os.path.realpath(__file__)
        #print("script_file dir = "+script_file)
        directory = os.path.dirname(script_file)
                
        if __name__ == "__main__":
            #print("inside blend file")  
            #print(os.path.dirname(directory))
            directory = os.path.dirname(directory)  
        
        print("Target Dir = "+directory)
                
        # Clear existing "assests" dir if required   
        if scene.b_delete_assets_dir:           
            if os.path.exists(scene.export_path+scene.s_project_name+PATH_ASSETS):
                shutil.rmtree(scene.export_path+scene.s_project_name+PATH_ASSETS)
                    
        # Create output path
        os.makedirs(scene.export_path+scene.s_project_name, exist_ok=True)
        os.makedirs(scene.export_path+scene.s_project_name+PATH_ASSETS, exist_ok=True)
        os.makedirs(scene.export_path+scene.s_project_name+PATH_RESOURCES, exist_ok=True)
        os.makedirs(scene.export_path+scene.s_project_name+PATH_ENVIRONMENT, exist_ok=True)                
        os.makedirs(scene.export_path+scene.s_project_name+PATH_JAVASCRIPT, exist_ok=True)
        
        #check if addon or script for correct path
        shutil.copyfile(directory+PATH_RESOURCES+"sky.jpg", scene.export_path+scene.s_project_name+PATH_RESOURCES+"sky.jpg")
        shutil.copyfile(directory+PATH_RESOURCES+"controller.png", scene.export_path+scene.s_project_name+PATH_RESOURCES+"controller.png")        
        shutil.copyfile(directory+PATH_RESOURCES+"favicon.ico", scene.export_path+scene.s_project_name+"/favicon.ico")    
        shutil.copyfile(directory+PATH_RESOURCES+"style.css", scene.export_path+scene.s_project_name+"/style.css")
        shutil.copyfile(directory+PATH_RESOURCES+"joystick.js", scene.export_path+scene.s_project_name+PATH_JAVASCRIPT+"/joystick.js")
        shutil.copyfile(directory+PATH_RESOURCES+"camera-cube-env.js", scene.export_path+scene.s_project_name+PATH_JAVASCRIPT+"/camera-cube-env.js")       
        shutil.copyfile(directory+PATH_RESOURCES+"joystick.js", scene.export_path+scene.s_project_name+PATH_JAVASCRIPT+"/joystick.js")
        shutil.copyfile(directory+PATH_RESOURCES+"negx.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/negx.jpg")
        shutil.copyfile(directory+PATH_RESOURCES+"negy.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/negy.jpg")
        shutil.copyfile(directory+PATH_RESOURCES+"negz.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/negz.jpg")
        shutil.copyfile(directory+PATH_RESOURCES+"posx.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/posx.jpg")        
        shutil.copyfile(directory+PATH_RESOURCES+"posy.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/posy.jpg")        
        shutil.copyfile(directory+PATH_RESOURCES+"posz.jpg", scene.export_path+scene.s_project_name+PATH_ENVIRONMENT+"/posz.jpg")        
        
        
        # Loop 3D entities
        exclusion_obj_types = ['CAMERA','LAMP','ARMATURE']
        exported_obj = 0
        reflections = ""

        for obj in bpy.data.objects:
            if obj.type not in exclusion_obj_types:
                print(obj.name)
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(state=True)
                bpy.context.view_layer.objects.active = obj
                #bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY') 
                location = obj.location.copy()
                bpy.ops.object.location_clear()
                actualposition = str(location.x)+" "+str(location.z)+" "+str(-location.y)

                # export gltf
                if obj.type == 'MESH':
                    print(obj.name,"custom properties:")
                    for K in obj.keys():
                        if K not in '_RNA_UI':
                            print( "\n", K , "-" , obj[K], "\n" )
                            if K == "AFRAME_CUBEMAP" and scene.b_cubemap:
                                if scene.b_camera_cube:
                                    reflections = ' geometry="" camera-cube-env="distance: 500; resolution: 512; repeat: true; interval: 400"'
                                else:
                                    reflections = ' geometry="" cube-env-map="path: '+scene.s_cubemap_path+'; extension: '+scene.s_cubemap_ext+'; reflectivity: 0.99;"'
                    filename = scene.export_path+scene.s_project_name+PATH_ASSETS + obj.name + '.gltf'
                    bpy.ops.export_scene.gltf(filepath=filename, export_format='GLTF_EMBEDDED', use_selection=True)
                    assets.append('\n\t\t\t\t<a-asset-item id="'+obj.name+'" src="/assets/'+obj.name + '.gltf'+'"></a-asset-item>')
                    if scene.b_cast_shadows:
                        entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" gltf-model="#'+obj.name+'" scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: true"'+reflections+'></a-entity>')
                    else:
                        entities.append('\n\t\t\t<a-entity id="#'+obj.name+'" gltf-model="#'+obj.name+'" scale="1 1 1" position="'+actualposition+'" visible="true" shadow="cast: false"'+reflections+'></a-entity>')
                # deselect object
                obj.location = location
                obj.select_set(state=False)
                exported_obj+=1
                


        bpy.ops.object.select_all(action='DESELECT')

        # Templating ------------------------------
        #print(assets)
        all_assets = ""
        for x in assets:
            all_assets = all_assets+x

        all_entities = ""
        for y in entities:
            all_entities = all_entities+y

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
            showvr_controllers = '\t\t\t<a-entity id="leftHand" oculus-touch-controls="hand: left" vive-controls="hand: left"></a-entity>\n\t\t\t<a-entity id="rightHand" laser-controls oculus-touch-controls="hand: right" vive-controls="hand: right" '+raycaster+'></a-entity>'
        else:
            showvr_controllers = ""    
            
        #shadows
        if scene.b_cast_shadows:
            showcast_shadows = "true"
        else:
            showcast_shadows = "false"
            
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
            show_raycast=raycaster)
            
            
        #print(s)

        # Saving the main INDEX FILE
        with open(scene.export_path+scene.s_project_name+PATH_INDEX, "w") as file:
            file.write(s)
        
        scene.s_output = str(exported_obj)+" meshes exported"
        return {'FINISHED'}


# ------------------------------------------- REGISTER / UNREGISTER 

def register():
    bpy.utils.register_class(AframeExportPanel_PT_Panel)
    bpy.utils.register_class(AframeExport_OT_Operator)
    bpy.types.Scene.s_aframe_version = bpy.props.StringProperty(
        name="A-Frame",
        description="A-frame version",
        default = "1.0.4") 
    bpy.types.Scene.b_stats = bpy.props.BoolProperty(
        name="Show Stats",
        description="Enable rendering stats in game",
        default = False)
    bpy.types.Scene.b_vr_controllers = bpy.props.BoolProperty(
        name="Enable VR Controllers (HTC,Quest)",
        description="Enable HTC/Quest Controllers in game",
        default = True)    
    bpy.types.Scene.b_hands = bpy.props.BoolProperty(
        name="Use Hands Models",
        description="Use hands models instead of controllers",
        default = True)               
    bpy.types.Scene.b_joystick = bpy.props.BoolProperty(
        name="Show Joystick",
        description="Add a joystick on screen",
        default = False)       
    bpy.types.Scene.b_cubemap = bpy.props.BoolProperty(
        name="Cube Env Map",
        description="Enable Cube Map component",
        default = False)   
    bpy.types.Scene.s_cubemap_path = bpy.props.StringProperty(
        name="Path",
        description="Cube Env Path",
        default = "/env/")   
    bpy.types.Scene.b_cubemap_background = bpy.props.BoolProperty(
        name="Enable Background",
        description="Enable Cube Map Background",
        default = False)  
    bpy.types.Scene.s_cubemap_ext = bpy.props.StringProperty(
        name="Ext",
        description="Image File Extension",
        default = "jpg")
    bpy.types.Scene.b_blender_lights = bpy.props.BoolProperty(
        name="Export Blender Lights",
        description="Export Blenedr Lights or use Aframe default ones",
        default = False)                                          
    bpy.types.Scene.b_cast_shadows = bpy.props.BoolProperty(
        name="Cast Shadows",
        description="Cast and Receive Shadows",
        default = False)          
    bpy.types.Scene.b_lightmaps = bpy.props.BoolProperty(
        name="Use Lightmaps as Occlusion (GlTF Settings)",
        description="GLTF Models don\'t have lightmaps: turn on this option will save lightmaps to Ambient Occlusion in the GLTF models",
        default = False)
    bpy.types.Scene.f_player_speed = bpy.props.FloatProperty(
        name="Player Speed",
        description="Player Speed",
        default = 0.1)           
    bpy.types.Scene.f_raycast_length = bpy.props.FloatProperty(
        name="Raycast Length",
        description="Raycast lenght to interact with objects",
        default = 1.0)  
    bpy.types.Scene.f_raycast_interval = bpy.props.FloatProperty(
        name="Raycast Interval",
        description="Raycast Interval to interact with objects",
        default = 1500.0)
    bpy.types.Scene.export_path = bpy.props.StringProperty(
        name = "Export To",
        description = "Path to the folder containing the files to import",
        default = "C:/temp/",
        subtype = 'FILE_PATH')    
    bpy.types.Scene.s_project_name = bpy.props.StringProperty(
        name="Name",
        description="Project's name",
        default = "aframe-prj")     
    bpy.types.Scene.s_output = bpy.props.StringProperty(
        name="output",
        description="output export",
        default = "output")     
    bpy.types.Scene.b_delete_assets_dir = bpy.props.BoolProperty(
        name="Clear Assets Dir before export",
        description="Clear the asset dir",
        default = False)
    bpy.types.Scene.b_camera_cube = bpy.props.BoolProperty(
        name="Camera Cube Env",
        description="Enable Camera Cube Env component",
        default = False)               
    bpy.types.Scene.f_player_height = bpy.props.FloatProperty(
        name="Player Height",
        description="Player Height",
        default = 1.7)     
    bpy.types.Scene.b_raycast = bpy.props.BoolProperty(
        name="Enable Raycast",
        description="Enable Raycast",
        default = False)               
                                  

        
def unregister():
    bpy.utils.unregister_class(AframeExportPanel_PT_Panel)
    bpy.utils.unregister_class(AframeExport_OT_Operator)
    del bpy.types.Scene.s_aframe_version
    del bpy.types.Scene.b_stats
    del bpy.types.Scene.b_vr_controllers
    del bpy.types.Scene.b_hands
    del bpy.types.Scene.b_joystick
    del bpy.types.Scene.b_cubemap
    del bpy.types.Scene.s_cubemap_path
    del bpy.types.Scene.b_cubemap_background
    del bpy.types.Scene.s_cubemap_ext	
    del bpy.types.Scene.b_blender_lights	
    del bpy.types.Scene.b_cast_shadows	
    del bpy.types.Scene.b_lightmaps
    del bpy.types.Scene.f_player_speed
    del bpy.types.Scene.f_raycast_length
    del bpy.types.Scene.f_raycast_interval
    del bpy.types.Scene.export_path
    del bpy.types.Scene.s_project_name
    del bpy.types.Scene.s_output
    del bpy.types.Scene.b_delete_assets_dir
    del bpy.types.Scene.b_camera_cube
    del bpy.types.Scene.f_player_height    
    del bpy.types.Scene.b_raycast  
    

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()