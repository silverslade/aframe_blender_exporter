# Blender Exporter to A-Frame VR


This Blender add-on will allow you to model your scene in Blender and export to an A-Frame VR project with a single click. This is an open source project under MIT terms, so feel free to email me or ask for a pull request.


<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/aframe_exporter.png">
</p>

## Features

+ Pure Blender AddOn (tested on Blender 2.83)
+ Simple UI for configuration
+ It exports and creates a new A-Frame project
+ Optimized Pipeline: Model with blender -> export -> test on browser
+ Open Source (MIT)

## Main Configuration
This Addon manages the following settings (all of them switchable inside the UI):

+ Stats window
+ Joystick controller on screen
+ HTC and Quest controllers
+ Cube Map Env (for objects with reflections)
+ Cast Shadows
+ Manage Raycast
+ Manage player's speed and height
+ Manage project name and final export directory

## Contents

+ [Installation](#installation)
+ [How to use the Addon](#How-to-use-the-Addon)
+ [Credits](#Credits)
+ [Help](#Help)
+ [License](#License)

## Installation

+ Download the latest release version from [Itch.io](https://silverslade.itch.io/a-frame-blender-exporter)
+ Open Blender (2.80+)
+ Edit -> Preferences -> Add-ons -> Install
+ Browse and choose the addon zip file
+ Enable the addon

## How to use the Addon

<p align="center">
  <img src="https://github.com/silverslade/aframe_blender_exporter/raw/master/images/main-window.png">
</p>


+ Open a new/existing blender scene.
+ Open the View3D window (`n` key) to show the export window.
+ Set up your settings
+ Click on `Export to A-Frame project`
+ Launch a local web server to test your WebVR page: there are several possibilities, the best are nodejs or python inside the output target directory)
    + run `live-server` (install it with `npm install -g live-server`) or
    + run `python -m SimpleHTTPServer`

For better instructions, see the official [project page](https://silverslade.itch.io/a-frame-blender-exporter).

### Main UI configuration

| Property       | Description      | Default Value                          |
|----------------|------------------|----------------------------------|
| A-Frame        | A-Frame Version  | `1.0.4` | 
| Show Stats     | Show the A-Frame stats window. For debug purpose.  | `False` | 
| Show Joystick  | Show a icon controller to move player  | `False`    | 
| Enable VR Controllers (HTC, Quest) | Enable Controllers for further inteactions  | `False`  | 
| Cube Env Map   | For skybox reflections (but not objects reflections). To get objects reflections also, enable the `Camera Cube Env` | `False`  | 
| Cast Shadows   | For dynamic lights and shadows.| `False`    | 
| Enable Raycast   | Activate a raycast for interactions | `False`     | 
| Name   | Project name. It's the target directory where your project will be created. | `aframe-prj`       | 
| Export To   | Target Directory where the `Name` Directory will be created | `C:\temp\` | 

# Credits

## Contributors

In collaboration with `Andrea Rotondo`, a VR Expert since 1998
informations and contacs: 
+ rotondo.andrea@gmail.com
+ http://virtual-art.it
+ https://www.facebook.com/wox76
+ https://www.facebook.com/groups/134106979989778/

## Third Party Components
This Addon Uses the following 3rd Party Software (or their integration/modification):
+ Aframe Joystick - https://github.com/mrturck/aframe-joystick
+ Aframe Components - https://github.com/colinfizgig/aframe_Components
+ Icons - https://ionicons.com/


# Help

If you like the project and want to help, these are the main activities:

+ Writing documentation
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