'''
Functions and objects shared between other modules of Mcblend.
'''
from __future__ import annotations

from ctypes import c_int
import math
from enum import Enum
from typing import (
    Dict, NamedTuple, List, Optional, Tuple, Any, Iterable, Sequence)

import numpy as np

import bpy_types
import bpy
import mathutils

from .texture_generator import Mask, ColorMask, get_masks_from_side
from .exception import NameConflictException, NoCubePolygonsException

MINECRAFT_SCALE_FACTOR = 16
'''The scale convertion from blender to minecraft (16 units == 1 meter).'''

class MCObjType(Enum):
    '''The types of Minecraft objects created from blender objects.'''
    CUBE = 'CUBE'
    BONE = 'BONE'
    BOTH = 'BOTH'
    LOCATOR = 'LOCATOR'

class MeshType(Enum):
    '''
    Type of the exported mesh. Changes the way of representation of this
    object in exported model file.
    '''
    CUBE = 'Cube'
    POLY_MESH = 'Poly Mesh'

class ObjectId(NamedTuple):
    '''
    Object that represents Unique ID of blender object (bone, empty or mesh).

    For meshes and empties:
        - :code:`bone_name` is just an empty string.
        - :code:`name` is the name of the object.
    For bones:
        - :code:`bone_name` is the name of the bone.
        - :code:`name` is the name of the armature that owns the bone.
    '''
    name: str
    bone_name: str

