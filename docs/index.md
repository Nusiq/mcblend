# Overview
Mcblend is a Blender addon for creating and animating Minecraft Bedrock Edition models.

## Features
- Importing and exporting Minecraft Bedrock Edition polymesh and cube-based
- Exporting keyframe animations and poses for entities and attachables.
- Animations can be baked into Minecraft format even if they use features
  not supported by the game like inverse kinematics and constraints.
- Generating UV-maps and textures for Minecraft models.
- Simplified process of creating physics simulations based on the rigid bodies.

## Planned features
The improvements planned for this Blender plugin are often listed as
["issues"](https://github.com/Nusiq/mcblend/issues) on the GitHub project page.
The page is open for suggestions and feature requests.

## Installation
1. Download and install
  [Blender 2.93](https://www.blender.org/download/lts/2-93/) (the current LTS version).
2. Download the "latest" or "pre-release" version (zip file) from the project
  page on GitHub: [https://github.com/Nusiq/mcblend/releases](https://github.com/Nusiq/mcblend/releases)

!!! Note
    Mcblend project uses *pre-release* for versions which aren't fully
    documented. The are stable and ready to use. It's recommended to use the
    *pre-release* version because it may contain some bug fixes and in most
    cases the only downside is that you might see some unexplained buttons
    here and there.

    Sometimes there is no *pre-release* version available. This means that the
    project is fully documented and you should download the *latest* version.

3. In Blender go to: `Edit -> Preferences -> Add-ons -> Install...`
![](/mcblend/img/blender_addons.png)
4. Select the zip file in the file explorer.
![](/mcblend/img/blender_addons_filechooser.png)
5. Search for "Mcblend" in Add-ons and select the checkbox to enable the add-on
![](/mcblend/img/blender_addons_checkbox.png)

## Updating
Currently there is no system for updating Mcblend. If you want to update it, you
must uninstall the old version of the addon and then install the new one.

## Versioning system
The Mcblend uses semantic versioning with 3 dot-separated numbers:
MAJOR.MINOR.PATCH

- MAJOR - Compatibility breaking change. This means that loading a project made
  with an older version of Mcblend might not work properly. A change of the
  major version number doesn't necessairly mean that Mcblend is vastly
  different from the user's perspective. Historically the major version were
  updated quite often even if possible compatibility problems were unlikely or
  very easy to fix.
- MINOR - Addition of new a new feature.
- PATCH - Bug fix.

Changing MAJOR resets MINOR and PATCH. Changing MINOR resets PATCH.
