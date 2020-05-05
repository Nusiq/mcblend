'''
Functions related to exporting animations.
'''
import typing as tp

import bpy_types
import mathutils

import numpy as np

from .common import (
    MINECRAFT_SCALE_FACTOR, ObjectMcProperties, ObjectMcTransformations,
    MCObjType, get_local_matrix, get_mcrotation, ObjectId
)


class AnimationProperties(tp.NamedTuple):
    '''
    Data class that represents configuration of animation

    # Properties:
    - `name: str` - name of the animation.
    - `length: float` - the length of animation in seconds.
    - `loop_animation: bool` - value of loop property of Minecraft animation.
    - `anim_time_update: str` - value of anim_time_update property of Minecraft
      animation.
    '''
    name: str
    length: float
    loop_animation: bool
    anim_time_update: str


# TODO - rewrite this function
def get_mcanimation_json(
        animation_properties: AnimationProperties,
        bone_data: tp.Dict[ObjectId, tp.Dict[str, tp.List[tp.Dict]]],  # TODO - change to data class
        object_properties: tp.Dict[ObjectId, ObjectMcProperties],
        extend_json: tp.Optional[tp.Dict] = None) -> tp.Dict:
    '''
    Returns a dictionary with animation or edits the `extend_json` dictionary.
    Additionaly removes the unnecessary keyframes to optimise the animation.

    # Arguments:
    - `animation_properties: AnimationProperties` - the properties of the
      animation represented by AnimationProperties object.
    - `bone_data: Dict[ObjectId, Dict[str, List[Dict]]]` - position rotation
      and scale of every bone for every frame.
    - `object_properties: Dict[ObjectId, ObjectMcProperties]` - the properties
      of all of the Minecraft cubes and bones.
    - `extend_json: Optional[Dict]` - A dictionary with with old animation JSON
      file to overwrite. If this parameter is None or has invalid structure a new
      dictionary is created.

    # Returns:
    `Dict` - a dictionary with JSON file with animation.
    '''
    def reduce_property(keyframes: tp.List[tp.Dict]) -> tp.List[tp.Dict]:
        '''
        Removes some of the keyframes from list of keyframes values of
        a property (rotation, location or scale)
        '''
        if len(keyframes) == 0:
            return []
        last_val = keyframes[0]['value']
        reduced_property = [keyframes[0]]
        for i in range(1, len(keyframes)-1):
            curr_val = keyframes[i]['value']
            next_val = keyframes[i+1]['value']
            if curr_val != last_val or curr_val != next_val:
                reduced_property.append(keyframes[i])
                last_val = curr_val
        # Add last element unless there is only one (in which case it's
        # already added)
        if len(keyframes) > 1:
            reduced_property.append(keyframes[-1])
        return reduced_property

    def validate_extend_json(extend_json: tp.Optional[tp.Dict]):
        '''
        Reads content of dictionary and validates if it can be used by
        export_animation(). Returns ture if the anim_dict is valid or false if it's
        not.
        '''
        if not isinstance(extend_json, dict):
            return False
        try:
            return isinstance(extend_json['animations'], dict) # type: ignore
        except (TypeError, LookupError):
            return False

    # Extract bones data
    bones: tp.Dict = {}
    for boneid, bone in bone_data.items():
        bones[object_properties[boneid].name()] = {
            'position': {},
            'rotation': {},
            'scale': {}
        }
        for prop in reduce_property(bone['position']):
            bones[
                object_properties[boneid].name()
            ]['position'][prop['time']] = prop['value']
        for prop in reduce_property(bone['rotation']):
            bones[
                object_properties[boneid].name()
            ]['rotation'][prop['time']] = prop['value']
        for prop in reduce_property(bone['scale']):
            bones[
                object_properties[boneid].name()
            ]['scale'][prop['time']] = prop['value']

    # Returning result
    if extend_json is not None and validate_extend_json(extend_json):
        result = extend_json
    else:
        result = {
            "format_version": "1.8.0",
            "animations": {}
        }
    result["animations"][f"animation.{animation_properties.name}"] = {
        "animation_length": animation_properties.length,
        "bones": bones
    }
    data = result["animations"][f"animation.{animation_properties.name}"]
    if animation_properties.loop_animation:
        data['loop'] = True
    if animation_properties.anim_time_update != "":
        data['anim_time_update'] = animation_properties.anim_time_update
    return result

# TODO - keep transformations in object_properties? Dataclss for output?
def get_transformations(
        object_properties: tp.Dict[ObjectId, ObjectMcProperties]
        ) -> tp.Dict[ObjectId, ObjectMcTransformations]:
    '''
    Loops over object_properties and returns the dictionary with
    information about transformations of every bone.

    # Arguments:
    - `object_properties: Dict[ObjectId, ObjectMcProperties]` - the properties
      of all of the Minecraft cubes and bones.

    # Returns:
    `Dict[ObjectId, ObjectMcTransformations]` - a dictionary with
    transformations for every object.
    '''
    transformations: tp.Dict[ObjectId, ObjectMcTransformations] = {}
    for objid, objprop in object_properties.items():
        if objprop.mctype in [MCObjType.BONE, MCObjType.BOTH]:
            if objprop.mcparent is not None:
                parent_matrix = object_properties[
                    objprop.mcparent
                ].matrix_world()
            else:
                parent_matrix = mathutils.Matrix()
            # Scale
            scale = (
                np.array(objprop.matrix_world().to_scale()) /
                np.array(parent_matrix.to_scale())
            )[[0, 2, 1]]
            # Locatin
            local_matrix = get_local_matrix(
                parent_matrix.normalized(),
                objprop.matrix_world().normalized()
            )
            location = np.array(local_matrix.to_translation())
            location = location[[0, 2, 1]] * MINECRAFT_SCALE_FACTOR
            # Rotation
            rotation = get_mcrotation(
                objprop.matrix_world(), parent_matrix
            )
            transformations[objid] = ObjectMcTransformations(
                location=location, scale=scale, rotation=rotation
            )
    return transformations


# TODO - remove this funciton
def get_mctranslations(
        parent_rot: np.ndarray, child_rot: np.ndarray,
        parent_scale: np.ndarray, child_scale: np.ndarray,
        parent_loc: np.ndarray, child_loc: np.ndarray
        ) -> tp.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Compares original transformation of an object to compare them with the new
    ones to get transformation values for animation.

    # Arguments:
    - `parent_rot: ndarray` - original rotation vector
    - `child_rot: ndarray` - new rotation vector
    - `parent_scale: ndarray` - original scale vector
    - `child_scale: ndarray` - new scale vector
    - `parent_loc: ndarray` - original location vector
    - `child_loc: ndarray` - new location vector

    # Returns:
    `Tuple[ndarray, ndarray, ndarray]` - a tuple with location, rotation and
    scale difference between old and new values. The scale difference is
    calculated by proportion.
    '''
    # Scale
    scale = child_scale / parent_scale

    # Location
    loc = child_loc - parent_loc

    # Rotation
    rot = child_rot - parent_rot

    return loc, rot, scale


def get_next_keyframe(context: bpy_types.Context) -> tp.Optional[int]:
    '''
    Returns the index of next keyframe from all of selected objects.
    Returns None if there is no more keyframes to chose.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.

    # Returns:
    `Optional[int]` - index of the next keyframe or None
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
    if next_keyframe is not None and next_keyframe > context.scene.frame_end:
        return None
    return next_keyframe
