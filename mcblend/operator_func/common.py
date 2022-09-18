'''
Functions and objects shared between other modules of Mcblend.
'''
from __future__ import annotations

from ctypes import c_int
import math
from enum import Enum
from typing import (
    Deque, Dict, Iterator, NamedTuple, List, Optional, Tuple, Any, Iterable, Sequence)
from collections import deque

import numpy as np

import bpy
from bpy.types import MeshUVLoopLayer, Object, MeshPolygon, PoseBone

import mathutils

from .typed_bpy_access import get_armature_data_bones

from .texture_generator import Mask, ColorMask, get_masks_from_side
from .exception import ExporterException

MINECRAFT_SCALE_FACTOR = 16
'''The scale convertion from blender to minecraft (16 units == 1 meter).'''

class AnimationLoopType(Enum):
    '''The types of the loop property from Minecraft animations'''
    TRUE = 'true'
    FALSE = 'false'
    HOLD_ON_LAST_FRAME = 'hold_on_last_frame'

class MCObjType(Enum):
    '''The types of Minecraft objects created from blender objects.'''
    CUBE = 'CUBE'
    BONE = 'BONE'
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
        - :code:`name` is the name of the object.
        - :code:`bone_name` is just an empty string.

    For bones:
        - :code:`name` is the name of the armature that owns the bone.
        - :code:`bone_name` is the name of the bone.
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
            self, thisobj_id: ObjectId, thisobj: Object,
            parentobj_id: Optional[ObjectId], children_ids: List[ObjectId],
            mctype: MCObjType, group: McblendObjectGroup):
        self.thisobj_id = thisobj_id
        self.thisobj: Object = thisobj
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
    def children(self) -> Tuple[McblendObject, ...]:
        '''
        Children of this object from the :class:`McblendObjectGroup` of this
        object.
        '''
        children: List[McblendObject] = []
        for child_id in self.children_ids:
            if child_id in self.group:
                children.append(self.group[child_id])
        return tuple(children)

    @property
    def inflate(self) -> float:
        '''Inflate value of this object'''
        return self.thisobj.mcblend.inflate

    @inflate.setter
    def inflate(self, inflate: float):
        self.thisobj.mcblend.inflate = inflate

    @property
    def min_uv_size(self) -> np.ndarray:
        '''The lower UV-size limit of this object.'''
        return np.array(
            self.thisobj.mcblend.min_uv_size)

    @min_uv_size.setter
    def min_uv_size(self, min_uv_size: np.ndarray):
        self.thisobj.mcblend.min_uv_size = min_uv_size

    @property
    def mesh_type(self) -> MeshType:
        '''Mesh type of this object'''
        return MeshType(self.thisobj.mcblend.mesh_type)

    @mesh_type.setter
    def mesh_type(self, mesh_type: MeshType):
        self.thisobj.mcblend.mesh_type = (
            mesh_type.value)

    @property
    def mirror(self) -> bool:
        '''Whether the objects UV is mirrored.'''
        return self.thisobj.mcblend.mirror

    @mirror.setter
    def mirror(self, mirror: bool):
        self.thisobj.mcblend.mirror = mirror

    @property
    def uv_group(self) -> str:
        '''The name of the UV-group of this object.'''
        return self.thisobj.mcblend.uv_group

    @uv_group.setter
    def uv_group(self, uv_group: str):
        self.thisobj.mcblend.uv_group = uv_group

    @property
    def obj_data(self) -> Any:
        '''
        The "data" property of the blender object wrapped inside this object.
        '''
        return self.thisobj.data

    @property
    def this_pose_bone(self) -> PoseBone:
        '''The pose bone of this object (doesn't work for non-bone objects)'''
        return self.thisobj.pose.bones[self.thisobj_id.bone_name]

    @property
    def obj_name(self) -> str:
        '''The name of this object used for exporting to Minecraft model.'''
        if self.thisobj.type == 'ARMATURE':
            return self.thisobj.pose.bones[
                self.thisobj_id.bone_name
            ].name
        return self.thisobj.name

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
        elif self.group.world_origin is not None:
            p_matrix = self.group.get_world_origin_matrix()
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
            child_q = child_matrix.normalized().to_quaternion()
            parent_q = parent_matrix.inverted().normalized().to_quaternion()
            return (parent_q @ child_q).to_euler('XZY')

        if other is not None:
            result_euler = local_rotation(
                self.obj_matrix_world, other.obj_matrix_world
            )
        elif self.group.world_origin is not None:
            result_euler = local_rotation(
                self.obj_matrix_world,
                self.group.get_world_origin_matrix()
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
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side1)

    @property
    def side2_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 2 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 0, 1))]
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side2)

    @property
    def side3_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 3 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 0, 0))]
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side3)

    @property
    def side4_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 4 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((0, 1, 1))]
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side4)

    @property
    def side5_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 5 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((0, 0, 1))]
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
        return get_masks_from_side(uv_group.side5)

    @property
    def side6_uv_masks(self) -> Sequence[Mask]:
        '''
        Sequence of masks affecting the texture of side 6 of the cube of this
        object.
        '''
        if self.uv_group == '':
            return [ColorMask((1, 1, 0))]
        uv_group = bpy.context.scene.mcblend_uv_groups[self.uv_group]
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
        return tuple(i.value for i in groups)

