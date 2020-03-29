# Basics

![](../../img/mcblend_gui_image.png)

## GUI
After installation and enabling the add-on there should be an additional tab
called "Mcblend" (number 1 on the image) on the right sidebar of 3d-viewport
(default key to open/close the sidebar in Blender is N). Opening this tab
reveals panels which are used to accesss most of the functionallity of the
addon.

Additionally there is custom operator for parenting the objects for minecraft
model, that you can find in 3D viewport, in `Object -> Parent` menu (number 2
on the image).

## Limitations
Minecraft models for bedrock edition support only cuboids. This means that the
exported model also needs to be created out of cuboids only.
Every meash which is not a cuboid will use its bounding box in process of
exporting the model.Note that a mesh which has one cuboid in it but tilted in relation to the object rotation isn't considered to be a cuboid. 

A good way to avoid mistakes caused by meshes with a wrong shape ist to enable
display of bounding box in object properties in Blender see if object is a
proper cuboid
`Properties -> Object properties -> Viewport display -> Bounds (checkobx)`
(number 3 in the image).

## Custom properties
Mcblend uses custom object properties to store some data about minecraft model
You can view the these porperties in `Object properties -> Custom properties`.

![](../../img/custom_properties.png)
