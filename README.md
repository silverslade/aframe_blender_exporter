# Blender Exporter to A-Frame VR

This Blender add-on allows you to model your scene in Blender and export it to an A-Frame VR project with a single click. 
The generated sources can be modified manually according to your project needs and can use a baking process to use baked Lightmaps.

This is an open source project under MIT terms, so feel free to email me or ask for a pull request, or just offer me a coffe!

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/aframe_exporter_0_0_6.png">
</p>

## Features

+ Pure Blender Add-On (tested on Blender 2.83)
+ Simple UI for configuration
+ It exports and creates a new A-Frame project
+ Optimized Pipeline: Model with blender -> export -> test on browser
+ Use baked Lightmaps generated with [The Lightmapper Add-on](https://github.com/Naxela/The_Lightmapper) by Naxela
+ Use of a A-Frame html template saved inside the blend file (to make a higher customisation)
+ Open Source (MIT)

## Changelog & todo

See [here](https://github.com/silverslade/aframe_blender_exporter/blob/master/CHANGELOG.md) for the updated changelog.

## Main Configuration
This Addon manages the following settings (all of them switchable inside the UI):

+ Stats window
+ Joystick controller on screen
+ HTC and Quest controllers
+ Cube Map Env (for objects with reflections)
+ Cast Shadows
+ Raycast Management
+ Player's speed and height Management
+ Project name and final export directory
+ Use of the Lightmapper add-on to add lightmaps to the exported models
+ Use an embedded HTTP Server for quick preview

## Contents

+ [Installation](#installation)
+ [How to use the Addon](#How-to-use-the-Addon)
+ [Credits](#Credits)
+ [Help](#Help)
+ [License](#License)

## Installation

+ Download the latest release version from [Itch.io](https://silverslade.itch.io/a-frame-blender-exporter)
+ Open Blender (2.83+)
+ Edit -> Preferences -> Add-ons -> Install
+ Browse and choose the addon zip file
+ Enable the addon
+ Note: This addon requires the glTF Exporter 2.0 (Add-on version v1.2.75)
+ Note: If you want to use baked Lightmaps, it requires the Lightmapper Add-on, [The Lightmapper Add-on](https://github.com/Naxela/The_Lightmapper). You have to install it manually.

## How to use the Addon

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/main-window.png">
</p>


+ Open a new/existing blender scene.
+ Open the View3D window (`n` key) to show the export window.
+ Set up best settings for your scene
+ Click on `Export to A-Frame project`
+ Launch a local web server to test your WebVR page: there are several possibilities
    + run the embedded server, click on the `Start Serving` button
    + run `live-server` (install it with `npm install -g live-server`)
    + run `python -m SimpleHTTPServer`
+ Customize the 'index.html'-template in the Script-tab for future exports
+ Use `Custom Properties` of blender-objects to control tags/attributes ([example](https://gist.github.com/coderofsalvation/2468dc3dfbaca0520cd65c20dfad7eb8))

For massive exports, 'live-server' could be more useful because it can manage a content auto-refresh.

For better instructions, see the official [project page](https://silverslade.itch.io/a-frame-blender-exporter).

### Main UI configuration

Main Ui for the current version 0.0.6.
For a better usability, the add-on is divided in 5 main panels: a-frame, player, interactive/action, bake, exporter.

#### A-Frame Panel

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/aframe_panel.png">
</p>

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| A-Frame | A-Frame Version  | `1.0.4` | 
| Show Stats | Show the A-Frame stats window. For debug purpose.  | `False`| 
| Show Joystick | Show a icon controller to move player  | `False` | 
| Enable VR Controllers (HTC, Quest) | Enable Controllers for further inteactions  | `False` | 
| Cube Env Map | For skybox reflections (but not objects reflections). To get objects reflections also, enable the `Camera Cube Env` | `False` | 
| Camera Cube Env | with objects reflections | `False` | 
| Show Enviroment Sky | Activate a default skybox | `False` | 
| Enable Background | Camera cube env with background sky | `False` | 
| Path | directory path for the equirectangular sky  | `/env/` | 
| Ext | with objects reflections | `jpg` | 
| Cast Shadows | For dynamic lights and shadows.| `False` | 

#### Player Panel

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/player_panel.png">
</p>

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| Enable Raycast | Activate a raycast for interactions. You can set length and interval values | `False` | 
| Raycast Length | Set the Length of the raycast. Shorter or turned off is for better performance | `4.0` | 
| Raycast Interval | Set the polling interval in msec. Higher is for better performance  | `2000.0` | 
| Player Height | Set the Height of the main camera | `1.70` | 
| Player Speed | Set the Speed of the player | `0.1` | 

#### Interactive/Action Panel

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/interactive_panel.png">
</p>

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| Add Cubemap | Enable the reflections for the selected object  |  | 
| Add Rotation on Z | Enable rotation animation on Z axis for the selected object  |  | 
| Add Toggle Images | set 2 images toggling with click on the selected object (plane mesh)  |  | 
| Add Link Web | Enable html link when clicking on the selected object  |  | 
| Add Video | set a mp4 video for the selected object  (plane mesh) |  | 

#### Bake Panel

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/bake_panel.png">
</p>

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| Use Lightmapper Add-on for bake lightmaps | If checked the generated lightmaps will be used for the meshes| `False` | 
| 0 "Delete all Lightmaps" | clear memory and files lightmaps |  | 
| 1 "Prepare Selection for Lightmapper" | select objects for bake and set Lightmapper configuration| WIP  | 
| 2 "Bake with Lightmapper" | Bake with the Lightmapper add-on | (wait the end of the process, better is toggle on Window -> System Console) | 
| 3 "Save Lightmaps" | all lightmaps will be copied inside a "lightmaps" directory in the target project |  | 
| 4 "Clean Lightmaps | it's needed because the changes to the shaders can be incompatible with A-Frame |  | 


#### Exporter Panel

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/export_panel.png">
</p>

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| Name | Project name. It's the target directory where your project will be created. | `aframe-prj`       | 
| Export To | Target Directory where the `Name` Directory will be created | `C:/temp/` | 
| Clear Assets Directory | To remove old 3d models from the main assets dir |  | 

### The Lightmapper Add-on

Since the 0.0.5+ version, the A-Frame Exporter will be compatible with the Lightmapper Add-on by Naxela.

The Lightmapper Add-on is an open source Blender Add-on project for an incredibly quick baking process: it uses the GPU and it can be configured to use a denoiser and an open CV module to clean the lightmaps. It can be much faster than the Blender Bake standard process.

To use the Lightmapper for baking lightmaps:

+ Install the Add-on from [Here](https://github.com/Naxela/The_Lightmapper)
+ Install and configure the denoise and opencv 
+ Untick the "Cast Shadows" option
+ Open the "Bake" panel and follow the enumerated buttons
+ 0 "Delete all Lightmaps"
+ 1 "Prepare Selection for Lightmapper"
+ 2 "Bake with Lightmapper" (wait the end of the process, better is toggle on Window -> System Console)
+ 3 "Save Lightmaps" (all lightmaps will be copied inside a "lightmaps" directory in the target project)
+ 4 "Clean Lightmaps" (it's needed because the changes to the shaders can be incompatible with A-Frame)
+ Then you can use Aframe exporter as usual - "Export A-Frame project" (it will load the saved lightmaps and it will apply them to the a frame component)
+ Remember to make backups. Often.

Though the process may seem quite rough, it works. In the future release I'll work for a more linear process.
But in few minutes you can enjoy a complex baked scene inside A-Frame with just few clicks.

# Credits

In collaboration with `Andrea Rotondo`, a VR Expert since 1998
informations and contacs: 
+ rotondo.andrea@gmail.com
+ http://virtual-art.it
+ https://www.facebook.com/wox76
+ https://www.facebook.com/groups/134106979989778/

## Contributors

+ Code Refactoring - [@fsoft72](https://github.com/fsoft72)
+ HTTP Embedded Server - [@msfeldstein](https://github.com/msfeldstein)
+ embedded index.html template - [@coderofsalvation](https://github.com/coderofsalvation)

## Third Party Components
This Addon Uses the following 3rd Party Software (or their integration/modification):
+ Aframe Joystick - https://github.com/mrturck/aframe-joystick
+ Aframe Components - https://github.com/colinfizgig/aframe_Components
+ Icons - https://ionicons.com/


# Help

If you like the project and want to help, these are the main activities:

+ Writing documentation (wiki)
+ Writing Official Manual or (video/text) tutorial
+ Tests on different O.S. (i.e. MacOSX, Linux)
+ Python script programming
+ Add new features

In this case, drop me a line.

# License
The MIT License (MIT)

Copyright (c) 2020 Alessandro Schillaci

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
