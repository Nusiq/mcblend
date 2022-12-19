# Limitations

Minecraft models and animations have a strict set of limitations. Blender is
is not designed for Minecraft. As a result, there are a few rules that
you have to follow when working with Mcblend.

## Modeling
Every *cube* and *poly_mesh* must be a separate object. The model must have
exactly 1 armature. Cubes and poly_meshes are parented to the bones of the
armature using
[bone parenting](https://docs.blender.org/manual/en/2.93/scene_layout/object/editing/parent.html#bone-parent).

The bones of the armature represent the bones of the
Minecraft model and the objects parented to them represent cubes or
poly_meshes. *Empties* are used as Minecraft's *locators*.

The objects and empties can be parented to different objects (but not to
empties) as long as there is a bone on top of their hierarchy.

If a bone has no parents and children it's ignored during the export. This is
useful because in Blender you sometimes may want to use such bones for inverse
kinematics. Skipping these bones doesn't mean that you loose anything because
the bones without child cubes, locators or poly meshes can't be viewed in
the game anyway.

```{note}
Mcblend provides tools that make following these rules easier.

The *[separate cubes operator](gui/3d_viewport_sidebar.md#mesh-transformations-panel)* can
help you with separating meshes that contain multiple cubes into multiple
objects with properly aligned rotations. This means that you can create
your model in a single mesh and as long as its parts have proper shapes,
it's possible to separate them to a format that can be used by Mcblend.

If you don't want to be restricted to using only cuboids for your model you
can also mark some objects as
[poly_mesh](gui/object_properties.md#object-properties-mesh).
Be aware that the poly_mesh models are still an experimental feature in
Minecraft and they could be removed from the game in the future.
```

<details>
<summary><b>[CLICK] Detailed explanation</b></summary>

Modeling limitations are the outcome of the format of Minecraft's model files.
The code below shows the JSON file of a Minecraft model with some of its parts
replaced with `...`.
```json
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
Minecraft models are made out of bones. Every bone has a list of cubes
and/or a poly_mesh. Every cube and polymesh has its own pivot and rotation.
Mcblend needs to know these values in order to export the model. This means
that you can't just pack everything into a single mesh because a mesh is just a
collection of vertices without concept of rotation. Hence, you need to create
separate meshes for each cube and poly_mesh.

<br/><br/>

The rule of using a single armature per Minecraft model just makes working with
multiple models easier. Older versions of Mcblend used to allow using
hierarchies where some of the bones were represented by empties but such
models were hard to understand and the feature was removed.

</details>
<br/>

## UV mapping

The UV maps of the faces of the *cubes* must be rectangular and the must be
aligned with the orientation of the texture image. They also must be properly
rotated to match the rotations allowed by Minecraft. A proper rotation is
when:

- Front, back, left and right faces have their top and bottom edges aligned
    horizontally (remaining edges are vertical).
- Top and bottom face have their front and back edges aligned horizontally and
    left and right edges aligned vertically.

```{note}
The alignment rules are defined in the local space of the cubes which makes
it hard to understand when you look at the model with rotated cubes but
Mcblend can help you with that. If you're getting warnings in your export
like:
`Cube based on Blender object "Cube": "north" face has invalid UV-mapping. Skipped.`
you can use the [Fix model UV-mapping](gui/3d_viewport_sidebar.md#uv-mapping-panel)
operator. It will rearrange the UVs of selected objects so that they match
the Minecraft rules.
```

<details>
<summary><b>[CLICK] Detailed explanation</b></summary>

There are two types of the UV-mapping in Minecraft per-face UV mapping and
the default UV mapping. The snippets of code below show how they look:

</br></br>

The default UV-mapping:
```
"uv": [0.0, 64.0],
```

</br>

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

</br>

The default UV-mapping isn't very flexible. The size and position of the faces
are based on the size of the cube. The vector passed to the "uv" property
defines the offset. With Mcblend you don't have to worry about the type of
UV-mapping you use. If the faces are arranged in a way that allow saving the
UV in default format Mcblend will do it (because it's more compact). Otherwise
the UV is saved using the second format.

<br/><br/>

Unfortunately the per-face UV mapping is also limited. It can't rotate the UV
by 90 degrees. It uses two vectors to define the mapping of the face - the
"uv" (offset) and the "uv_size". This format lets you flip the rectangle but
not rotate it.

</details>
<br/>

## Animating

There must be no more than 180° of rotation between two key frames,
or the exported animation will look different in Minecraft than in the Blender
preview.

```{note}
A quick fix to this problem is adding additional key frames for wide angle
rotations.
```

<details>
<summary><b>[CLICK] Detailed explanation</b></summary>

This issue is caused by the way Mcblend computes Minecraft's rotations
internally.

<br/><br/>

Blender supports multiple rotation modes and uses different rotation types for
different kinds of objects. For example, bone rotations in armatures use
quaternions, but meshes use Euler angles. Additionally, user can choose
different rotation modes for each object. Minecraft uses Euler angles, but the
axes are set differently.

<br/><br/>

Mcblend can export models and animations regardless of the rotation modes used,
but internally everything is converted to quaternions / translation matrices.
The design decision for the internal use of quaternions was motivated by the
fact that quaternions help avoid some calculation errors.

<br/><br/>

Unfortunately, the quaternion number system has only one unique representation
for each rotation orientation, so you cannot distinguish the full rotation from
no rotation at all (360° == 0°).

<br/><br/>

Therefore, you cannot use angles greater than 180° between two key frames
because Mcblend will always try to export the smallest rotation possible to
the animation.

</details>
<br/>

