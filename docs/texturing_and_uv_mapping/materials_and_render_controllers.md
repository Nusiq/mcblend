# Materials and Render Controllers

In Mcblend, render controllers control which bones of a model use which materials and textures. You can configure the render controllers of the model by selecting an armature and opening the `Mcblend: Render Controllers` panel in the `Object properties`. These render controllers are used during the process of [automatic UV mapping](/texturing_and_uv_mapping/automatic_uv_mapping), and changes to them can be seen by running the `Automatic UV Mapping` operator.

![](/img/texturing_and_uv_mapping/render_controllers_settings.png)

Render controllers in Mcblend are simply tools for creating Blender materials. You can viewed these materials in the `Shading` workspace.

![](/img/texturing_and_uv_mapping/render_controller_shading_workspace.png)

If one bone is displayed by multiple render controllers, their properties will be stacked on top of each other in the same way as they would be in Minecraft for a model with multiple render controllers displaying the same bone. The star patterns in Mcblend render controllers work in the same way as the patterns in Minecraft for matching the names of bones.

There are six materials supported by Mcblend that can be used to configure render controllers:

- `entity`: imitates the entity material, with no emissive properties, complete opacity, and no backface culling.
- `entity_emissive`: uses the alpha channel for emissive properties, complete opacity, and no backface culling.
- `entity_alphablend`: no emissive properties, uses the alpha channel, and has backface culling.
- `entity_alphatest_one_sided`: no emissive properties, backface culling, and parts of the model below 50% transparency are invisible, while the rest is opaque.
- `entity_alphatest`: no emissive properties, parts of the model below 50% transparency are completely transparent, the rest is opaque, and there is no backface culling.

Mcblend also recognizes some other materials used in Minecraft when their names are inserted into the text field, but these are simply aliases for the materials listed above.

The emissive properties of a texture can be seen by lowering the `Strength of the studiolight` while viewing the model in `Material Preview` mode in the viewport shading. The image below shows an emissive material and its texture.

![](/img/texturing_and_uv_mapping/render_controller_view_emissive.png)
