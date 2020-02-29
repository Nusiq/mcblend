# Blender-Export-MC-Bedrock-Model
Blender addon that exports models for custom entities for Minecraft Bedrock Edition.

## Features
- Exporting models into json files that for minecraft bedrock edition.
- Exporting animations into json files that for minecraft bedrock edition.

## Planned features
- UV Mapping/Texturing the models for export
- Exporting minecraft models that use "inflate" option.
- Optimizing the size of the animation file (currently it defines a rotation, location and scale for every keyframe of the animation
for every bone).
- Other planned small features can be found in the ["Issues"](https://github.com/Nusiq/Blender-Export-MC-Bedrock-Model/issues]) tab of this project on Github.

## Instalation
1. Download the zip file from github.
2. In Blender do: Edit -> Preferences -> Add-ons -> Install... -> Select the zip file in file explorer.
3. Serch for "MC Bedrock Export" in Add-ons. Check the box to enable the add-on

## How to use it
Minecraft models for bedrock edition support only cuboids. This means that the exported model needs to be created out of
cuboids only. Every meash which is not a cuboid will use its bounding box in process of exporting the model. A mesh which
has one cuboid in it but tilted in relation to the mesh rotation isn't considered to be a cuboid. Tip: You can enable display
of bounding box in object properties in Blender.

### Mcbones and mccubes
To avoid confusion minecraft bones and cubes will be called mcbones and mccubes respectively. Bones of armature in Blender will
be refered as bones and meshes in shape of cube/cuboid will be refered as cubes.

### Parenting mcbones
The add-on implements custom parenting system disconected from default Blender parenting. The system uses custom object
properties (you can see them in object properties tab). This allows to have different parent child setup in blender than in
the exported model.

You can parent object by using "Parent bedrock bone" operator which you can find under the F3 button menu. Tip: You can setup
a shortcut to this function in Object Mode -> Object -> Parent -> right click "Parent bedrock bone" -> Add Shortcut.

You can clear custom parenting property by removing it from the custom properties of the mesh (its called "mc_parent")
or by using "Clear parent from bedrock bone" operator which can be accessed from F3 button menu. Tip: You can setup as shortcut
to this function in Object Mode -> Object -> Parent -> right click "Clear parent from bedrock bone" -> Add Shortcut.

## What becomes a mcbone and what becomes a mccube?
The add-on takes two types of object while creating the models - meshes and empties. Addon decides what should become
an mcbone or mccube automatically by following the certain set of rules (the order of checking this rules is the same
as in this document):
1. If object type is "empty" it creates an mcbone (without mccubes)
2. If the object is a mesh with a child defined by custom property ("mc_parent" in another mesh) it creates mcbone with one
mccube in it.
3. If the object is a mesh with custom property "mc_is_bone" with value set to 1 than the object becomes a mcbone with one
mccube in it.
4. Mesh with parent and without children the mesh becomes a mccube and is added to a list of mccubes of parent mcbone.
5. In every other case (mesh without parent and without children) becomes a mcbone with single mccube in it.

Waring: A mesh that becomes mccube can't be animated. If you wan't to animate a mesh that doesn't have custom children and has
custom parent make sure to add "mc_is_bone" property to it.

## Exporting the models and the animations:
After installation and enabling the add-on there should be an additional tab called "MC Bedrock exporter" on the right side of
3d-viewport. Opening this tab reveals two panels - "Export bedrock animation" and "Export bedrock model" each of this panels contain
2 fields and a button. One of the fields is a file chooser used to select the path of exported file the other field is a text input
for the name of the model/animation. The button is used to export the file.

Before exporting you need to select all of the objects that you want exported. Remember to set the timeline of the animation to a
point in which the model is in its neutral position.
Tip: You can use frame 0 (frame before the animation starts) and add a keyframe with neutral model position to it.

Press the button on a panel to export model or animation.
