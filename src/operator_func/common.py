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
    LOCATOR = 'LOCATOR'


class ObjectId(tp.NamedTuple):
    '''
    Unique ID of a mesh, empty or a bone.
    
    For meshes and empties it's armature_name is just an empty string and the
    name is the name of the object.

    For bones the ID uses both the name (name of the bone) and armature name
    which is the name of the armature containing the bone.
    '''
    name: str
    armature_name: str


class ObjectMcProperties(object):
    '''
    Wrapper class for the objects used by the addon to create some parts of
    the minecraft model. This class can be used to containg bpy_types.Object
    and bones from the armature to provide for them similar functionallity.
    '''
    def __init__(
        self, thisobj: bpy_types.Object, mcparent: tp.Optional[ObjectId],
        mcchildren: tp.Tuple[ObjectId], mctype: MCObjType
    ):
        self.thisobj: bpy_types.Object = thisobj
        self.mcparent: tp.Optional[ObjectId] = mcparent
        self.mcchildren: tp.Tuple[ObjectId] = mcchildren
        self.mctype: MCObjType = mctype

    def clear_uv_layers(self):
        '''Clears the uv layers from the object'''
        # TODO - do nothing when the object is bone
        while len(self.thisobj.data.uv_layers) > 0:
            self.thisobj.data.uv_layers.remove(
                self.thisobj.data.uv_layers[0]
            )

    def set_mc_uv(self, uv: tp.Tuple[int, int]):
        '''Sets the mc_uv property of the cube'''
        # TODO - raise exception when the object is not CUBE or BOTH
        self.thisobj['mc_uv'] = uv

    def get_mc_uv(self) -> tp.Tuple[int, int]:
        '''Returns the mc_uv property of the object'''
        # TODO - return none if the object is not CUBE or BOTH
        return tuple(self.thisobj['mc_uv'])  # type: ignore

    def has_uv(self):
        '''Returns true if the object has mc_uv property'''
        # TODO - return false when object is not a CUBE or BOTH
        return 'mc_uv' in self.thisobj

    def has_mc_inflate(self) -> bool:
        '''Returns true if the object has the mc_inflate property'''
        # TODO - return false when object is not a CUBE or BOTH
        return 'mc_inflate' in self.thisobj

    def get_mc_inflate(self) -> float:
        '''Returns the value of mc_inflate property of the object'''
        # TODO - raise exception when the object is not a CUBE or BOTH
        return self.thisobj['mc_inflate']

    def has_mc_mirror(self) -> bool:
        '''Returns true if the object has mc_mirror object'''
        return 'mc_mirror' in self.thisobj

    def get_mc_mirror(self) -> int:
        '''Returns the value of mc_mirror property of the object'''
        # TODO - this shouldnt be used. has_mc_mirror is enough
        return self.thisobj['mc_mirror']

    def has_mc_uv_group(self) -> bool:
        # TODO - raise exception when the object is not a CUBE or BOTH
        return 'mc_uv_group' in self.thisobj

    def get_mc_uv_group(self) -> str:
        '''Returns the value of mc_uv_group property of the object'''
        # TODO - raise exception when the object is not a CUBE or BOTH
        return self.thisobj['mc_uv_group']

    def data_polygons(self) -> tp.Any:
        '''Returns the polygons (faces) of the object'''
        # TODO - raise exception when the object is not a CUBE or BOTH
        return self.thisobj.data.polygons

    def data_vertices(self) -> tp.Any:
        '''Returns the vertices of the object'''
        # TODO - raise exception when the object is not a CUBE or BOTH
        return self.thisobj.data.vertices

    def data_uv_layers_active_data(self) -> tp.Any:
        '''Return the data of active uv-layers of the object'''
        # TODO - raise exception when the object is not CUBE or BOTH
        return self.thisobj.data.uv_layers.active.data

    def data_uv_layers_new(self):
        '''Adds UV-layer to an object.'''
        # TODO - raise exception when the object is not CUBE or BOTH
        self.thisobj.data.uv_layers.new()

    def name(self) -> str:
        '''Returns the name of the object'''
        # TODO - resolve name conflicts when the object is bone
        return self.thisobj.name

    def type(self) -> str:
        '''Returns the type of the object.'''
        # TODO - return BONE when the object is bone
        return self.thisobj.type

    def bound_box(self) -> tp.Any:  # Undefined type?
        return self.thisobj.bound_box

    def matrix_world(self) -> mathutils.Matrix:
        return self.thisobj.matrix_world.copy()



