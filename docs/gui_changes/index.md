# GUI Changes
Mcblend adds new panels to Blender GUI:

- _Mcblend_ tab on [sidebar](#sidebar),
- _Mcblend UV groups_ tab in the [Scene Properties](#scene-properties),
- _Mcblend events_ tab in the [Scene Properties](#scene-properties),
- _Mcblend object properties_ in the [Object Properties](#object-properties),
- _Mcblend: Export model_ and _Mcblend: Export animation_ in
  the export menu,
- _Mcblend: Import model_ in the import menu.

## Sidebar
The sidebar gives access to most of the Mcblend functionality. It contains 5
panels:

- [Export bedrock animation](../basic_operators/#exporting-animations),
- [Export bedrock model](../basic_operators/#exporting-models),
- [Set bedrock UVs](../basic_operators/#uv-mapping),
- [Operators](../basic_operators/#modifying-mcblend-properties),
- [Import bedrock model](../basic_operators/#importing-models).

![](../img/mcblend_gui_image.png)

## Scene properties

Scene properties tab has two new panels:

- _Mcblend UV groups_ - used for [creating](../uv_groups) and [customizing](../texture_customization) UV-groups.
- _Mcblend events_ - used for adding events for creating [sound- and particle-effects animations](../animating_effects).


![](../img/uv_groups_panel.png)

## Object properties

Object properties tab has new panel - _Mcblend object properties_.
It lets you view and edit custom object properties used by
[Mcblend operators]((../basic_operators/#modifying-mcblend-properties)).

![](../img/object_properties.png)

- *Export as bone* - whether the object should be always exported as
  independent bone or it can be exported as cube/polymesh and grouped with
  other objects.
- *Mesh type (dropdown list)* - *Cube* or *Poly mesh*. Decides if the object
  should be exported as a cube or polymesh. Objects with non-cuboid shapes must
  be polymesh type or you won't be able to export them.

!!! note

    Polymesh models are still experimental Minecraft feature and they could
    even be removed from Minecraft. Experimental features are not allowed on
    marketplace map so keep that in mind if you're making a map for
    marketplace.

- *UV Group (textfield)* - displays the [UV-group](../uv_groups) name of the
  selected object.
- *Mirror* - the mirror property is used only during the
  [UV-mapping](../basic_operators/#uv-mapping). It affects how to map the faces
  of the object in a same way as Minecraft mirror property of a cube.
- *Inflate* - stores the Minecraft inflate property value of the cube.

!!! note

    Editing the Inflate value through this panel does not change the dimensions
    of the object, but it does change the inflate value in the exported object.
    If you want to inflate/deflate the object you should use the
    inflate operator from the sidebar.