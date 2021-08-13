# Conversion rules
There are no directly equivalent objects in Blender models to Minecraft models.
Mcblend uses a set of rules to decide which parts of the model
should be turned into bone, locator or cube.

1. Every model must have an armature (many properties of the model are
   saved in the armature object).
2. The bones of the armature are converted into the bones of the Minecraft model
   unless they don't have any children or parents. This rule helps avoid
   exporting bones used for inverse kinematics.
3. The child objects (meshes) of the bones are converted into cubes or polymesh
   (you can use the [mesh type](../gui#object-properties) property to
   decide whether the object is exported as a polymesh or a cube). Mcblend uses
   "Bone" parenting mode. You can set a bone to be a parent of an object while
   you're in "Pose mode" by selecting the child object in outliner, and then
   selecting the bone and pressing `CTRL+P`. In the context menu select the
   "Bone" option.
4. The empties are translated into locators. They cannot have child objects.
   You can parent the empty to a bone in exactly the same way as described in
   point 3.
5. You don't have to parent the cuboids directly to bones. You can parent them
   to each other, as long as one of them is parented to a bone.

!!! note
    The best way to learn what kinds of object are converted to what is trial
    and error.