class ObjectMcTransformations(tp.NamedTuple):
    '''
    Temporary properties of transformations of an object (mesh or empty)
    for the minecraft animation. Changes in these values over the frames of the
    animation are used to calculate the values for minecraft animation json.
    '''
    location: np.array
    scale: np.array
    rotation: np.array


class McConvertibleType(Enum):
    '''
    Type of an object in blender that can be converted into something in
    minecraft model.
    '''
    BONE = 'BONE'
    MESH = 'MESH'
    EMPTY = 'EMPTY'


def get_vect_json(arr: tp.Iterable) -> tp.List[float]:
    '''
    Changes the iterable whith numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.
    '''
    result = [round(i, 3) for i in arr]
    for i in range(len(result)):
        if result[i] == -0.0:
            result[i] = 0.0
    return result


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
    objprop: ObjectMcProperties
) -> np.ndarray:
    '''
    Returns cube size based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
    bound_box = objprop.bound_box()
    return (np.array(bound_box[6]) - np.array(bound_box[0]))[[0, 2, 1]]


def get_mccube_position(
    objprop: ObjectMcProperties, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube position based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    # TODO - is this unused code important?
    # bound_box = obj.bound_box
    # bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(objprop.bound_box()[0])[[0, 2, 1]]


def get_mcpivot(
    objprop: ObjectMcProperties,
    object_properties: tp.Dict[ObjectId, ObjectMcProperties]
) -> np.ndarray:
    '''
    Returns the pivot point of a mcbone (or mccube).
    - objprop - the properties of this mcbone/mccube
    - object_properties - the properties of all of the mccubes and mcbones in
      minecraft model
    '''
    def local_crds(
        parent_matrix: mathutils.Matrix, child_matrix: mathutils.Matrix
    ) -> mathutils.Vector:
        '''Local coordinates of child matrix inside parent matrix'''
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _get_mcpivot(objprop: ObjectMcProperties) -> mathutils.Vector:
        if objprop.mcparent is not None:
            result = local_crds(
                object_properties[objprop.mcparent].matrix_world(),
                objprop.matrix_world()
            )
            result += _get_mcpivot(object_properties[objprop.mcparent])
        else:
            result = objprop.matrix_world().to_translation()
        return result

    return np.array(_get_mcpivot(objprop).xzy)


def get_object_mcproperties(
    context: bpy_types.Context
) -> tp.Dict[ObjectId, ObjectMcProperties]:
    '''
    Loops through context.selected_objects and returns a dictionary with custom
    properties of mcobjects. Returned dictionary uses the ObjectId of the
    objects as keys and the custom properties as values.
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

    properties: tp.Dict[ObjectId, ObjectMcProperties] = {}
    for obj in context.selected_objects:
        if obj.type == "":  # Invalid object (like Camera)
            continue
        tmp_prop = tmp_properties[obj.name]
        if obj.type == 'EMPTY':
            if "mc_is_bone" in obj:
                tmp_prop['mc_obj_type'] = MCObjType.BONE
            elif "mc_parent" not in obj:
                tmp_prop['mc_obj_type'] = MCObjType.BONE
            elif len(tmp_properties[obj.name]["mc_children"]) > 0:
                tmp_prop['mc_obj_type'] = MCObjType.BONE
            else:
                tmp_prop['mc_obj_type'] = MCObjType.LOCATOR
        elif obj.type == 'MESH':
            if len(tmp_properties[obj.name]["mc_children"]) > 0:
                tmp_prop['mc_obj_type'] = MCObjType.BOTH
            elif "mc_is_bone" in obj:
                tmp_prop["mc_obj_type"] = MCObjType.BOTH
            elif "mc_parent" in obj:
                tmp_prop["mc_obj_type"] = MCObjType.CUBE
            else:  # Not connected to anything
                tmp_prop["mc_obj_type"] = MCObjType.BOTH

        properties[ObjectId(obj.name, '')] = ObjectMcProperties(
            thisobj = obj,
            mcparent = ObjectId(obj['mc_parent'].name, '') if 'mc_parent' in obj else None,
            mcchildren = tuple(ObjectId(i.name, '') for i in tmp_prop['mc_children']),  # type: ignore
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
