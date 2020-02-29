import bpy
import mathutils
import math
import numpy as np

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp


MINECRAFT_SCALE_FACTOR = 16

# Names for temporary types of objects for the exporter
CUBE, BONE, BOTH = 'CUBE', 'BONE', "BOTH"


#COMMON
def get_local_matrix(
    parent_world_matrix: mathutils.Matrix, child_world_matrix: mathutils.Matrix
) -> mathutils.Matrix:
    '''
    Returns translation matrix of child in relation to parent.
    In space defined by parent translation matrix.
    '''
    return (
        parent_world_matrix.inverted() @ child_world_matrix
    )

def json_vect(arr: tp.Iterable) -> tp.List[float]:
    '''
    Changes the iterable whith numbers into basic python list of floats.
    Values from the original iterable are rounded to the 4th deimal
    digit.
    '''
    return [round(i, 3) for i in arr]

def rotation(
    child_matrix: mathutils.Matrix,
    parent_matrix: tp.Optional[mathutils.Matrix]=None
) -> np.ndarray:
    '''Returns the rotation of mcbone represented by the "obj" object.'''
    def local_rotation(
        child_matrix: mathutils.Matrix, parent_matrix: mathutils.Matrix
    ) -> mathutils.Euler:
        '''
        Reuturns Euler rotation of a child matrix in relation to parent matrix
        '''
        child_matrix = child_matrix.normalized()
        parent_matrix = parent_matrix.normalized()
        return (
            parent_matrix.inverted() @ child_matrix
        ).to_quaternion().to_euler('XZY')

    if parent_matrix is not None:
        result = local_rotation(
            child_matrix, parent_matrix
        )
    else:
        result = child_matrix.to_euler('XZY')
    result = np.array(result)[[0, 2, 1]]
    result = result * np.array([1, -1, 1])
    result = result * 180/math.pi  # math.degrees() for array
    return result


