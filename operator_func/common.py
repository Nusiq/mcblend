import bpy
import mathutils
import math
import numpy as np
from enum import Enum

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp


MINECRAFT_SCALE_FACTOR = 16


class MCObjType(Enum):
    '''
    Used to mark what type of minecraft object should be created from a mesh in
    blender.

    CUBE - is a cube which is a part of a bone.
    BONE - is just a bone without cubes in it.
    BOTH - is a bone with a cube inside.
    '''
    CUBE = 'CUBE'
    BONE = 'BONE'
    BOTH = 'BOTH'


class ObjectMcProperties(tp.NamedTuple):
    '''
    Temporary minecraft-related properties of an object (mesh or empty).
    '''
    mcchildren: tp.Tuple[str]
    mctype: MCObjType


class ObjectMcTransformations(tp.NamedTuple):
    '''
    Temporary properties of transformations of an object (mesh or empty)
    for the minecraft animation. Changes in these values over the frames of the
    animation are used to calculate the values for minecraft animation json.
    '''
    location: np.array
    scale: np.array
    rotation: np.array



def get_vect_json(arr: tp.Iterable) -> tp.List[float]:
    '''
    Changes the iterable whith numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.
    '''
    return [round(i, 3) for i in arr]


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


# TODO - change stop using matrix_world and pass bpy_types.Object instead for
# more consistency in functions of this module.
def get_mcrotation(
    child_matrix: mathutils.Matrix,
    parent_matrix: tp.Optional[mathutils.Matrix]=None
) -> np.ndarray:
    '''
    Returns the rotation of mcbone.
    - child_matrix - the matrix_world of the object that represents the mcbone
    - parent_matrix - optional. the matrix_world of the object that is a
      mcparent (custom parenting) of the object that represents the mcbone.
    '''
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


def get_mcube_size(
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


def get_mccube_position(
    obj: bpy_types.Object, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube position based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(obj.bound_box[0])[[0, 2, 1]]


def get_mcpivot(obj: bpy_types.Object) -> np.ndarray:
    '''
    Returns the pivot point of a mcbone (or mccube) represented by the "obj"
    object.
    '''
    def local_crds(
        parent_matrix: mathutils.Matrix, child_matrix: mathutils.Matrix
    ) -> mathutils.Vector:
        '''Local coordinates of child matrix inside parent matrix'''
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _get_mcpivot(obj: bpy_types.Object) -> mathutils.Vector:
        if 'mc_parent' in obj:
            result = local_crds(
                obj['mc_parent'].matrix_world,
                obj.matrix_world
            )
            result += _get_mcpivot(obj['mc_parent'])
        else:
            result = obj.matrix_world.to_translation()
        return result

    return np.array(_get_mcpivot(obj).xzy)


def get_object_mcproperties(
    context: bpy_types.Context
) -> tp.Dict[str, ObjectMcProperties]:
    '''
    Loops through context.selected_objects and returns a dictionary with custom
    properties of mcobjects. Returned dictionary uses the names of the objects
    as keys and the custom properties as values.
    '''
    tmp_properties: tp.DefaultDict = defaultdict(
        lambda: {"mc_children": [], "mc_obj_type": ""}
    )

    # Objects other than EMPTY and MESH are ignored.
    for obj in context.selected_objects:
        if obj.type == 'EMPTY' or obj.type == 'MESH':
            if "mc_parent" in obj:
                tmp_properties[
                    obj["mc_parent"].name
                ]["mc_children"].append(obj)

    properties: tp.Dict[str, ObjectMcProperties] = {}
    for obj in context.selected_objects:
        tmp_prop = tmp_properties[obj.name]
        if obj.type == 'EMPTY':
            tmp_prop['mc_obj_type'] = MCObjType.BONE
        elif obj.type == 'MESH':
            if len(tmp_properties[obj.name]["mc_children"]) > 0:
                tmp_prop['mc_obj_type'] = MCObjType.BOTH
            elif "mc_is_bone" in obj and obj["mc_is_bone"] == 1:
                tmp_prop["mc_obj_type"] = MCObjType.BOTH
            elif "mc_parent" in obj:
                tmp_prop["mc_obj_type"] = MCObjType.CUBE
            else:  # Not connected to anything
                tmp_prop["mc_obj_type"] = MCObjType.BOTH

        properties[obj.name] = ObjectMcProperties(
            mcchildren = tuple(i.name for i in tmp_prop['mc_children']),  # type: ignore
            mctype = tmp_prop['mc_obj_type']
        )

    return properties


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
