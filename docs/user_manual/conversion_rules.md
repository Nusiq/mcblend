# Conversion rules
Mcblend takes two types of object while creating the models - meshes and
empties. Addon decides what should become an mcbone, mccube or locator
by following the certain set of rules. The rules are cheked in the same order
as the list below.

## Conversion rules for empties:
1. Empty with `mc_is_bone` property becomes an mcbone.
2. Empty without parents becomes an mcbone.
3. Empty with children (`mc_parent` property in another object pointing at the
empty) becomes mcbone.
4. Empty in every other case (empty with no `mc_is_bone` propety, with parent and
without children) becomes a locator.

## Conversion rules for meshes:
1. If the mesh has a child defined by custom property (`mc_parent` in another
object) it creates mcbone with one mccube in it.
2. If the mesh has custom property `mc_is_bone` than the object becomes a
mcbone with one mccube in it.
3. Mesh with parent and without children becomes a mccube and is added to a
list of mccubes of parent mcbone.
4. In every other case (mesh without parent and without children) becomes a
mcbone with single mccube in it.

Remember that mccubes can't be animated. If you wan't to animate a mesh that
doesn't have custom children and has custom parent make sure to add
`mc_is_bone` property to it.
