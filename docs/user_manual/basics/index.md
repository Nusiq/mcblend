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
Minecraft bedrock edition models support only cuboids. You cannot use other
shapes for your model. Mcblend uses bounding boxes to create cuboids for
the exported model.

!!! note

    The best way to avoid problems with invalid meshes is to always use
    blenders "Object mode" for editing the model. Additionally you can enable
    drawing the bounding box in object
    `Object properties -> Viewport display -> Bounds`

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
