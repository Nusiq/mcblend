# Glossary
## Mcbones and mccubes
To avoid confusion minecraft bones and cubes will be called mcbones and mccubes
respectively.

- mcbone - a bone in minecraft model (bones in a rig in blender are called just
bones).
- mccube - a cube in minecraft model (part of a mcbone).

## List of custom object properties used by the plug-in
- mc_parent - points to an parent object in mcmodel.
- mc_uv_group - used to group cubes with same width, depth and height to assign
same uv-mapping to them.
- mc_uv - U and V value of mcmodel uv-mapping.
- mc_is_bone - if exists it marks an object as a mcbone.
- mc_inflate - the inflate value of mc_cube in minecraft model.