class McblendObject:
    '''
    A class that wraps Blender objects (meshes, empties and bones) and
    provides access to various properties used by Mcblend.


    :param thisobj_id: The :class:`ObjectId` that identifies this object.
    :param thisobj: Blender object wrapped inside this object.
    :param parentobj_id: The :class:`ObjectId` of the parent of this object.
    :param children_ids: The list of :class:`ObjectId`s of the children of this
        object.
    :param mctype: The :class:`MCObjType` of of this object.
    :param group: The :class:`McblendObjectGroup` that stores all of the
        :class:`McblendObject`s being processed with this object.
    '''
    def __init__(
            self, thisobj_id: ObjectId, thisobj: bpy.types.Object,
            parentobj_id: Optional[ObjectId], children_ids: List[ObjectId],
            mctype: MCObjType, group: McblendObjectGroup):
        self.thisobj_id = thisobj_id
        self.thisobj: bpy.types.Object = thisobj
        self.parentobj_id: Optional[ObjectId] = parentobj_id
        self.children_ids: List[ObjectId] = children_ids
        self.mctype: MCObjType = mctype
        self.group = group

    @property
    def parent(self) -> Optional[McblendObject]:
        '''Parent of this object.'''
        try:
            if self.parentobj_id is None:
                return None
            return self.group[self.parentobj_id]
        except KeyError:
            return None

    @property
    def children(self) -> Tuple[McblendObject]:
        '''
        Children of this object from the :class:`McblendObjectGroup` of this
        object.
        '''
        children: List[McblendObject] = []
        for child_id in self.children_ids:
            if child_id in self.group:
                children.append(self.group[child_id])
        return tuple(children)  # type: ignore

    @property
    def inflate(self) -> float:
        '''Inflate value of this object'''
        return self.thisobj.nusiq_mcblend_object_properties.inflate

    @inflate.setter
    def inflate(self, inflate: float):
        self.thisobj.nusiq_mcblend_object_properties.inflate = inflate

    @property
    def mesh_type(self) -> MeshType:
        '''Mesh type of this object'''
        return MeshType(self.thisobj.nusiq_mcblend_object_properties.mesh_type)

    @mesh_type.setter
    def mesh_type(self, mesh_type: MeshType):
        self.thisobj.nusiq_mcblend_object_properties.mesh_type = (
            mesh_type.value)

    @property
    def mirror(self) -> bool:
        '''Whether the objects UV is mirrored.'''
        return self.thisobj.nusiq_mcblend_object_properties.mirror

    @mirror.setter
    def mirror(self, mirror: bool):
        self.thisobj.nusiq_mcblend_object_properties.mirror = mirror

    @property
    def is_bone(self) -> bool:
        '''Whether the object should be exported as bone to Minecraft model.'''
        return self.thisobj.nusiq_mcblend_object_properties.is_bone

    @is_bone.setter
    def is_bone(self, is_bone: bool):
        self.thisobj.nusiq_mcblend_object_properties.is_bone = is_bone

    @property
    def uv_group(self) -> str:
        '''The name of the UV-group of this object.'''
        return self.thisobj.nusiq_mcblend_object_properties.uv_group

    @uv_group.setter
    def uv_group(self, uv_group: str):
        self.thisobj.nusiq_mcblend_object_properties.uv_group = uv_group

    @property
    def obj_data(self) -> Any:
        '''
        The "data" property of the blender object wrapped inside this object.
        '''
        return self.thisobj.data

    @property
    def obj_name(self) -> str:
        '''The name of this object used for exporting to Minecraft model.'''
        if self.thisobj.type == 'ARMATURE':
            return self.thisobj.pose.bones[
                self.thisobj_id.bone_name
            ].name
        return self.thisobj.name.split('.')[0]

    @property
    def obj_type(self) -> str:
        '''
        The type of the blender object wrapped inside this
        object (ARMATURE, MESH or EMPTY).
        '''
        return self.thisobj.type

    @property
    def obj_bound_box(self) -> Any:
        '''The bound_box of the blender object wrapped inside this object.'''
        return self.thisobj.bound_box

    @property
    def obj_matrix_world(self) -> mathutils.Matrix:
        '''
        The copy of the translation matrix (matrix_world) of the blender
        wrapped inside this object.
        '''
        if self.thisobj.type == 'ARMATURE':
            return self.thisobj.matrix_world.copy() @ self.thisobj.pose.bones[
                self.thisobj_id.bone_name
            ].matrix.copy()
        return self.thisobj.matrix_world.copy()

    @property
    def mcube_size(self) -> np.ndarray:
        '''
        The cube size in Minecraft format based on the bounding box of the
        blender object wrapped inside this object.
        '''
        # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
        bound_box = self.obj_bound_box
        return (np.array(bound_box[6]) - np.array(bound_box[0]))[[0, 2, 1]]

    @property
    def mccube_position(self) -> np.ndarray:
        '''
        The cube position in Minecraft format based on the bounding box of
        the blender object wrapped inside this object.
        '''
        return np.array(self.obj_bound_box[0])[[0, 2, 1]]

    @property
    def mcpivot(self) -> np.ndarray:
        '''
        The pivot point of Minecraft object exported using this object.
        '''
        def local_crds(
                parent: McblendObject, child: McblendObject
            ) -> mathutils.Vector:
            '''Local coordinates of child matrix inside parent matrix'''
            # Applying normalize() function to matrix world of parent and child
            # suppose to fix some errors with scaling but tests doesn't show any
            # difference.
            # It does fix the issue #62 so PLEASE don't change it again!
            return child.get_local_matrix(
                parent, normalize=True).to_translation()

        def _get_mcpivot(objprop: McblendObject) -> mathutils.Vector:
            if objprop.parent is not None:
                result = local_crds(objprop.parent, objprop)
                result += _get_mcpivot(objprop.parent)
            else:
                result = objprop.obj_matrix_world.to_translation()
            return result

        return np.array(_get_mcpivot(self).xzy)

    def get_local_matrix(
            self, other: Optional[McblendObject] = None, normalize: bool = False
        ) -> mathutils.Matrix:
        '''
        Returns translation matrix of this object optionally in translation
        space of the other :class:`McblendObject`.

        :param other: Optional - the other :class:`McblendObject`
        :param normalize: Whether to normalizes parent and child matrixes
            before calculating the relative matrix. This solves problems
            related to different scales of parent and child transformations
            (see github issue #62 and #71)
        :returns: translation matrix of this object.
        '''
        if other is not None:
            p_matrix = other.obj_matrix_world
        else:
            p_matrix = (
                # pylint: disable=no-value-for-parameter
                mathutils.Matrix()
            )
        c_matrix = self.obj_matrix_world
        if normalize:
            p_matrix.normalize()
            c_matrix.normalize()
        return p_matrix.inverted() @ c_matrix

    def get_mcrotation(
            self, other: Optional[McblendObject] = None
        ) -> np.ndarray:
        '''
        Returns the Minecraft rotation of this object optionally in relation
        to the other :class:`McblendObject`.

        # Arguments:
        :param other: Optional - the the other :class:`McblendObject`.
        :returns: numpy array with the rotation of this object in Minecraft
            format.
        '''
        def local_rotation(
                child_matrix: mathutils.Matrix, parent_matrix: mathutils.Matrix
            ) -> mathutils.Euler:
            '''
            Returns Euler rotation of a child matrix in relation to parent matrix
            '''
            child_matrix = child_matrix.normalized()
            parent_matrix = parent_matrix.normalized()
            return (
                parent_matrix.inverted() @ child_matrix
            ).to_quaternion().to_euler('XZY')

        if other is not None:
            result_euler = local_rotation(
                self.obj_matrix_world, other.obj_matrix_world
            )
        else:
            result_euler = self.obj_matrix_world.to_euler('XZY')
        result: np.ndarray = np.array(result_euler)[[0, 2, 1]]
        result = result * np.array([1, -1, 1])
        result = result * 180/math.pi  # math.degrees() for array
        return result

    def cube_polygons(self) -> CubePolygons:
        '''
        Returns the :class:`CubePolygons` of this object (always new copy of
        the object).
        '''
        return CubePolygons.build(self.thisobj, self.mirror)

    @property
    def side1_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 1 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((0, 1, 0))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side1)

    @property
    def side2_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 2 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 0, 1))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side2)

    @property
    def side3_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 3 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 0, 0))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side3)

    @property
    def side4_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 4 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((0, 1, 1))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side4)

    @property
    def side5_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 5 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((0, 0, 1))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side5)

    @property
    def side6_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 6 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 1, 0))]
        uv_group = bpy.context.scene.nusiq_mcblend_uv_groups[self.uv_group]
        masks = get_masks_from_side(uv_group.side6)
        return masks

    def find_lose_parts(self) -> Tuple[int, ...]:
        '''
        Finds lose parts thisobj (must be a MESH otherwise an empty tuple is
        returned). Returns a tuple of integers, the indices of the tuple
        represent the indices of vertices, and the values identify the group.
        Vertices that aren't connected to anything are assigned to group "-1".
        The names of the groups aren't integers in any particular order. They
        are based on the lowest vertex index in the group - e.g. a group with
        vertices (3,6,2,4) would get ID 2 because 2 is the lowest vertex index.
        '''
        if self.obj_type != 'MESH':
            return tuple()
        obj = self.thisobj

        # List that represents the grouping - index: the index of vertex
        # value: the pointer to identifier of a group of that vertex
        groups = [c_int(-1) for _ in range(len(obj.data.vertices))]

        for edge in obj.data.edges:
            a, b = edge.vertices
            aptr, bptr = groups[a], groups[b]
            if aptr.value != -1:
                if bptr.value != -1:
                    bptr.value = aptr.value = min(a, b, aptr.value, bptr.value)
                else:
                    groups[b] = aptr
                    aptr.value = min(a, b, aptr.value)
            elif bptr.value != -1: # aptr.value is None
                groups[a] = bptr
                bptr.value = min(a, b, bptr.value)
            else:  # aptr.value is None and bptr.value is None
                groups[b] = aptr
                aptr.value = min(a, b)
        return tuple([i.value for i in groups])

