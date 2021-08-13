# Limitations

## Every cube must be a separate Blender object
If you are creating a traditional Minecraft model with all parts made out of
cuboids, you must make sure that every cuboid is a separate object (separate mesh).

You can use edit mode to rotate, scale and move your cuboids to your preference,
however, they must be separated before you export the model
(see *[separate cubes operator](../gui/#mesh-transformations-panel)*)

If you don't want to be restricted to using only cuboids for your model you can
also mark your objects as [polymesh](../gui#object-properties).
Be aware that the polymesh models are still an experimental feature in
Minecraft and they could be removed in the future.

## No wide angles in animations
There must be no more than 180° of rotation between two key frames, or the exported
animation will look different in Minecraft than in the preview in Blender.

This issue is caused by the way Mcblend computes Minecraft's rotations
internally.

Blender supports multiple rotation modes and uses different rotation types for
different kinds of objects. For example, bone rotations in armatures use
quaternions, but meshes use Euler angles. Additionally, users can choose
different rotation modes for each object. Minecraft uses Euler angles, but the
axes are set differently.

Mcblend can export models and animations regardless of the rotation modes used,
but internally everything is converted to quaternions / translation matrices.
The design decision for the internal use of quaternions was motivated by the
fact that quaternions help avoid some calculation errors.

Unfortunately, the quaternion number system has only one unique representation
for each rotation orientation, so one cannot distinguish the full rotation from no
rotation at all (360° == 0°).

Therefore, you cannot use angles greater than 180° between two key frames
because Mcblend will always try to export the smallest rotation possible.

!!! note

    A quick fix to this problem is adding additional key frames for wide angle
    rotations.


## Every model must have an armature
Blender has a lot of features. Way more than the Minecraft models support.
Therfore there is no way of translating everything to Minecraft format. Mcblend
has a set of [conversion rules](../conversion_rules/) which define what
objects are converted to what. The TL;DR version is: *bones of armature
are translated to bones, meshes are translated to cubes or polymesh and
empties are translated to locators.* You can edit multiple objects at once
with Mcblend. Every armature can be exported as a Minecraft model. The parent
rules decide which mesh belongs to what mode.

