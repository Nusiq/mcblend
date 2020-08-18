# Panels
## Custom properties panel

This panel adds easy access for managing some of the custom properties used by
the plugin.

![](../../img/custom_properties_panel.png)

__Usage__

- **Toggles mc_mirror** - Toggles `mc_mirror` property for selected object.
  Objects that have `mc_mirror` property will have different UV mapping
  than the objects without it when you run the `Set bedrock UVs` operator.
- **Set mc_uv_group** - Groups selected object together which affects the
  UV-mapping. Object assigned to the same `mc_uv_group` is mapped to the same
  spot on the texture if they have the same dimensions.

!!! note

    Sometimes when you want to get really compact texture its good to select
    all of the abject and assign them to the same mc_uv_group before running
    the `Set bedrock UVs` operator. The cubes with the same shape will get
    the same UV (for example if you have symetrical humanoid model than its
    left and right hand will be mapped to the same UV texture space).
- **Toggle mc_is_bone** - Toggles `mc_is_bone` property for selected objects.
  object with this property are always exported as bones in the Minecraft
  model. Mcblend usually tries to export most of the meshes as cubes and group
  them together in some parent object which will become a bone. If you want to
  mark certain cube as an independent bone than you need to use `mc_is_bone`
  property.

!!! note

    The best way of using Mcblend is to have one rig for the model parenting
    the meshes to bones of that rig. This allows you to take the advantage
    of useful features like inverse kinematics and also creates a model in
    which its really easy to distinguish which blender object becames what
    in minecraft model. That is - bones will be translated into minecraft
    bones and meshes into cubes. If you add some empties without children
    objects they will become the locators.
- **Set mc_inflate** - Set the `mc_inflate` vale for selected objects. This is
  equivalent to setting the inflate value in the Minecraft model. Running this
  operator opens a panel in the bottom left corner of the 3D viewport. You
  can use this panel to adjust the "inflate" value.

![](../../img/set_mc_inflate_redo_panel.png)

- **Round dimensions** - Rounds the dimensions of the object to integers.
  This operator is useful for aviding problems with UV-mapping.

!!! note

    Its a good habit to always run this operator before exporting the model.
    Models with cubes with non-integer sizes ussualy have issues with UV
    mapping and don't look good. If you want to so some slight tweaks to the
    size of a cube you should use the `Set mc_inflate` operator.

## Set bedrock UVs panel

This panel is used for creating UV-mapping for the model and generating
template textures.

![](../../img/set_bedrock_uvs_panel.png)

__Usage__

To perform the UV-mapping fill in the form and press "Set Minecraft
UVs"

- **Texture width** - the texture width property of the Minecraft model.
- **Texture height** - the texture height property of the Minecraft model.
  If you sent this property to 0 the texture height will be selected
  automatically to fit all textures as tight as possible.
- **Template resolution** - Sets the resolution of the template texture. If you
  set this to 0 then the template texture won't be created. This value
  describes how many pixels on the image is represented by one texture_widht or
  texture_height unit in the model definition. The value 1 gives the standard
  Minecraft texture resolution. Higher values can be used to create "HD"
  textures.


!!! note

    After generating the UV mapping you can still go to the UV editor and
    move everything to your liking. This operator tries to layout the
    UVs of the selected objects on the texture space using the basic
    non-per-face minecraft UV-mapping. If you move the UV in such way that it
    will be impossible to map it in standard minecraft UV-mapping way than
    mcblend will detect that and use per-face UV mapping. Also if you manually
    arrange the shape of the UV to per-face UV-mapping shape than Mcblend will
    detect that and export the model in "minecrafty" way of mapping the UV.
    Don't move individual vertices of the faces on the UV unless you know what
    you're doing. The faces on the UV must remain rectangles or the UV of the
    exported model may have some unexpected shapes.


## Export bedrock model panel

This panel is used for exporting the models. You can set here the name
and visible bounds of the model. Exported model will automatically add
the `geometry.` prefix so you don't need to do that.

![](../../img/export_model_panel.png)

__Usage__

1. Select all of the objects that you want to export.
2. Insert the name of the model.
3. Press the "Export model" button.

## Export bedrock animation panel

This panel is used for exporting animations.

![](../../img/export_animation_panel.png)

__Usage__

1. Select all of the objects to export.
2. Fill in the form with the information about the animation.
3. Press the "Export animation" button.

- **Name** - the name of the animation.
- **Loop** - if true than the loop property of the animation is also set
  to true.
- **Current frame only** - instead of exporting animation exports the
  current frame as looped "pose animation".
- **anim_time_update** - this is copied to "anim_time_update" property
  of the minecraft animtion. If you leave this blank the the animation
  won't use the anim_time_update property.

!!! note

    The time of the animation is determined by the time of animation
    that you can set in the timeline. The animations should always start
    at frame 1. Frame 0 should have the model in the reset pose.

## Import bedrock model panel

This panel is used for importing bedrock models from JSON files.

![](../../img/import_model_panel.png)

__Usage__

Press the button and use file explorer to find the model you want to import.
There is additional property in the file explorer which allows you to specify
the name of the geometry you want to import. Only geometries with `geometry.`
prefix in the name are supported. You don't have to write the prefix (it's
added automatically to the name). If you leave this field empty only the
first model from the list of geometries will be imported.

The "Replace bones with empties" changes the way of importing the model.
If check the box the imported model will use empties instead of armature
and bones. Both ways of importing model represent the same thing in
minecraft according to the [conversion rules](../conversion_rules/).

![](../../img/import_model_file_explorer.png)