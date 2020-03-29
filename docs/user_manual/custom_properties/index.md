# Custom properties - panel

This panel adds easy acces for managing some of the custom properties used by
the plugin.

![](../../img/custom_properties_panel.png)

## Usage
- **Toggles mc_mirror** - Toggles `mc_mirror` property for selected object.
Objects that has `mc_mirror` property creates mccubes with mirror value set to
true.
- **Set mc_uv_group** - Groups selected object together to affect the
UV-mapping. If two objects have the same dimensions and same `mc_uv_group`
they get the same UV during the uv-mapping.
- **Toggle mc_is_bone** - Toggles `mc_is_bone` property for selected objects.
Adding this property to an object indicates that the object should be exported
to as a separate bone in minecraft model.
- **Set mc_inflate** - Set the `mc_inflate` vale for selected objects.
`mc_inflate` is translated to the inflate value of a mccube in minecraft model.
