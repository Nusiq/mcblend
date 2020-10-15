# Limitations

## Cuboids only
Minecraft Bedrock Edition models must only be made of cuboids (unless you are
using an experimental feature that is not yet supported). You cannot use other
shapes in your model.

Each cube in the model must be a separate mesh. The mesh must be exactly the
same shape as its bounding box. If the model shape is different from the
bounding box, Mcblend may fail on export, and if not, the exported
model will only be an approximation of what you see in the viewport.

!!! note

    The best way to avoid problems with invalid meshes is to always use the
    "Object mode" for editing the model and always scaling the cuboids in their
    local space.

    Additionally, you can enable drawing of an object boundary in:
    `Object properties -> Viewport display -> Bounds`

## No wide angles in animations
There must be no more than 180° rotation between two keyframes.

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

Therefore, you cannot use angles greater than 180° between two keyframes.

!!! note

    A quick fix to this problem is adding additional keyframes for wide
    rotations.


## No dots in names names
The add-on does not allow the use of names that have periods. Anything after
the first dot in the object name is ignored during the conversion. You can use
dots in the names of the objects that aren't converted to bones in exported 
Minecraft model. The conversion rules are described in the
[next](../conversion_rules/) section of the user documentation.
