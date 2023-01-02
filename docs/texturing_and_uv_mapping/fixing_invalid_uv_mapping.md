# Fixing Invalid UV Mapping

![](/img/texturing_and_uv_mapping/fix_invalid_uv_button.png)

The `Fix invalid UV mapping` operator is a tool for fixing rotated rectangles in the UV maps of a model. In Minecraft, there are two types of UV mapping for cubes: default and per-face. Mcblend automatically selects the appropriate mapping mode, so you don't have to worry about it while working with the model.


The per-face UV mapping is more flexible, as it allows you to set the UV map of each face of the cube separately. However, it is still quite limited. Internally, it saves the UV information as two vectors: one representing the UV coordinates on the texture, and the other representing the size of the rectangle on the texture to be mapped onto the face of the cube. This format allows for mirroring the cube along the X and Y axes, but does not allow for rotating it by 90 degrees.

*The image below shows a texture with the letter "F" on it and its possible transformations achieved through mirroring. The second image depicts a rotated "F" which cannot be achieved by mirroring alone.*

![](/img/texturing_and_uv_mapping/invalid_uv_illustration_1.png)

![](/img/texturing_and_uv_mapping/invalid_uv_illustration_2.png)

The Fix invalid UV mapping operator is used to fix rotated rectangles in the UV maps. If a cube in the model has an invalid UV map and you try to export it, Mcblend will do so, but it will also print a warning message about the invalid UV map and will not include the UV map information in the cube.

![](/img/texturing_and_uv_mapping/invalid_uv_warning_message.png)

To fix invalid UV maps on your model, select the armature and use the `Fix invalid UV mapping` button in the 3D viewport sidebar under the `Mcblend` tab. This will fix any invalid UV maps for all cubes in the model.