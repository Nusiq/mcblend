# Object properties

![](/img/gui/object_properties_bone.png)
![](/img/gui/object_properties_cube.png)

## Object Properties (mesh)

This is the panel visible when opening the `Object Properties` when the active object is a mesh.

(mcblend-object-properties)=
### Mcblend: Object properties

![](/img/gui/object_properties_mesh.png)

- `Mesh type` - a dropdown list that lets you select between `Cube` or `Poly mesh`. Decides if the object should be exported as a cube or polymesh.
- `UV Group` (textfield) - displays the UV group name of the selected object.
- `Mirror` - the mirror property is used only during the UV mapping. It affects the mapping of the object's faces in the same way as Minecraft's mirror property of a cube.
- `Inflate` - stores the Minecraft's inflate property value of the cube.
- `Min UV bound` - this property is used during automatic UV mapping. It defines the minimal space on the texture used for a cube. If a cube has width, height or depth lower than one unit of length, this property can be used to make sure that every face will get some space on the texture.

## Object properties (armature)
This is the panel visible when opening the `Object Properties` when the active object is an armature.

### Mcblend: Model properties

![](/img/gui/object_properties_armature_model_properties.png)

This panel has some of the basic properties of the Minecraft model like the width and height of visible bounds (they have the same names as in the Minecraft model) and some properties used for texture generation.

- `Model origin` - allows you to select whether the transformations of the bones and cubes in the exported model should be relative to the armature of the model or to the world origin.
- `Name` - the name of the model (excluding the `geometry.` prefix).
- `Visible bounds width` - the width of the visible bounds of the model.
- `Visible bounds height` - the height of the visible bounds of the model.
- `Visible bounds offset` - the offset of the visible bounds of the model.
- `Texture width` - the width of the texture used for the model.
- `Texture height` - the height of the texture used for the model.
- `Allow texture expanding` - allows changing the texture width and height during automatic UV mapping.
- `Generate Texture` - a checkbox that decides whether the texture should be generated during automatic UV mapping or not.
- `Template resolution` defines the size of the texture. The real resolution of the generated texture image is equal to texture width and height multiplied by texture resolution.
- `Automatic UV mapping` - a button that triggers the automatic UV mapping.

### Mcblend: Render Controllers

![](/img/gui/object_properties_armature_render_controllers.png)

The Materials panel allows you to quickly create materials that are similar to those found in Minecraft. To do this, you can add multiple render controllers to your model. Each render controller can only have one texture, as multitexture materials are currently not supported. However, a render controller can have multiple Minecraft materials, which can be assigned using name patterns in the same way as you would in Minecraft.

Once you've set up your render controller, you can use the `Apply materials` button to automatically create the materials for preview in Blender. This will help you get a better sense of how your model will look in Minecraft.

(mcblend-object-properties-animations)=
### Mcblend: Animations

![](/img/gui/object_properties_armature_animations.png)

The `Mcblend: Animations panel` allows you to easily switch between animations in your project. These animations are represented as NLA tracks on the armature, with additional data attached to them. Selecting a different animation in the panel will also switch the active NLA track.

- The `New animation` button creates a new animation. You can't use this operator while editing an action of the armature. If you want to create a new action, you need to stash the other action first.
- The `Remove animation` button removes the currently active animation.
- The `Select animation` dropdown list lets you select the animation to edit.
- The `Name` field sets the name of the animation.
- The `Skip rest poses` checkbox enables animation export optimization. If enabled, the keyframes that don't affect the armature (because they are the rest poses) are skipped in the exported file. In most cases, it's recommended to enable this option.
- The `Export as pose` checkbox, if enabled, causes the exported animation to contain only one looped frame.
- The `Override previous animation` field directly translates to the override_previous_animation property of the Minecraft animation. It doesn't affect how the animation is rendered in Blender.
- The `Loop` field directly translates to the loop property of the Minecraft animation file. There are three options: `true`, `false`, and `hold_on_last_frame`.
- The `Anim Time Update` field directly translates to the anim_time_update property of the Minecraft animation file. You should either leave it empty (if you don't want to have anim_time_update in your animation) or put a Molang expression in it. It doesn't affect the animation in Mcblend because Mcblend doesn't support Molang.
- The `Interpolation mode` field directly translates to the interpolation mode of the Minecraft animation file. There are four options: `linear`, `smooth`, `step`, and `auto`.
- The `Frame start` field indicates the first frame of the animation. It tells Mcblend where the animation starts.
- The `Frame end` field indicates the last frame of the animation. It tells Mcblend where the animation ends.

## Object properties (bone of armature)

### Mcblend: Bone properties

![](/img/gui/object_properties_armature_bone_properties.png)

This is the panel visible when opening the `Object Properties` when the active object is a bone in a `Pose Mode`.

- `Bone name` - This displays the name of the currently selected bone. You can also use it to rename the bone.
- `Binding` - This property corresponds to Minecraft's binding property. It is useful for creating models of attachables, but does not affect the model in Blender.
