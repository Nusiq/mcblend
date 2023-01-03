# Limitations

Minecraft models and animations have certain constraints that must be followed. Blender was not designed specifically for Minecraft, so there are a few limitations to be aware of when using Mcblend. This section outlines these limitations and provide guidelines for working within them.


## Modeling
In order to use Mcblend, you must adhere to the following modeling constraints:

- Each cube and polymesh must be a separate object.
- The model must have exactly one armature.
- Cubes and polymeshes must be parented to the bones of the armature using ["bone parenting."](https://docs.blender.org/manual/en/2.93/scene_layout/object/editing/parent.html#bone-parent).
- Bones in the armature represent the bones of the Minecraft model, and the objects parented to them represent cubes or polymeshes.
- Empties can be used as Minecraft's "locators."
- Objects and empties can be parented to other objects (but not to empties) as long as there is a bone at the top of their hierarchy.
- If a bone has no parents or children, it will be ignored during export. This is useful because in Blender, you may sometimes want to use such bones for inverse kinematics.

```{note}
Mcblend provides tools to make it easier to follow these rules. The ["separate cubes operator"](gui/3d_viewport_sidebar.md#mesh-transformations-panel) can help you separate meshes that contain multiple cubes into multiple objects with properly aligned rotations. This means you can create your model in a single mesh and, as long as its parts have proper shapes, you can separate them into a format that can be used by Mcblend.

You can also mark certain objects as ["polymeshes,"](/modeling/cubes_vs_polymeshes) which allows you to use shapes other than cuboids for your model. However, be aware that polymeshes are an experimental feature in Minecraft and may be removed from the game in the future.
```

<details>
<summary><b>[CLICK] Detailed explanation</b></summary>

Modeling limitations are the result of the format of Minecraft's model files. As shown in the code snippet below, a Minecraft model is made up of bones, with each bone containing a list of cubes and/or a single polymesh. Each cube and polymesh has its own pivot and rotation, and Mcblend needs this information in order to export the model correctly. This means that it is not possible to pack everything into a single mesh, as a mesh is simply a collection of vertices without a concept of rotation of its separate parts. Instead, you must create separate meshes for each cube and polymesh.
```
{
    "format_version": "1.16.0",
    "minecraft:geometry": [
        {
            "description": {
                ...
            },
            "bones": [
                {
                    "name": "my_bone",
                    "pivot": [0, 0, 0],
                    "rotation": [90, 0, 0],
                    "locators": {
                        "my_locator": {
                            "offset": [0, 0, 0],
                            "rotation": [-45, 0, 0]
                        }
                    },
                    "cubes": [
                        {
                            "uv": [0.0, 0.0],
                            "size": [32, 32, 32],
                            "origin": [-16, -16, -16],
                            "pivot": [0, 0, 0],
                            "rotation": [-90, 0, 0]
                        },
                        {
                            ...
                        }
                    ],
                    "poly_mesh": {
                        ...
                    }
                },
                {
                    "name": "my_bone2",
                    "parent": "my_bone",
                    ...
                }
            ]
        }
    ]
}
```

The rule of using a single armature per Minecraft model helps to make the mapping between the model in Blender and the model in Minecraft more intuitive and easier to understand. It also simplifies the process of working with multiple models. In earlier versions of Mcblend, it was possible to use hierarchies where some bones were represented by empties, but this made the models confusing and difficult to interpret, so the feature was removed. By enforcing the use of a single armature, it becomes clearer how the various parts of the model in Blender correspond to their counterparts in Minecraft.

</details>
<br/>

## UV mapping

In Minecraft, the UV maps of the faces of cubes must be rectangular and aligned with the orientation of the texture image. They also must be properly rotated to match the rotations allowed by Minecraft. A proper rotation is when:

- The front, back, left, and right faces have their top and bottom edges aligned horizontally, with the remaining edges being vertical.
- The top and bottom faces have their front and back edges aligned horizontally, and their left and right edges aligned vertically.

```{note}
It can be difficult to understand these alignment rules when looking at a model with rotated cubes. However, Mcblend provides the [Fix invalid UV mapping](/texturing_and_uv_mapping/fixing_invalid_uv_mapping) operator to rearrange the UVs of selected objects to match the Minecraft rules. If you see warnings in your export such as:
`Cube based on Blender object "Cube": "north" face has invalid UV mapping. Skipped.`
you can use this operator to fix the UV mapping.

```
<details>

<summary><b>[CLICK] Detailed explanation</b></summary>

There are two types of UV mapping in Minecraft: per-face UV mapping and default UV mapping. The default UV mapping is not very flexible, as the size and position of the faces are based on the size of the cube. The vector passed to the "uv" property defines the offset. With Mcblend, you don't have to worry about the type of UV mapping you use. If the faces are arranged in a way that allows saving the UV in default format, Mcblend will do so (because it is more compact). Otherwise, the UV is saved using the per-face mapping format.

Unfortunately, the per-face UV mapping is also limited. It cannot rotate the UV by 90 degrees. It uses two vectors to define the mapping of the face: the "uv" (offset) and the "uv_size". This format allows for flipping the rectangle, but not rotating it.

Examples of both types of UV mapping in code are shown below:

The default UV mapping:
```
"uv": [0.0, 64.0],
```

The per-face UV mapping

```
"uv": {
    "north": {"uv": [48.0, 32.0], "uv_size": [32.0, -32.0]},
    "east": {"uv": [48.0, 128.0], "uv_size": [32.0, -32.0]},
    "south": {"uv": [48.0, 96.0], "uv_size": [32.0, -32.0]},
    "west": {"uv": [48.0, 64.0], "uv_size": [32.0, -32.0]},
    "up": {"uv": [112.0, 64.0], "uv_size": [-32.0, -32.0]},
    "down": {"uv": [16.0, 32.0], "uv_size": [32.0, 32.0]}
},
```

</details>


## Animating

There is a limitation on the amount of rotation that can occur between two keyframes in an animation created with Mcblend. The maximum amount of rotation allowed is 180°. If the rotation between two keyframes exceeds this amount, the exported animation will not match the preview in Blender.

```{note}
A quick fix for this issue is to add additional keyframes for wide angle rotations.
```



<details>
<summary><b>[CLICK] Detailed explanation</b></summary>

This limitation is a result of the way Mcblend calculates rotations internally.

Blender supports multiple rotation modes and uses different types of rotations for different kinds of objects. For example, bone rotations in armatures use quaternions, while meshes use Euler angles. Additionally, users can choose different rotation modes for each object. Minecraft uses Euler angles, but the axes are set differently.

Mcblend can export models and animations regardless of the rotation modes used, but internally everything is converted to quaternions or translation matrices. The decision to use quaternions internally was made because they help avoid certain calculation errors.

However, the quaternion number system has only one unique representation for each rotation orientation, so it is not possible to distinguish a full rotation (360°) from no rotation (0°). This means that angles greater than 180° between two keyframes cannot be used, as Mcblend will always try to export the smallest possible rotation to the animation.

</details>
<br/>

