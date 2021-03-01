# Limitations

## Every cube must be a separate Blender object
If you are creating a traditional Minecraft model with all parts made out of
cubes you mast make sure that every cube is an separate object (separate mesh).

You can use the edit mode to rotate, scale and move your cubes to your preference
however, they mast be separated before you export the model
(see *[separate cubes operator](../basic_operators#separate-cubes)*)

If you don't want to be restricted to using only cuboids for your model you can
also mark your objects as [polymesh](../gui_changes#object-properties).

## No wide angles in animations
There must be no more than 180° rotation between two key frames.

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
for each rotation orientation, so one cannot distinguish full rotation from no
rotation (360° == 0°).

Therefore, you cannot use angles greater than 180° between two key frames
because Mcblend will always try to export as short rotation as possible.

!!! note

    A quick fix to this problem is adding additional key frames for wide angle
    rotations.


## No dots in names names
The add-on does not allow the use of names that have periods. Anything after
the first dot in the object name is ignored during the conversion. You can use
dots in the names of the objects that aren't converted to bones of exported 
Minecraft model. The conversion rules are described in the
[conversion rules](../conversion_rules/) section of the user manual.