# TODO - CubePolygonsSolver, CubePolygons and CubePolygon is a messy structure
# maybe CubePolygonsSolver should be removed
class CubePolygonsSolver:
    '''
    This class is used for creating CubePolygons. It solves the problem of
    assigning correct vertices of a model to correct positions of Minecraft
    cubes.

    Properties:
    - p_options - lists of possible positions of vertices (there is 8 vertices)
    - polygons - MeshPolygons of the cube
    - solved - whether the problem was solved or not
    - solution - a list of assigned positions of vertices (list of names like
        '+++').
    '''
    FACE_PATTERNS = [
        ['---', '+--', '+-+', '--+'],  # Cube Front (north)
        ['--+', '-++', '-+-', '---'],  # Cube Right (east)
        ['-++', '+++', '++-', '-+-'],  # Cube Back (south)
        ['+--', '++-', '+++', '+-+'],  # Cube Left (west)
        ['--+', '+-+', '+++', '-++'],  # Cube Up (up)
        ['-+-', '++-', '+--', '---'],  # Cube Down (down)
    ]
    FACE_NAMES = ['north', 'east', 'south', 'west', 'up', 'down']

    # key (side, is_mirrored) : value (names of the vertices)
    MC_MAPPING_UV_ORDERS = {
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

    def __init__(
            self, p_options: List[List[str]],
            polygons: MeshPolygon):
        self.p_options = p_options
        self.polygons = polygons
        self.solved = False
        self.solution: List[Optional[str]] = [None] * 8

    @staticmethod
    def _get_vertices_order(
        name: str, mirror: bool,
        bound_box_vertices: List[str]
    ) -> Tuple[int, int, int, int]:
        '''Gets the order of vertices for given cube polygon'''
        mc_mapping_uv_order = CubePolygonsSolver.MC_MAPPING_UV_ORDERS[
            (name, mirror)]
        result = []
        for vertex_name in mc_mapping_uv_order:
            # Throws ValueError
            index = bound_box_vertices.index(vertex_name)
            result.append(index)
        return tuple(result)  # type: ignore

    def get_cube_polygons(self, mirror: bool) -> CubePolygons:
        '''
        Creates CubesPolygons object based on the solution.
        '''
        if not self.solved:
            raise RuntimeError(
                "Trying to access solution before runing solve function")
        cube_polygons: Dict[str, CubePolygon] = {}
        for polygon in self.polygons:
            complete_face: List[str] = []
            for vertex_index in polygon.vertices:
                complete_face.append(self.solution[vertex_index])
            for j, face_pattern in enumerate(CubePolygonsSolver.FACE_PATTERNS):
                if cyclic_equiv(face_pattern, complete_face):
                    side_name = CubePolygonsSolver.FACE_NAMES[j]
                    order = CubePolygonsSolver._get_vertices_order(
                        side_name, mirror, complete_face)
                    cube_polygons[side_name] = (
                        CubePolygon(
                            polygon,
                            tuple(complete_face),  # type: ignore
                            order))
        return CubePolygons(**cube_polygons)

    def is_valid(self):
        '''
        Check if suggested solution can be valid. The solution may be
        incomplete. This function returns False only in case of finding an
        error in solution. If the solution doesn't provide any information
        about
        '''
        used_face_patterns = [False]*6
        for polygon in self.polygons:
            complete_face = [None]*4
            for i, vertex_index in enumerate(polygon.vertices):
                complete_face[i] = self.solution[vertex_index]
            if None in complete_face:
                continue  # This face is not complete
            for j, face_pattern in enumerate(CubePolygonsSolver.FACE_PATTERNS):
                if used_face_patterns[j]:
                    continue  # This pattern is used already (don't check that)
                if cyclic_equiv(face_pattern, complete_face):
                    used_face_patterns[j] = True
                    break  # found matching face pattern
            else:
                return False  # Matching face_pattern not found
        return True

    def solve(self, vertex_index: int=0):
        '''
        Assigns the vertices to their positions (fills the self.solution table)
        using constraints from self.p_options and self.polygons.

        :returns: True if operation succeeded and False otherwise
        '''
        for position_code in self.p_options[vertex_index]:
            if position_code in self.solution:
                continue
            self.solution[vertex_index] = position_code
            if not self.is_valid():
                continue
            if vertex_index >= 7:
                self.solved = True
                return True
            if self.solve(vertex_index+1):
                return True
        self.solution[vertex_index] = None
        return False

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
    def build(cube: Object, mirror: bool) -> CubePolygons:
        '''
        Creates :class:`CubePolygons` object for given blender object cube.

        :param cube: blender cube mesh.
        :param mirror: Whether the order of vertices in returned
            :class:`CubePolygons` should match Minecraft mirrored mapping format
            or not.
        '''
        # 0. Check if mesh has 12 edges
        if len(cube.data.edges) != 12:
            raise ExporterException(
                f"Object {cube.name.split('.')[0]} is not a cube. Number of edges != 12."
            )
        # 1. Check if object has 6 quadrilateral faces
        if len(cube.data.polygons) != 6:
            raise ExporterException(
                f"Object {cube.name.split('.')[0]} is not a cube. Number of faces != 6."
            )
        for polygon in cube.data.polygons:
            if len(polygon.vertices) != 4:
                raise ExporterException(
                    f"Object {cube.name.split('.')[0]} is not a cube. Not all faces are "
                    "quadrilateral."
                )
        # At this point the topology is correct but the cube might be deformed
        # or rotated inside its bound box

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

        p_options: List[List[str]] =  []
        for vertex_id in range(8):
            vertex_crds = np.array(cube.data.vertices[vertex_id].co)
            # Find the closest point of bounding box (key from bb_crds)
            shortest_distance: Optional[float] = None
            for k, v in bb_crds.items():
                p_options.append([])
                curr_distance = np.linalg.norm(v-vertex_crds)
                if shortest_distance is None:
                    shortest_distance = curr_distance
                    p_options[vertex_id] = [k]
                elif np.allclose(shortest_distance, curr_distance):
                    p_options[vertex_id].append(k)
                elif curr_distance < shortest_distance:
                    shortest_distance = curr_distance
                    p_options[vertex_id] = [k]

        solver = CubePolygonsSolver(p_options, list(cube.data.polygons))
        if not solver.solve():
            raise ExporterException(
                f'Object "{cube.name}" is not a cube.')

        try:
            return solver.get_cube_polygons(mirror)
        except TypeError as e:  # Missing argument
            raise ExporterException(
                f'Object "{cube.name}" is not a cube.'
            ) from e

    def __iter__(self) -> Iterator[CubePolygon]:
        yield self.east
        yield self.north
        yield self.west
        yield self.south
        yield self.up
        yield self.down

class CubePolygon(NamedTuple):
    '''
    Single face in :class:`CubePolygons`.

    :param side: :class:`MeshPolygon` object from blender mesh.
    :param orientation: The names of the vertices of the Mesh polygon. Vertices
        are named with 3-character-string (using only '+' and '-'). Where each
        character symbolizes whether the vertex is on increasing (+) or
        decreasing (-) side of the corresponding axis (XYZ) in local space of
        the object.
    :param order: Stores the order (values from 0 to 3) in which the loops of
        the face should be rearranged to match this: 0 left bottom corner,
        1 right bottom corner, 2 right top corner, 3 left top corner.
    '''
    side: MeshPolygon
    orientation: Tuple[str, str, str, str]
    order: Tuple[int, int, int, int]

    def uv_layer_coordinates(
            self, uv_layer: MeshUVLoopLayer) -> np.ndarray:
        '''
        Returns 4x2 numpy array with UV coordinates of this cube polygon loops
        from the uv_layer. The order of the coordinates in the array is
        defined by self.order (left bottom, right bottom, right top, left top)
        '''
        ordered_loop_indices = np.array(self.side.loop_indices)[[self.order]]
        crds = np.array([uv_layer.data[i].uv for i in ordered_loop_indices])
        return crds

    @staticmethod
    def validate_rectangle_uv(crds: np.ndarray) -> Tuple[bool, bool, bool]:
        '''
        Takes an 4x2 array with UV coordinates of 4 points (left bottom,
        right bottom, right top, left top) and checks if they're mapped to
        rectangular shape. The rectangle can have any width and height (
        including negative values) but can't be rotated.

        Returns 3 flags:

            1. Whether the object is a cuboid.
                - all vertices must be in the corners in the right order
                - top/bottom vertices must be at the top/bottom
                - left/right vertices must be at the left/right
            2. Whether left and right vertices are flipped (object scaled with
                negative value on U axis)
            3. Whether top and bottom vertices are flipped (object scaled with
                negative value on V axis)

        Notes:

        - When first flag is False the second and third flat is also False.
        - Usually used in combination with CubePolygon.uv_layer_coordinates
        '''
        min_ = crds.min(axis=0)
        max_ = crds.max(axis=0)
        # All loops in the corners
        if not (
            np.isclose(crds, min_) | np.isclose(crds, max_)
        ).all():
            return False, False, False

        lb, rb, rt, lt = crds
        # Left to left, right to right, bottom to bottom, top to top
        if (
                not np.isclose(lb[0], lt[0]) or
                not np.isclose(rb[0], rt[0]) or
                not np.isclose(lt[1], rt[1]) or
                not np.isclose(lb[1], rb[1])
        ):
            return False, False, False
        # is_valid, is_u_flipped, is_v_flipped
        return True, lb[0] != min_[0], lb[1] != min_[1]

class McblendObjectGroup:
    '''
    A group of :class:`McblendObject`s often used as a main datasource for
    operations executed by Mcblend.
    The objects can be accessed with ObjectId with __getitem__ method like
    from a dict.

    :param armature: the armature used as a root of the object group.
    :param world_origin: optional object that replaces the origin point of
        the world. The matrix_world of that objects becomes defines the
        transformation space of the animation. Animating that object is
        equivalent to animating everything else in opposite way.
    '''
    def __init__(
            self, armature: Object,
            world_origin: Optional[Object]):
        self.data: Dict[ObjectId, McblendObject] = {}
        '''the content of the group.'''
        self.world_origin: Optional[Object] = world_origin
        self._load_objects(armature)

    def get_world_origin_matrix(self):
        '''
        Returns the matrix_world of the world_origin object or rises an
        exception.
        '''
        if self.world_origin is None:
            raise RuntimeError("World origin not defined")
        return self.world_origin.matrix_world

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

    def _load_objects(self, armature: Object):
        '''
        Loops offspring of an armature and and creates :class:`McblendObjects`
        for this group. Used by constructor.

        :param armature: the armature used as a root of the object group.
        '''
        # Loop bones
        for bone in get_armature_data_bones(armature):
            obj_id: ObjectId = ObjectId(armature.name, bone.name)
            parent_bone_id: Optional[ObjectId] = None
            if bone.parent is not None:
                parent_bone_id = ObjectId(armature.name, bone.parent.name)
            self.data[obj_id] = McblendObject(
                thisobj_id=obj_id, thisobj=armature,
                parentobj_id=parent_bone_id, children_ids=[],
                mctype=MCObjType.BONE, group=self)
        for obj in armature.children:
            if obj.parent_type != 'BONE':
                continue  # TODO - maybe a warning here?
            parentobj_id = ObjectId(obj.parent.name, obj.parent_bone)
            obj_id = ObjectId(obj.name, "")
            if obj.type  == 'MESH':
                self.data[obj_id] = McblendObject(
                    thisobj_id=obj_id, thisobj=obj, parentobj_id=parentobj_id,
                    children_ids=[], mctype=MCObjType.CUBE, group=self)
                self.data[parentobj_id].children_ids.append(obj_id)
                # Further offspring of the "child" (share same parent in mc
                # model)
                offspring: Deque[Object] = deque(obj.children)
                while offspring:
                    child = offspring.pop()
                    child_id: ObjectId = ObjectId(child.name, "")
                    if child.parent_type != 'OBJECT':
                        continue
                    if child.type == 'MESH':
                        self.data[child_id] = McblendObject(
                            thisobj_id=child_id, thisobj=child,
                            parentobj_id=parentobj_id, children_ids=[],
                            mctype=MCObjType.CUBE, group=self)
                        self.data[parentobj_id].children_ids.append(child_id)
                        offspring.extend(child.children)
                    elif child.type == 'EMPTY':
                        self.data[child_id] = McblendObject(
                            thisobj_id=child_id, thisobj=child,
                            parentobj_id=parentobj_id, children_ids=[],
                            mctype=MCObjType.LOCATOR, group=self)
                        self.data[parentobj_id].children_ids.append(child_id)
            elif obj.type == 'EMPTY':
                self.data[obj_id] = McblendObject(
                    thisobj_id=obj_id, thisobj=obj, parentobj_id=parentobj_id,
                    children_ids=[], mctype=MCObjType.LOCATOR, group=self)
                self.data[parentobj_id].children_ids.append(obj_id)

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

def apply_obj_transform_keep_origin(obj: Object):
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

def fix_cube_rotation(obj: Object):
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

def get_vect_json(arr: Iterable) -> List[float]:
    '''
    Changes the iterable of numbers into basic python list of floats.
    Values from the original iterable are rounded to the 3rd deimal
    digit.

    :param arr: an iterable of numbers.
    '''
    result = [round(i, 3) for i in arr]
    for i, _ in enumerate(result):
        if result[i] == -0.0:
            result[i] = 0.0
    return result

def star_pattern_match(text: str, pattern: str) -> bool:
    '''
    Matches text with a pattern that uses "*" as a wildcard which
    can represent any number of characters.

    :param pattern: the pattern
    :param text: the text being matched with pattern
    '''
    lenp, lent = len(pattern), len(text)

    # Only empty text can match empty pattern
    if lenp == 0:
        return lent == 0

    # The table that represents matching smaller patterns to
    # parts of the text. Row 0 is for empty pattern, column 0
    # represents empty text: matches[text+1][pattern+1]
    matches = [[False for i in range(lenp + 1)] for j in range(lent + 1)]

    # Empty pattern matches the empty string
    matches[0][0] = True

    # Only paterns made out of '*' can match empty stirng
    for p in range(1, lenp+1):
        # Propagate matching apttern as long as long as the
        # pattern uses only '*'
        if pattern[p - 1] == '*':
            matches[0][p] = matches[0][p - 1]
        else:
            break
    # Fill the pattern matching table (solutions to
    # shorter patterns/texts are used to solve
    # other patterns with increasing complexity).
    for t in range(1, lent + 1):
        for p in range(1, lenp + 1):
            if pattern[p - 1] == '*':
                # Two wys to propagate matching value
                # A) Same pattern without '*' worked so this also works
                # B) Shorter text matched this pattern, and it ends with '*'
                # so adding characters doesn't change anything
                matches[t][p] = (
                    matches[t][p - 1] or
                    matches[t - 1][p]
                )
            elif pattern[p -1] == text[t - 1]:
                # One way to propagate matching value
                # If the pattern with one less character matched the text
                # with one less character (and we have a matching pair now)
                # then this pattern also matches
                matches[t][p] = matches[t - 1][p - 1]
            else:
                matches[t][p] = False  # no match, always false
    return matches[lent][lenp]  # return last matched pattern
