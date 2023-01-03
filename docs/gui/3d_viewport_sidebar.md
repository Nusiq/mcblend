# 3D viewport sidebar

![](/img/gui/sidebar.png)

The 3D viewport sidebar includes a new `Mcblend` section, which has two panels. One panel contains buttons with commonly used functions, while the other panel is for resource pack integration. You can open the sidebar by pressing `N` while hovering over the 3D viewport if you're using the default shourtcuts.

![](/img/gui/sidebar_only.png)

## Operators
### UV mapping panel
- `Fix invalid UV mapping` - operator used to fix invalid UV mapping of the model's cuboids. All faces of the cuboids in the Minecraft model must be rectangular and have a certain rotation. This operator ensures that these conditions are true.
- `Set the UV group` - adds the selected objects to one of the existing UV groups.
- `Clear UV group` - It removes selected objects from UV groups.

### Mesh Transformations panel
- `Inflate` - Inflates the selected object using Minecraft's inflate property. Running this operator opens a panel in the bottom left corner of the 3D viewport. You can use this panel to adjust the `inflate` value.
- `Separate and align cubes` - Detects cubes grouped in a single mesh and splits them into separate objects. Unlike the vanilla Blender operator (`Mesh -> Separate`), the `Separate and align cubes` operator from Mcblend is designed for working with cuboids and can detect their rotations.
- `Prepare physics simulation` - Automatically creates objects, which can be used for physics simulation.

## Resurce Pack panel
The Resource Pack panel in Mcblend allows you to connect a resource pack to your project. Once you open Blender, you will see a single button called `Load Resource Pack`. This button loads information about the entities and attachable items that are available for import.

After loading the resource pack, additional GUI elements will appear:
- The top dropdown list allows you to select whether you want to import an entity or a model of an attachable item.
- Below the dropdown list, there is a text box that allows you to select the item or entity you want to import.
- At the bottom of the panel, additional options will appear, allowing you to select textures, materials, and models. These options depend on the properties of the render controllers of the thing you want to import.
- The `Import from project` button allows you to import selected items to the project.

You can use the `Unload Resource Pack` button to unload the currently loaded resource pack. Note that the data about the resource pack is not saved in the project file, so you will have to load it every time you open the project.