# MODELS
def cube_size(
    obj: bpy_types.Object, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube size based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return (np.array(obj.bound_box[6]) - np.array(obj.bound_box[0]))[[0, 2, 1]]


def cube_position(
    obj: bpy_types.Object, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube position based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(obj.bound_box[0])[[0, 2, 1]]


def pivot(obj: bpy_types.Object) -> np.ndarray:
    '''
    Returns the pivot point. Of a mcbone (or mccube represented by the "obj"
    object.
    '''
    def local_crds(
        parent_matrix: mathutils.Matrix, child_matrix: mathutils.Matrix
    ) -> mathutils.Vector:
        '''Local coordinates of child matrix inside parent matrix'''
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _pivot(obj: bpy_types.Object) -> mathutils.Vector:
        if 'mc_parent' in obj:
            result = local_crds(
                obj['mc_parent'].matrix_world,
                obj.matrix_world
            )
            result += _pivot(obj['mc_parent'])
        else:
            result = obj.matrix_world.to_translation()
        return result

    return np.array(_pivot(obj).xzy)


def to_mc_bone(
    bone: bpy_types.Object, cubes: tp.Optional[tp.List[bpy_types.Object]]=None
) -> tp.Dict:
    '''
    :param bone: the main object that represents the bone.
    :param cubes: the list of objects that represent the cubes that belong to
    the bone. If the "bone" is one of the cubes it should be included on the
    list.

    Returns the dictionary that represents a single mcbone in json file
    of exported model.
    '''
    def _scale(obj: bpy_types.Object) -> np.ndarray:
        '''Scale of a bone'''
        _, _, scale = obj.matrix_world.decompose()
        return np.array(scale.xzy)

    mcbone = {'name': bone.name, 'cubes': []}

    # Code
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name
        b_rot = rotation(bone.matrix_world, bone['mc_parent'].matrix_world)
    else:
        b_rot = rotation(bone.matrix_world)

    b_pivot = pivot(bone) * MINECRAFT_SCALE_FACTOR

    for cube in cubes:
        translation = get_local_matrix(
            bone.matrix_world, cube.matrix_world
        )

        _b_scale = _scale(cube)

        c_size = (
            cube_size(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_pivot = pivot(cube) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            cube_position(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_rot = rotation(cube.matrix_world, bone.matrix_world)

        mcbone['cubes'].append({
            'uv': [0, 0],
            'size': json_vect(c_size),
            'origin': json_vect(c_origin),
            'pivot': json_vect(c_pivot),
            'rotation': json_vect(c_rot)
        })

    mcbone['pivot'] = json_vect(b_pivot)
    mcbone['rotation'] = json_vect(b_rot)
    return mcbone


def get_model_template(model_name: str, mc_bones: tp.List[tp.Dict]) -> tp.Dict:
    '''
    Returns the dictionary that represents JSON file for exporting the model
    '''
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.{model_name}",
                    "texture_width": 1,
                    "texture_height": 1,
                    "visible_bounds_width": 10,
                    "visible_bounds_height": 10,
                    "visible_bounds_offset": [0, 2, 0]
                },
                "bones": mc_bones
            }
        ]
    }


def get_object_properties() -> tp.Dict:
    '''
    Loops through bpy.context.selected_objects and returns a dictionary with
    some properties of selected objects:
     - "mc_obj_type" with value "CUBE" or "BONE" or "BOTH".
     - "mc_children" properties for easy access to reverse relation
       of "mc_parent".

    The properties are returned as dictionary.
    '''
    temporary_properties = defaultdict(
        lambda: {"mc_children": [], "mc_obj_type": None}
    )

    # Objects other than EMPTY and MESH are ignored.
    for obj in bpy.context.selected_objects:
        if obj.type == 'EMPTY' or obj.type == 'MESH':
            if "mc_parent" in obj:
                temporary_properties[
                    obj["mc_parent"].name
                ]["mc_children"].append(obj)

    for obj in bpy.context.selected_objects:
        if obj.type == 'EMPTY':
            temporary_properties[obj.name]['mc_obj_type'] = BONE
        elif obj.type == 'MESH':
            if len(temporary_properties[obj.name]["mc_children"]) > 0:
                temporary_properties[obj.name]['mc_obj_type'] = BOTH
            elif "mc_is_bone" in obj and obj["mc_is_bone"] == 1:
                temporary_properties[obj.name]["mc_obj_type"] = BOTH
            elif "mc_parent" in obj:
                temporary_properties[obj.name]["mc_obj_type"] = CUBE
            else:  # Not connected to anything
                temporary_properties[obj.name]["mc_obj_type"] = BOTH

    return dict(temporary_properties)


# ANIMATIONS
def get_transformations(
    object_properties: tp.Dict
) -> tp.Dict[str, tp.Dict[str, np.ndarray]]:
    # TODO - update doc string (added object_properties property)
    '''
    Loops over bpy.context.selected_objects and returns the dictionary with
    information about transformations of every bone.

    Result is a dictionary with name of the bone as a key and whith another
    dictionary that contains the information about "rotation", "scale" and
    "location" of the bone. The scale is an np.ndarray Euler rotation in
    degrees.
    '''
    transformations = {}
    for obj in bpy.context.selected_objects:
        if (
            obj.name in object_properties and
            object_properties[obj.name]['mc_obj_type'] in [BONE, BOTH]
        ):
            if 'mc_parent' in obj:
                # Calculate translation in parent axis
                location = get_local_matrix(
                    obj['mc_parent'].matrix_world.normalized(),
                    obj.matrix_world.normalized()
                ).to_translation()
                # Add result
                transformations[obj.name] = {
                    'rotation': rotation(
                        obj.matrix_world, obj['mc_parent'].matrix_world
                    ),
                    'scale': (
                        np.array(obj.matrix_world.copy().to_scale()) /
                        np.array(
                            obj['mc_parent'].matrix_world.copy().to_scale()
                        )
                    ),
                    'location': location
                }
            else:
                scale = np.array(obj.matrix_world.copy().to_scale())
                location = np.array(
                    obj.matrix_world.normalized().to_translation()
                )
                transformations[obj.name] = {
                    'rotation': rotation(obj.matrix_world),
                    'scale': scale,
                    'location': location * scale
                }
    return transformations


def get_next_keyframe() -> tp.Optional[int]:
    '''
    Returns the index of next keyframe from selected objects.
    Returns None if there is no more keyframes to chose.
    '''
    curr = bpy.context.scene.frame_current
    next_keyframe = None
    for obj in bpy.context.selected_objects:
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


def to_mc_translation_vectors(
    parent_rot: np.ndarray, child_rot: np.ndarray,
    parent_scale: np.ndarray, child_scale: np.ndarray,
    parent_loc: np.ndarray, child_loc: np.ndarray
) -> tp.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Compares original rotation, scale and translation with new rotation, scale
    and translation of an object to return location, rotation and scale values
    (in this order) that can be used by the dictionary used for exporting the
    animation data to minecraft format.
    '''
    child_scale = child_scale[[0, 2, 1]]
    parent_scale = parent_scale[[0, 2, 1]]
    scale = child_scale / parent_scale
    scale = scale

    loc = child_loc - parent_loc
    loc = np.array(loc) * MINECRAFT_SCALE_FACTOR
    loc = loc[[0, 2, 1]] / parent_scale

    rot = child_rot - parent_rot

    return loc, rot, scale


def get_animation_template(
    name: str, length: int, loop_animation: bool, anim_time_update: str,
    bone_data: tp.Dict[str, tp.Dict[str, tp.List[int]]]
):
    '''
    :param str name: name of the animation
    :param int length: the length of animation (in frames). The FPS vlaue
    is extracted from bpy.context.scene.render.fps.
    :param int loop_animation: Loops the animation
    :param int anim_time_update: Adds anim_time_update property to the
    animation.
    :param tp.Dict[str, tp.Dict[str, tp.List[int]]] bone_data: Dictionary
    filled with dictionaries that describe postition, rotation and scale
    for each frame (uses bone name as a key).

    Returns the tamplate of a dictionary that represents the JSON file with
    minecraft animation.
    '''
    def reduce_property(
        ls: tp.List[tp.Dict]
    ) -> tp.List[tp.Dict]:
        '''
        Removes some of the keyframes from list of keyframes values of
        a property (rotation, location or scale)
        '''
        if len(ls) == 0:
            return []
        last_val = ls[0]['value']
        result = [ls[0]]
        for i in range(1, len(ls)-1):
            curr_val = ls[i]['value']
            next_val = ls[i+1]['value']
            if curr_val != last_val or curr_val != next_val:
                result.append(ls[i])
                last_val = curr_val
        # Add last element unless there is only one (in which case it's
        # already added)
        if len(ls) > 1:
            result.append(ls[-1])
        return result

    # Extract bones data
    bones = {}
    for bone_name, bone in bone_data.items():
        bones[bone_name] = {
            'position': {},
            'rotation': {},
            'scale': {}
        }
        for prop in reduce_property(bone['position']):
            bones[bone_name]['position'][prop['time']] = prop['value']
        for prop in reduce_property(bone['rotation']):
            bones[bone_name]['rotation'][prop['time']] = prop['value']
        for prop in reduce_property(bone['scale']):
            bones[bone_name]['scale'][prop['time']] = prop['value']
    # Returning result
    result = {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{name}": {
                "animation_length": (length-1)/bpy.context.scene.render.fps,
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


def pick_closest_rotation(
    modify: np.ndarray, close_to: np.ndarray
) -> np.ndarray:
    '''
    Takes two numpy.arrays that represent rotation in
    euler rotation mode (using degrees). Modifies the
    values of 'modify' vector to get different representations
    of the same rotation. Picks the vector which is the
    closest to 'close_to' vector (euclidean distance).
    '''
    def _pick_closet_location(
        modify: np.ndarray, close_to: np.ndarray
    ) -> tp.Tuple[float, np.ndarray]:
        choice = modify
        distance = np.linalg.norm(choice - close_to)

        for i in range(3):  # Adds removes 360 to all 3 axis (picks the best)
            arr = np.zeros(3)
            arr[i] = 360
            while choice[i] < close_to[i]:
                new_choice = choice + arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                else:
                    distance, choice = new_distance, new_choice
            while choice[i] > close_to[i]:
                new_choice = choice - arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                else:
                    distance, choice = new_distance, new_choice
        return distance, choice

    distance1, choice1 = _pick_closet_location(modify, close_to)
    distance2, choice2 = _pick_closet_location(  # Counterintuitive but works
        (modify + np.array([180, 180, 180])) * np.array([1, -1, 1]),
        close_to
    )
    if distance2 < distance1:
        return choice2
    else:
        return choice1

