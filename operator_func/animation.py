import bpy
import numpy as np

# Additional imports for mypy
import bpy_types
import typing as tp

from .common import (
    MINECRAFT_SCALE_FACTOR, ObjectMcProperties, ObjectMcTransformations,
    MCObjType, get_local_matrix, get_mcrotation
)

# ANIMATIONS
def get_mcanimation_json(
    context: bpy_types.Context,
    name: str, length: int, loop_animation: bool, anim_time_update: str,
    bone_data: tp.Dict[str, tp.Dict[str, tp.List[tp.Dict]]]
):
    '''
    - name - name of the animation
    - length - the length of animation (in frames). The FPS vlaue is extracted
      from context.scene.render.fps.
    - loop_animation - Loops the animation
    - anim_time_update - Adds anim_time_update property to the animation.
    - bone_data - Dictionary filled with dictionaries that describe postition,
      rotation and scale for each frame (uses bone name as a key).

    Returns a dictionary with animation for minecraft entity. Optimizes
    bone_data to reduce the size of the animation file.
    '''
    def reduce_property(
        context: bpy_types.Context,
        ls: tp.List[tp.Dict]
    ) -> tp.List[tp.Dict]:
        '''
        Removes some of the keyframes from list of keyframes values of
        a property (rotation, location or scale)
        '''
        if len(ls) == 0:
            return []
        last_val = ls[0]['value']
        reduced_property = [ls[0]]
        for i in range(1, len(ls)-1):
            curr_val = ls[i]['value']
            next_val = ls[i+1]['value']
            if curr_val != last_val or curr_val != next_val:
                reduced_property.append(ls[i])
                last_val = curr_val
        # Add last element unless there is only one (in which case it's
        # already added)
        if len(ls) > 1:
            reduced_property.append(ls[-1])
        return reduced_property

    # Extract bones data
    bones: tp.Dict = {}
    for bone_name, bone in bone_data.items():
        bones[bone_name] = {
            'position': {},
            'rotation': {},
            'scale': {}
        }
        for prop in reduce_property(context, bone['position']):
            bones[bone_name]['position'][prop['time']] = prop['value']
        for prop in reduce_property(context, bone['rotation']):
            bones[bone_name]['rotation'][prop['time']] = prop['value']
        for prop in reduce_property(context, bone['scale']):
            bones[bone_name]['scale'][prop['time']] = prop['value']
    # Returning result
    result: tp.Dict = {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{name}": {
                "animation_length": (length-1)/context.scene.render.fps,
                "bones": bones
            }
        }
    }
    data = result["animations"][f"animation.{name}"]
    if loop_animation:
        data['loop'] = True
    if anim_time_update != "":
        data['anim_time_update'] = anim_time_update
    return result


def get_transformations(
    context: bpy_types.Context,
    object_properties: tp.Dict[str, ObjectMcProperties]
) -> tp.Dict[str, ObjectMcTransformations]:
    '''
    Loops over context.selected_objects and returns the dictionary with
    information about transformations of every bone. Uses `object_properties`
    to check if object should be animated (only bones can be animated in
    minecraft)

    Returns a dicionary with name of the object as keys and transformation
    properties as values.
    '''
    transformations:tp.Dict[str, ObjectMcTransformations] = {}
    for obj in context.selected_objects:
        if (
            obj.name in object_properties and
            object_properties[obj.name].mctype in
            [MCObjType.BONE, MCObjType.BOTH]
        ):
            if 'mc_parent' in obj:
                parent = obj['mc_parent']
                # Scale
                scale = (
                    np.array(obj.matrix_world.to_scale()) /
                    np.array(parent.matrix_world.to_scale())
                )[[0, 2, 1]]
                # Locatin
                local_matrix = get_local_matrix(
                    parent.matrix_world.normalized(),
                    obj.matrix_world.normalized()
                )
                location = np.array(local_matrix.to_translation())
                location = location[[0, 2, 1]] * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = get_mcrotation(obj.matrix_world, parent.matrix_world)
            else:
                # Scale
                scale = np.array(obj.matrix_world.to_scale())[[0, 2, 1]]
                # Location
                location = np.array(
                    obj.matrix_world.normalized().to_translation()
                )
                location = location[[0, 2, 1]] * scale * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = get_mcrotation(obj.matrix_world)
            transformations[obj.name] = ObjectMcTransformations(
                location=location, scale=scale, rotation=rotation
            )
    return transformations


def get_mctranslations(
    parent_rot: np.ndarray, child_rot: np.ndarray,
    parent_scale: np.ndarray, child_scale: np.ndarray,
    parent_loc: np.ndarray, child_loc: np.ndarray
) -> tp.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Compares original transformations with new transformations of an object
    to return location, rotation and scale values (in this order) that can be
    used by the dictionary used for exporting the animation data to minecraft
    format.
    '''
    child_scale = child_scale
    parent_scale = parent_scale
    scale = child_scale / parent_scale
    scale = scale

    loc = child_loc - parent_loc
    loc = loc / parent_scale

    rot = child_rot - parent_rot

    return loc, rot, scale


def get_next_keyframe(context: bpy_types.Context) -> tp.Optional[int]:
    '''
    Returns the index of next keyframe from all of selected objects.
    Returns None if there is no more keyframes to chose.
    '''
    curr = context.scene.frame_current
    next_keyframe = None
    for obj in context.selected_objects:
        if (
            obj.animation_data is not None and
            obj.animation_data.action is not None and
            obj.animation_data.action.fcurves is not None
        ):
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.keyframe_points is not None:
                    for kframe_point in fcurve.keyframe_points:
                        time = kframe_point.co[0]
                        if time > curr:
                            if next_keyframe is None:
                                next_keyframe = time
                            else:
                                next_keyframe = min(time, next_keyframe)
    return next_keyframe
