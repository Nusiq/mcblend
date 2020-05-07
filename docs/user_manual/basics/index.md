# Basics
## GUI

![](../../img/mcblend_gui_image.png)

After installation and enabling the add-on there should be an additional tab
called "Mcblend" on the right side of 3d-viewport (default key to open/close
the sidebar in Blender is N). Opening this tab reveals panels that are used
to access most of the functionality of the addon. Every panel is described
further in the user manual in [panels](../panels/) section.

Additionally, you can find some new options in the `File -> Export` and
`File -> Import` menus.

## Limitations

### Cuboids only
Minecraft bedrock edition models support only cuboids (unless you use an
experimental feature which is not supported yet). You cannot use other
shapes for your model. Mcblend uses bounding boxes to create cuboids for
the exported model.

!!! note

    The best way to avoid problems with invalid meshes is to always use
    blenders "Object mode" for editing the model. Additionally you can enable
    drawing the bounding box in object
    `Object properties -> Viewport display -> Bounds`

### Wide angles in rotations
Blender supports multiple rotation modes and uses different types of rotation
for different kinds of objects. For example rotations of bones in armatures
use quaternions but meshes use Euler (XYZ) angles. Additionally users can
choose to use different rotation modes for each object. Minecraft uses Euler
angles but the axes are set up differently than in Blender so there is no
direct way to use the Minecraft coordinates system in Blender.

Mcblend can export models and animations regardless of used rotation modes.
Internally everything is converted into quaternions and then into Minecraft
coordinate system when it's needed. The design choice of using quaternions
internally was motivated by the fact that quaternions help avoiding some
computation errors. Unfortunately, Quaternions are number system which has
unique representation for every rotation so you can't distinguish full turn
from no turn at all.

The consequence of choosing quaternions is that it's impossible to have
rotation wider than 180 degrees between two keyframes. When an animation is
exported Mcblend translates quaternions into Euler angles and picks the
rotation which requires as little movement as possible to end up in a new pose.

!!! note

    A quick fix to this problem is adding additional keyframes for rotations
    that don't look right.


### Names
The addon does not allow the usage of names that have dots in it. Everything
after the first dot in the name of the object is ignored during the conversion.
You can use dots in the names of the objects which aren't converted into bones
for the Minecraft model. Conversion rules are described in the
[next](../conversion_rules/) section of the user manual.

## Custom properties
Mcblend uses custom object properties to store some data about the Minecraft
model:

- `mc_uv_group` - used to group cubes with the same width, depth and height to
  assign same UV-mapping to them.
- `mc_uv` - U and V value of Minecraft UV-mapping.
- `mc_is_bone` - marks an object as a Minecraft bone.
- `mc_inflate` - the "inflate" value of cube in the Minecraft model.
- `mc_mirror` - marks that the object has the "mirror" property set to true.

You can view these properties in `Object properties -> Custom properties`

![](../../img/custom_properties.png)
