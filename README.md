# Blender-Export-MC-Bedrock-Model
Blender addon that exports models for custom entities for Minecraft Bedrock
Edition.

## Features
- Exporting models into json files for minecraft bedrock edition.
- Exporting animations into json files for minecraft bedrock edition.
- UV Mapping/Texturing
- Exporting minecraft models that use "inflate" option.
- Creating UV-mapping template textures.
- Adding locators
## Planned features
- Some planned features can be found in the
["Issues"](https://github.com/Nusiq/Blender-Export-MC-Bedrock-Model/issues])
tab of this project on Github.

## Instalation
1. Download the zip file from github.
2. In Blender do: Edit -> Preferences -> Add-ons -> Install... -> Select the
zip file in file explorer.
3. Serch for "MC Bedrock Export" in Add-ons. Check the box to enable the add-on

## How to use it
Minecraft models for bedrock edition support only cuboids. This means that the
exported model needs to be created out of cuboids only. Every meash which is
not a cuboid will use its bounding box in process of exporting the model. A
mesh which has one cuboid in it but tilted in relation to the object rotation
isn't considered to be a cuboid. Tip: You can enable display of bounding box
in object properties in Blender see if object is a proper cuboid.

### Mcbones and mccubes
To avoid confusion minecraft bones and cubes will be called mcbones and mccubes
respectively. Bones of armature in Blender will be refered as bones and meshes
in shape of cube/cuboid will be refered as cubes.

### Parenting mcbones
The add-on implements custom parenting system disconected from default Blender
parenting. The system uses custom object properties (you can see them in object
properties tab). This allows to have different parent child setup in blender
than in the exported model.

You can parent object by using "Parent bedrock bone" operator which you can
find under the F3 button menu. Tip: You can setup a shortcut to this
function in Object Mode -> Object -> Parent -> right click "Parent bedrock
bone" -> Add Shortcut.

You can clear custom parenting property by removing it from the custom
properties of the mesh (its called "mc_parent") or by using "Clear parent from
bedrock bone" operator which can be accessed from F3 button menu. Tip: You can
setup as shortcut to this function in Object Mode -> Object -> Parent -> right
click "Clear parent from bedrock bone" -> Add Shortcut.

## Mapping of blender objects into mcbones, mccubes and locators
The add-on takes two types of object while creating the models - meshes and
empties. Addon decides what should become an mcbone, mccube or locator
automatically by following the certain set of rules (the order of checking
this rules is the same as in this document):

#### Mapping rules for empties:
1. Empty with "mc_is_bone" property becomes an mcbone.
1. Empty without parents becomes an mcbone
2. Empty with children ("mc_parent" in another object pointing at the empty)
becomes mcbone
3. Every other case (empty with no "mc_is_bone" propety, with parent and
without children) becomes a locator.
#### Mapping rules for meshes:
1. If the mesh has a child defined by custom property ("mc_parent" in another
object) it creates mcbone with one mccube in it.
2. If the mesh has custom property "mc_is_bone" than the object becomes a mcbone with one mccube in it.
3. Mesh with parent and without children becomes a mccube and is added to a
list of mccubes of parent mcbone.
4. In every other case (mesh without parent and without children) becomes a
mcbone with single mccube in it.

Waring: A mesh that becomes mccube can't be animated. If you wan't to animate
a mesh that doesn't have custom children and has custom parent make sure to
add "mc_is_bone" property to it.

## Exporting the models and the animations:
After installation and enabling the add-on there should be an additional tab
called "MC Bedrock exporter" on the right sidebar of 3d-viewport (default key
to open/close the sidebar in Blender is N). Opening this tab reveals four
panels:
- Export bedrock animation
- Export bedrock model
- Set bedrock UVs
- Custom properties
### Export bedrock model
This panel is used to export the model. You need to select all of the objects
that are part of the model before exporting it.  Remember to set the timeline
of the animation to a point in which the model is in its neutral position.
Tip: You can use frame 0 (frame before the animation starts) and add a keyframe
with neutral model position to it.
- The top textfield is used to pick the path to a json file for exporting the
model.
- The "Name" field is the name of the model you want to export.
- "Export model" button exports the model.
### Export bedrock animation
This panel is used to export animations. You need to select all of the objects
that are part of the model to export the animation. If the model uses a rig for
animation you should also select the rig (even though it's not part of the
mcmodel).
- The top textfield is used to pick the path to a json file for exporting the
animation.
- The "Name" field is the name of the animation you want to export.
- The "Loop" checkbox decides if the exported animation should have loop value
set to true.
- anim_time_update - is a value (molang) that goes to anim_time_update property
of minecraft animation. If you leave this empty than the aniation won't use
anim_time_update property.
- "Export animation" button exports the animation.
### Set bedrock UVs
This panel is used to plan the UV mapping of the model. By default all of the
cubes in the model have uv-mapping set to [0, 0]. Use this panel before
exporting the model to get proper UV-mapping. The uv mapping vlaues are stored
on custom properties of the object in `mc_uv`.
- Texture width - the texture width property used for exporting of mcmodel.
- Texture height - the texture height property used for exporting of mcmodel.
If you sent this property to 0 the texture height will be selected
automatically.
- "Move existing mcUv mappings" - this chceckbox decides if the cubes that
already have assigned uv-mapping values can be moved.
- Move blender UV mappings - this checkbox decides if blender objects should
have their UV-mapping moved to match the minecraft model.
- Remove old UV maps. If set to true running the "Set bedrock UV" will remove
old uv mapping from the selected objects (objects in blender can have multiple
uv-maps, you can acces them in "Object data properties").
- Template resolution - Sets the resolution of the template texture.
Setting this to 0 prevents the creation of the template texture. This value
describes how many pixels on the image is represented by one texture_widht or
texture_height unit in model definition. The value of 1 gives the standard
minecraft texture resolution.
- "Set minecraft UVs" button runs the operator which plans the UV-mapping.
### Custom properties
This panel adds easy acces for managing some of the custom properties used by
the plugin to define how to export some parts of the model.
- Toggles mc_mirror - Toggles mc_mirror for selected objects. Adds or removes
mirror property from a cube in minecraft model.
- Set mc_uv_group - sets mc_uv_group for bedrock model. Objects that have the
same width, depth and height and are in the same mc_uv_group are mapped to
the same spot on the texutre.
- Toggle mc_is_bone - Toggles mc_is_bone for selected objects. Setting
mc_is_bone property to 1 ensures that the object will be converted to a mcbone
in minecraft model
- Set mc_inflate - Set the mc_inflate vale for selected objects and change their dimensions to fit the inflate values.


## List of custom object properties used by the plug-in
- mc_parent - points to an parent object in mcmodel.
- mc_uv_group - used to group cubes with same width, depth and height to assign
same uv-mapping to them.
- mc_uv - U and V value of mcmodel uv-mapping.
- mc_is_bone - if exists it marks an object as a mcbone.
- mc_inflate - the inflate value of mc_cube in minecraft model.