# key (side, is_mirrored) : value (names of the vertices)
# Used in CubePolygons constructor
_MC_MAPPING_UV_ORDERS = {
    ('east', False) :('-+-', '---', '--+', '-++'),
    ('north', False) :('---', '+--', '+-+', '--+'),
    ('west', False) :('+--', '++-', '+++', '+-+'),
    ('south', False) :('++-', '-+-', '-++', '+++'),
    ('up', False) :('--+', '+-+', '+++', '-++'),
    ('down', False) :('-+-', '++-', '+--', '---'),
    ('west', True) :('++-', '+--', '+-+', '+++'),
    ('north', True) :('+--', '---', '--+', '+-+'),
    ('east', True) :('---', '-+-', '-++', '--+'),
    ('south', True) :('-+-', '++-', '+++', '-++'),
    ('up', True) :('+-+', '--+', '-++', '+++'),
    ('down', True) :('++-', '-+-', '---', '+--'),
}

class CubePolygons(NamedTuple):
    '''
    Polygons of blender cube object that correspond to Minecraft cube faces.
    '''
    east: CubePolygon  # Cube Right
    north: CubePolygon  # Cube Front
    west: CubePolygon  # Cube Left
    south: CubePolygon  # Cube Back
    up: CubePolygon  # Cube Up
    down: CubePolygon  # Cube Down

    @staticmethod
    def build(cube: bpy.types.Object, mirror: bool) -> CubePolygons:
        '''
        Creates :class:`CubePolygons` object for given blender object cube.

        :param cube: blender cube mesh.
        :param mirror: Whether the order of vertices in returned
            :class:`CubePolygons` should match Minecraft mirrored mapping format
            or not.
        '''
        def get_order(
            name: str, mirror: bool,
            bound_box_vertices: Tuple[str, str, str, str]
        ) -> Tuple[int, int, int, int]:
            '''Gets the order of vertices for given cube polygon'''
            mc_mapping_uv_order = _MC_MAPPING_UV_ORDERS[(name, mirror)]
            result = []
            for vertex_name in mc_mapping_uv_order:
                # Throws ValueError
                index = bound_box_vertices.index(vertex_name)
                result.append(index)
            return tuple(result)  # type: ignore

        # 1. Check if object has 6 quadrilateral faces
        if len(cube.data.polygons) != 6:
            raise NoCubePolygonsException(
                f"Object {cube.name.split('.')} is not a cube. Number of faces != 6."
            )
        for polygon in cube.data.polygons:
            if len(polygon.vertices) != 4:
                raise NoCubePolygonsException(
                    f"Object {cube.name.split('.')} is not a cube. Not all faces are "
                    "quadrilateral."
                )

        # Blender crds (bounding box):
        # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
        mmm, mmp, mpp, mpm, pmm, pmp, ppp, ppm = tuple(cube.bound_box)
        # MC:      0+0 top; -00 right; 00- front;
        # Blender: 00+ top; -00 right; 0-0 front
        bb_crds = {
            "---": np.array(mmm), "--+": np.array(mmp),
            "-++": np.array(mpp), "-+-": np.array(mpm),
            "+--": np.array(pmm), "+-+": np.array(pmp),
            "+++": np.array(ppp), "++-": np.array(ppm)
        }

        north: List[str] = ['---', '+--', '+-+', '--+']  # Cube Front
        east: List[str] = ['--+', '-++', '-+-', '---']  # Cube Right
        south: List[str] = ['-++', '+++', '++-', '-+-']  # Cube Back
        west: List[str] = ['+--', '++-', '+++', '+-+']  # Cube Left
        up: List[str] = ['--+', '+-+', '+++', '-++']  # Cube Up
        down: List[str] = ['-+-', '++-', '+--', '---']  # Cube Down
        cube_polygon_builder = {}  # Input for CubePolygons constructor
        for polygon in cube.data.polygons:
            bbv: List[str] = []  # bound box vertices
            for vertex_id in polygon.vertices:
                vertex_crds = np.array(
                    cube.data.vertices[vertex_id].co
                )
                # Find the closest point of bounding box (key from bb_crds)
                shortest_distance: Optional[float] = None
                closest_bb_point = '---'
                for k, v in bb_crds.items():
                    curr_distance = np.linalg.norm(v-vertex_crds)
                    if shortest_distance is None:
                        shortest_distance = curr_distance
                        closest_bb_point = k
                    elif curr_distance < shortest_distance:
                        shortest_distance = curr_distance
                        closest_bb_point = k
                bbv.append(closest_bb_point)

            if cyclic_equiv(north, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['north'] = CubePolygon(
                    polygon, t_bbv, get_order('north', mirror, t_bbv)
                )
            elif cyclic_equiv(east, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['east'] = CubePolygon(
                    polygon, t_bbv, get_order('east', mirror, t_bbv)
                )
            elif cyclic_equiv(south, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['south'] = CubePolygon(
                    polygon, t_bbv, get_order('south', mirror, t_bbv)
                )
            elif cyclic_equiv(west, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['west'] = CubePolygon(
                    polygon, t_bbv, get_order('west', mirror, t_bbv)
                )
            elif cyclic_equiv(up, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['up'] = CubePolygon(
                    polygon, t_bbv, get_order('up', mirror, t_bbv)
                )
            elif cyclic_equiv(down, bbv):
                t_bbv: Tuple[str, str, str, str] = tuple(bbv)  # type: ignore
                cube_polygon_builder['down'] = CubePolygon(
                    polygon, t_bbv, get_order('down', mirror, t_bbv)
                )
        try:
            return CubePolygons(**cube_polygon_builder)
        except TypeError as e:  # Missing argument
            raise NoCubePolygonsException(
                f'Object "{cube.name}" is not a cube.'
            ) from e

class CubePolygon(NamedTuple):
    '''
    Single face in :class:`CubePolygons`.

    :param side: :class:`bpy_types.MeshPolygon` object from blender mesh.
    :param orientation: The names of the vertices of the Mesh polygon. Vertices
        are named with 3-character-string (using only '+' and '-'). Where each
        character symbolizes whether the vertex is on increasing (+) or
        decreasing (-) side of the corresponding axis (XYZ) in local space of
        the object.
    :param order: Stores the order (values from 0 to 3) in which the loops of
        the face should be rearranged to match this: 0 left bottom corner,
        1 right bottom corner, 2 right top corner, 3 left top corner.
    '''
    side: bpy_types.MeshPolygon
    orientation: Tuple[str, str, str, str]
    order: Tuple[int, int, int, int]

class McblendObjectGroup:
    '''
    A group of :class:`McblendObject`s often used as a main datasource for
    operations executed by Mcblend.
    The objects can be accessed with ObjectId with __getitem__ method like
    from a dict.

    :param context: the context of runing an operator.
    '''
    def __init__(self, context: bpy_types.Context):
        self.data: Dict[ObjectId, McblendObject] = {}
        '''the content of the group.'''

        self._load_objects(context)
        self._check_name_conflicts()

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key: ObjectId) -> McblendObject:
        return self.data[key]

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        return self.data.__iter__()

    def values(self):
        '''Lists values of this group (the :class:`McblendObject`s).'''
        return self.data.values()

    def keys(self):
        '''Lists valid keys to use in this object.'''
        return self.data.keys()

    def items(self):
        '''Iterator going through pairs of keys and values of this group.'''
        return self.data.items()

    def _load_objects(self, context: bpy_types.Context):
        '''
        Loops through selected objects and and creates :class:`McblendObjects`
        for this group. Used by constructor.

        :param context: the context of running an operator.
        '''
        for obj_id, obj in self._loop_objects(context.selected_objects):
            curr_obj_mc_type: MCObjType
            curr_obj_mc_parent: Optional[ObjectId] = None
            if obj.type == 'EMPTY':
                curr_obj_mc_type = MCObjType.BONE
                if (obj.parent is not None and len(obj.children) == 0 and
                        not obj.nusiq_mcblend_object_properties.is_bone):
                    curr_obj_mc_type = MCObjType.LOCATOR

                if obj.parent is not None:
                    curr_obj_mc_parent = self._get_parent_mc_bone(obj)
            elif obj.type == 'MESH':
                if (obj.parent is None or
                        obj.nusiq_mcblend_object_properties.is_bone):
                    curr_obj_mc_type = MCObjType.BOTH
                else:
                    curr_obj_mc_type = MCObjType.CUBE
                # If parent is none than it will return none
                curr_obj_mc_parent = self._get_parent_mc_bone(obj)
            elif obj.type == 'ARMATURE':
                bone = obj.data.bones[obj_id.bone_name]
                if (
                        bone.parent is None and len(bone.children) == 0 and
                        len([  # Children of a bone which are not other bones.
                            c for c in obj.children
                            if c.parent_bone == bone.name
                        ]) == 0
                    ):
                    continue  # Skip empty bones
                curr_obj_mc_type = MCObjType.BONE
                if bone.parent is not None:
                    curr_obj_mc_parent = ObjectId(obj.name, bone.parent.name)
            else:  # Handle only empty, meshes and armatures
                continue
            self.data[obj_id] = McblendObject(
                obj_id, obj, curr_obj_mc_parent,
                [], curr_obj_mc_type, self
            )
        # Fill the children property. Must be in separate loop to reverse the
        # effect of _get_parent_mc_bone() function.
        for objid, objprop in self.data.items():
            if objprop.parentobj_id is not None and objprop.parentobj_id in self.data:
                self.data[objprop.parentobj_id].children_ids.append(objid)

    def _check_name_conflicts(self):
        '''
        Looks through the dictionary of :class:`McblendObject`s of this object
        and tries to find the names conflicts in the names of the objects.

        Raises NameConflictException if name conflicts in some bones are
        detected. Used in constructor.
        '''
        names: List[str] = []
        for objprop in self.values():
            if objprop.mctype not in [MCObjType.BONE, MCObjType.BOTH]:
                continue  # Only bone names conflicts count
            if objprop.obj_name in names:
                raise NameConflictException(
                    f'Name conflict "{objprop.obj_name}". Please rename theobject."'
                )
            names.append(objprop.obj_name)

    @staticmethod
    def _loop_objects(objects: List) -> Iterable[Tuple[ObjectId, Any]]:
        '''
        Loops over the empties, meshes and armature objects from the list and
        yields them and their ids. If object is an armature than it also loops
        over every bone and yields the pair of armature and the id of the bone.
        Used in the constructor.

        :param objects: The list of blender objects.
        :returns: Iterable that goes through objects and bones.
        '''
        for obj in objects:
            if obj.type in ['MESH', 'EMPTY']:
                yield ObjectId(obj.name, ''), obj
            elif obj.type == 'ARMATURE':
                for bone in obj.data.bones:
                    yield ObjectId(obj.name, bone.name), obj

    @staticmethod
    def _get_parent_mc_bone(obj: bpy.types.Object) -> Optional[ObjectId]:
        '''
        Goes up through the ancestors of an :class:`bpy.types.Object` and
        tries to find the object that represents its parent bone in Minecraft
        model. Used in constructor.

        :param obj: Blender object which will be a bone in Minecraft model.
        :returns: Id of the object that represents a parent bone in Minecraft
            model.
        '''
        obj_id = None
        while obj.parent is not None:
            if obj.parent_type == 'BONE':
                return ObjectId(obj.parent.name, obj.parent_bone)

            if obj.parent_type == 'OBJECT':
                obj = obj.parent
                obj_id = ObjectId(obj.name, '')
                if (obj.type == 'EMPTY' or
                        obj.nusiq_mcblend_object_properties.is_bone):
                    return obj_id
            else:
                raise Exception(f'Unsupported parent type {obj.parent_type}')
        return obj_id

def cyclic_equiv(u: List, v: List) -> bool:
    '''
    Compare cyclic equivalency of two lists.

    Source:

    https://stackoverflow.com/questions/31000591/
    '''
    n, i, j = len(u), 0, 0
    if n != len(v):
        return False
    while i < n and j < n:
        k = 1
        while k <= n and u[(i + k) % n] == v[(j + k) % n]:
            k += 1
        if k > n:
            return True
        if u[(i + k) % n] > v[(j + k) % n]:
            i += k
        else:
            j += k
    return False

# TODO - maybe find a better place for this code

def apply_obj_transform_keep_origin(obj: bpy.types.Object):
    '''
    Apply object transformations but keep the origin in place. Resets object
    rotation and scale but keeps location the same.
    '''
    # Decompose object transformations
    loc, rot, scl = obj.matrix_local.decompose()
    loc_mat = mathutils.Matrix.Translation(loc)
    rot_mat = rot.to_matrix().to_4x4()
    scl_mat =  (
        mathutils.Matrix.Scale(scl[0],4,(1,0,0)) @
        mathutils.Matrix.Scale(scl[1],4,(0,1,0)) @
        mathutils.Matrix.Scale(scl[2],4,(0,0,1)))
    obj.matrix_local = loc_mat

    for vertex in obj.data.vertices:
        vertex.co =  rot_mat @ scl_mat @ vertex.co

def fix_cube_rotation(obj: bpy.types.Object):
    '''
    Rotate the bounding box of a cuboid so  it's aligned with
    the cube rotation. The scale and rotation of the object must
    be in default position for this function to work.

    :param obj: blender object with cuboid mesh. 
    '''
    # Get coordinates of 3 points (a,b and c) from any polygon
    # I'm assuming this is a cuboid so I also can assume that
    # vectors u and v are not planar:
    # u = vector(b, a) and v = (b, c)
    poly = obj.data.polygons[0]

    vertices = obj.data.vertices
    a = vertices[poly.vertices[0]].co
    b = vertices[poly.vertices[1]].co
    c = vertices[poly.vertices[2]].co

    # Calculate the normal vector of the surface with points
    # a, b and c
    u: mathutils.Vector = (a-b).normalized()
    v: mathutils.Vector = (c-b).normalized()

    # The cross product creates the 3rd vector that defines
    # the rotated space
    w = u.cross(v).normalized()
    # Recalculate V to make sure that all of the vectors are at
    # the right angle (even though they should be)
    v = w.cross(u).normalized()

    # Create rotation matrix (unit vectors x, y, z in columns)
    rotation_matrix = mathutils.Matrix((w, v, -u))
    # (w, v, -u) - this order of normals in rotation matrix is set up in
    # such way that applying the operator to the default cube (without
    # rotations) will not change its rotation and won't flip its scale to -1.
    # It will have no effect.


    # Rotate the mesh
    for vertex in obj.data.vertices:
        vertex.co = rotation_matrix @ vertex.co

    # Counter rotate object around its origin
    counter_rotation = rotation_matrix.to_4x4().inverted()

    loc, rot, scl = obj.matrix_local.decompose()
    loc_mat = mathutils.Matrix.Translation(loc)
    rot_mat = rot.to_matrix().to_4x4()
    scl_mat =  (
        mathutils.Matrix.Scale(scl[0],4,(1,0,0)) @
        mathutils.Matrix.Scale(scl[1],4,(0,1,0)) @
        mathutils.Matrix.Scale(scl[2],4,(0,0,1)))

    obj.matrix_local = loc_mat @ counter_rotation @ rot_mat @ scl_mat
