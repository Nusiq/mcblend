# Set bedrock UVs - panel

This panel is used for creating UV-mapping for the model and generating
template textures.

![](../../img/set_bedrock_uvs_panel.png)

## Usage
By default all of the cubes in the model have the [0, 0] uv-mapping.
The uv mapping vlaues of each object are stored in `mc_uv` custom property.

To perform the uv-mapping set the values in the form and press "Set minecraft
UVs"

- **Texture width** - the texture width property used for exporting of mcmodel.
- **Texture height** - the texture height property used for exporting of mcmodel.
If you sent this property to 0 the texture height will be selected
automatically.
- **Move existing mcUv mappings** - this chceckbox decides if the cubes that
already have assigned uv-mapping values can be moved.
- **Move blender UV mappings** - this checkbox decides if blender objects
should have their UV-mapping moved to match the minecraft model.
- **Remove old UV maps** - objects in blender can have multiple but only one of
them is visible uv-maps. Setting the value of this checkbox to true makes sure
that old uv-maps are removed when the new one is created.
- **Template resolution** - Sets the resolution of the template texture. If you
set this to 0 than the template texture won't be created. This value
describes how many pixels on the image is represented by one texture_widht or
texture_height unit in model definition. The value 1 gives the standard
minecraft texture resolution. Higher values can be used to create "HD"
textures.
- **Set minecraft UVs** button runs the operator which plans the UV-mapping and
optionally creates the template texture.
