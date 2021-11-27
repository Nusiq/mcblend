'''
Functions related to exporting models.
'''
from __future__ import annotations

from copy import copy
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field

import numpy as np
import mathutils
import bpy
import bpy_types

from .common import (
    MINECRAFT_SCALE_FACTOR, McblendObject, McblendObjectGroup, MCObjType,
    CubePolygons, CubePolygon, MeshType
)
from .bedrock_packs import Vector2di, Vector3d, Vector3di
from .json_tools import get_vect_json
from .exception import ExporterException
from .uv import CoordinatesConverter

@dataclass
class ModelExport:
    '''
    Object that represents model during export.

    :param model_name: name of the model
    :param texture_width: Minecraft model property - texture_width.
    :param texture_height: Minecraft model property - texture_height.
    :param visible_bounds_offset: Minecraft model property -
        visible_bounds_offset.
    :param visible_bounds_width: Minecraft model property -
        visible_bounds_width.
    :param visible_bounds_height: Minecraft model property -
        visible_bounds_height.
    :param bones: Optional - list of :class:`BoneExport` objects that represent
        the bones of this model.
    '''
    model_name: str
    texture_width: int
    texture_height: int
    visible_bounds_offset: Vector3d
    visible_bounds_width: float
    visible_bounds_height: float
    bones: List[BoneExport] = field(default_factory=list)

    def load(self, object_properties: McblendObjectGroup):
        '''
        Populates the self.bones dictionary.

        :param object_properties: Group of mcblend objects.
        '''
        for _, objprop in object_properties.items():
            if objprop.mctype == MCObjType.BONE:
                self.bones.append(BoneExport(objprop, self))

    @staticmethod
    def json_outer() -> Dict:
        '''
        Returns the outer part of the Minecraft model 1.16.0 JSON file
        without any geometries.
        '''
        model: Dict = {
            "format_version": "1.16.0",
            "minecraft:geometry": []
        }
        return model

    def json_inner(self) -> Dict:
        '''
        Creates a dict with a geometry for the Minecraft 1.12.0 model JSON
        file (JSON path: [ROOT]->"minecraft:geometry"->int).

        :returns: Minecraft model JSON dict.
        '''
        result: Dict = {
            "description": {
                "identifier": f"geometry.{self.model_name}",
                "visible_bounds_width": round(self.visible_bounds_width, 3),
                "visible_bounds_height": round(self.visible_bounds_height, 3),
                "visible_bounds_offset": get_vect_json(
                    self.visible_bounds_offset)
            },
            "bones": [bone.json() for bone in self.bones]
        }
        if self.texture_width > 0:  # Don't export invalid values
            result["description"]["texture_width"] = self.texture_width
        if self.texture_height > 0:  # Don't export invalid values
            result["description"]["texture_height"] = self.texture_height
        return result

class BoneExport:
    '''
    Object that represents a Bone during model export.

    # Properties
    - `model: ModelExport` - a model that contains this bone.
    - `name: str` - the name of the bone.
    - `parent: Optional[str]` - the name of a parent of this bone
    - `rotation: np.ndarray` - rotation of the bone.
    - `pivot: np.ndarray` - pivot of the bone.
    - `cubes: List[CubeExport]` - list of cubes to export.
    - `locators: Dict[str, LocatorExport]` - list of locators to export.
      (if exists) or None
    - `mcblend_obj: McblendObject` - McblendObject of this bone.
    '''
    def __init__(self, bone: McblendObject, model: ModelExport):
        '''
        Creates BoneExport. If the input value mctype is McObjectType.BONE
        than ValueError is raised.
        '''
        self.model = model
        self.mcblend_obj = bone
        # Test if bone is valid input object
        if bone.mctype != MCObjType.BONE:
            raise ValueError('Input object is not a bone.')

        # Create cubes and locators list
        cubes: List[McblendObject] = []
        locators: List[McblendObject] = []

        # Add children cubes if they are MCObjType.CUBE type
        for child in bone.children:
            if child.mctype is MCObjType.CUBE:
                cubes.append(child)
            elif child.mctype is MCObjType.LOCATOR:
                locators.append(child)

        self.name: str = bone.obj_name
        self.parent: Optional[str] = (
            None if bone.parent is None else bone.parent.obj_name)
        self.rotation: np.ndarray = bone.get_mcrotation(bone.parent)
        self.pivot: np.ndarray = bone.mcpivot * MINECRAFT_SCALE_FACTOR
        self.cubes: List[CubeExport] = []
        self.poly_mesh: PolyMesh = PolyMesh()
        self.locators: Dict[str, LocatorExport] = {}
        self.load(bone, cubes, locators)

    def load(
            self, thisobj: McblendObject, cube_objs: List[McblendObject],
            locator_objs: List[McblendObject]):
        '''
        Used in constructor to cubes and locators.
        '''
        uv_factory = UvExportFactory(
            (self.model.texture_width, self.model.texture_height)
        )

        def _scale(objprop: McblendObject) -> np.ndarray:
            '''Scale of a bone'''
            _, _, scale = objprop.obj_matrix_world.decompose()
            return np.array(scale.xzy)

        # Set locators
        for locatorprop in locator_objs:
            _l_scale = _scale(locatorprop)
            l_pivot = locatorprop.mcpivot * MINECRAFT_SCALE_FACTOR
            l_origin = l_pivot + (
                locatorprop.mccube_position *
                _l_scale * MINECRAFT_SCALE_FACTOR
            )
            l_rot = locatorprop.get_mcrotation(thisobj)
            self.locators[locatorprop.obj_name] = LocatorExport(
                l_origin, l_rot, locatorprop)

        # Set cubes
        for cubeprop in cube_objs:
            if cubeprop.mesh_type is MeshType.CUBE:
                _c_scale = _scale(cubeprop)
                c_size = cubeprop.mcube_size * _c_scale * MINECRAFT_SCALE_FACTOR
                c_pivot = cubeprop.mcpivot * MINECRAFT_SCALE_FACTOR
                c_origin = c_pivot + (
                    cubeprop.mccube_position * _c_scale * MINECRAFT_SCALE_FACTOR
                )
                c_rot = cubeprop.get_mcrotation(thisobj)

                if cubeprop.inflate != 0:
                    c_size = c_size - cubeprop.inflate*2
                    c_origin = c_origin + cubeprop.inflate

                uv, uv_mirror = uv_factory.get_uv_export(cubeprop, c_size)

                cube = CubeExport(
                    size=c_size, pivot=c_pivot, origin=c_origin,
                    rotation=c_rot, inflate=cubeprop.inflate, uv=uv,
                    uv_mirror=uv_mirror, mcblend_obj=cubeprop)
                self.cubes.append(cube)
            elif cubeprop.mesh_type is MeshType.POLY_MESH:
                cubeprop.obj_data.calc_normals_split()
                polygons = cubeprop.obj_data.polygons  # loop ids and vertices
                vertices = cubeprop.obj_data.vertices  # crds
                loops = cubeprop.obj_data.loops  # normals
                if cubeprop.obj_data.uv_layers.active is None:
                    raise ExporterException(
                        f'{cubeprop.thisobj.name} - exporting polymesh '
                        'objects without UV-layer is not supported')
                uv_data = cubeprop.obj_data.uv_layers.active.data  # uv

                inv_bone_matrix = cubeprop.get_local_matrix(thisobj)

                positions: List[List[float]] = []
                normals: List[List[float]] = []
                polys: List[List[Vector3di]] = []
                uvs: List[List[int]] = [list(i.uv) for i in uv_data]
                for vertex in vertices:
                    transformed_vertex = inv_bone_matrix @ vertex.co
                    transformed_vertex = (
                        np.array(transformed_vertex) * MINECRAFT_SCALE_FACTOR *
                        np.array(thisobj.obj_matrix_world.to_scale())
                    )[[0, 2, 1]] + self.pivot
                    positions.append(list(transformed_vertex))
                for loop in loops:
                    # pylint: disable=assignment-from-no-return
                    transformed_normal = mathutils.Vector(
                            np.array(loop.normal)[[0, 2, 1]]
                    ).normalized()
                    normals.append(list(transformed_normal))
                for poly in polygons:
                    # vertex data -> List[(positions, normals, uvs)]
                    curr_poly: List[Vector3di] = []
                    for loop_id, vertex_id in zip(
                            poly.loop_indices, poly.vertices):
                        curr_poly.append((vertex_id, loop_id, loop_id))
                    if len(curr_poly) == 3:
                        curr_poly.append(copy(curr_poly[2]))
                    polys.append(curr_poly)
                self.poly_mesh.extend_mesh_data(
                    positions, normals, polys, uvs, cubeprop)

    def json(self) -> Dict:
        '''
        Returns the dictionary that represents a single mcbone in json file
        of model.

        # Returns:
        `Dict` - the single bone from Minecraft model.
        '''
        # Basic bone properties
        mcbone: Dict = {'name': self.name}
        if self.parent is not None:
            mcbone['parent'] = self.parent
        mcbone['pivot'] = get_vect_json(self.pivot)
        mcbone['rotation'] = get_vect_json(self.rotation)
        binding = self.mcblend_obj.this_pose_bone.mcblend.binding
        if binding != "":
            mcbone['binding'] = binding

        # Locators
        if len(self.locators) > 0:
            mcbone['locators'] = {}
            for name, locator in self.locators.items():
                mcbone['locators'][name] = locator.json()

        # Cubess
        if len(self.cubes) > 0:
            mcbone['cubes'] = []
            for cube in self.cubes:
                mcbone['cubes'].append(cube.json())
        if len(self.poly_mesh.polys) > 0:  # If not empty
            mcbone['poly_mesh'] = self.poly_mesh.json()
        return mcbone

@dataclass
class LocatorExport:
    '''Object that represents a Locator during model export.'''
    offset: np.ndarray
    rotation: np.ndarray
    mcblend_obj: McblendObject

    def json(self):
        '''Returns JSON representation of this object'''
        # The rotation must be evaluated early because of rounding errors
        export_rotation = [
            i if i != -180 else 180
            for i in get_vect_json(self.rotation)
        ]
        if export_rotation == [0, 0, 0]:
            return get_vect_json(self.offset)
        return {
            'offset': get_vect_json(self.offset),
            'rotation': export_rotation
        }

@dataclass
class CubeExport:
    '''Object that represents a cube during model export.'''
    size: np.ndarray
    pivot: np.ndarray
    origin: np.ndarray
    rotation: np.ndarray
    inflate: float
    uv: Any
    uv_mirror: bool
    mcblend_obj: McblendObject

    def json(self):
        '''Returns JSON representation of this object.'''
        cube_dict = {
            'uv': self.uv,
            'size': get_vect_json(self.size),
            'origin': get_vect_json(self.origin),
            'pivot': get_vect_json(self.pivot),
            'rotation': [  # Change -180 in rotations to 180
                i if i != -180 else 180
                for i in get_vect_json(self.rotation)
            ]
        }
        if self.inflate != 0:
            cube_dict['inflate'] = round(self.inflate, 3)
        if self.uv_mirror:
            cube_dict['mirror'] = True
        return cube_dict

class PolyMesh:
    '''Object that represents a poly_mesh of a bone.'''
    def __init__(self):
        self.positions: List[List[float]] = []
        self.normals: List[List[float]] = []
        self.uvs: List[List[int]] = []
        self.polys: List[List[List[int]]] = []
        self.normalized_uvs: bool = True
        self.mcblend_objs: List[McblendObject] = []

    def extend_mesh_data(
            self, positions: List[List[float]], normals: List[List[float]],
            polys: List[List[Vector3di]],
            uvs: List[List[int]], mcblend_obj: McblendObject):
        '''
        Extends the poly_mesh data with new vertices, normals, polys and uvs
        from another mesh.
        '''
        self.mcblend_objs.append(mcblend_obj)
        vertex_id_offset = len(self.positions)
        normal_id_offset = len(self.normals)
        loop_id_offset = len(self.uvs)

        self.positions.extend(positions)
        self.normals.extend(normals)
        self.uvs.extend(uvs)
        for poly in polys:
            curr_poly: List[List[int]] = []
            for vertex_data in poly:
                curr_poly.append([
                    vertex_data[0] + vertex_id_offset,  # position id
                    vertex_data[1] + normal_id_offset,  # normal id
                    vertex_data[2] + loop_id_offset,  # uv id
                ])
            self.polys.append(curr_poly)

    def json(self):
        '''Return part of the model JSON with poly_mesh object.'''
        poly_mesh = {
            'normalized_uvs': self.normalized_uvs,
            'positions': [get_vect_json(i) for i in self.positions],
            'normals': [get_vect_json(i) for i in self.normals],
            'uvs': [get_vect_json(i) for i in self.uvs],
            'polys': self.polys,
        }
        return poly_mesh

class UvExportFactory:
    '''
    Object used for creating the UvExport objects. Decides which subtype of the
    UvExport object should be used.
    '''
    def __init__(self, texture_size: Vector2di):
        self.blend_to_mc_converter = CoordinatesConverter(
            np.array([[0, 1], [1, 0]]),
            np.array([[0, texture_size[0]], [0, texture_size[1]]])
        )
        self.mc_to_blend_converter = CoordinatesConverter(
            np.array([[0, texture_size[0]], [0, texture_size[1]]]),
            np.array([[0, 1], [1, 0]])
        )

    def get_uv_export(
            self, mcobj: McblendObject,
            cube_size: np.ndarray) -> Tuple[Any, bool]:
        '''
        Creates uv properties for given McblendObject.

        :param mcobj: Object that needs UvExport.
        :param cube_size: Size of the cube expressed in Minecraft coordinates
            system.
        :returns: The JSON with UV, and the mirror property
        '''
        layer: Optional[bpy.types.MeshUVLoopLayer] = (
            mcobj.obj_data.uv_layers.active)
        if layer is None:  # Make sure that UV exists
            raise ExporterException(f'{mcobj.thisobj.name} - missing UV layer')

        polygons = mcobj.cube_polygons() # Can rise ExporterException
        try:
            return self._get_standard_cube_uv_export(
                polygons, layer, cube_size)
        except ExporterException:
            try:
                return self._get_per_face_uv_export(polygons, layer)
            except ExporterException as e:
                raise ExporterException(
                    f'{mcobj.thisobj.name} - {str(e)} - impossible to export'
                ) from e

    def _get_uv(
            self, uv_layer: bpy.types.MeshUVLoopLayer,
            cube_polygon: CubePolygon, name: str) -> np.ndarray:
        '''
        Get certain UV coordinates identified by a name from a face.

        :param cube_polygon: The face of the cube
        :param name: The identifier of a loop in the UV
        '''
        face: bpy_types.MeshPolygon = cube_polygon.side
        name_index = cube_polygon.orientation.index(name)

        uv_layer_data_index = face.loop_indices[name_index]
        return self.blend_to_mc_converter.convert(
            np.array(uv_layer.data[uv_layer_data_index].uv)
        )

    def _get_standard_cube_uv_export(
            self, cube_polygons: CubePolygons,
            uv_layer: bpy.types.MeshUVLoopLayer, cube_size: np.ndarray
        ) -> Tuple[Any, bool]:
        '''
        Attempts to return UV and mirror for standard UV-mapping. Raises
        ExporterException exception if this kind of mapping is impossible for
        given input.
        '''
        # Get min and max value of he loop coordinates
        loop_crds_list: List[np.ndarray] = []
        for loop in uv_layer.data:
            loop_crds_list.append(
                self.blend_to_mc_converter.convert(np.array(loop.uv))
            )
        loop_crds_arr: np.ndarray = np.vstack(loop_crds_list)
        min_loop_crds: np.ndarray = loop_crds_arr.min(0)  # type: ignore
        # max_loop_crds = loop_crds_arr.max(0)

        # Depth width height
        # first round with get_json_vect to avoid numerical errors and than
        # round down to int (like minecraft does).
        w, h, d = [
            int(i) for i in
            get_vect_json(cube_size)]
        expected_shape = np.array([
            [d, d + h],  # north/front LD 0
            [d + w, d + h],  # north/front RD 1
            [d + w, d],  # north/front RU 2
            [d, d],  # north/front LU 3
            [0, d + h],  # east/right LD 4
            [d, d + h],  # east/right RD 5
            [d, d],  # east/right RU 6
            [0, d],  # east/right LU 7
            [2 * d + w, d + h],  # south/back LD 8
            [2 * d + 2 * w, d + h],  # south/back RD 9
            [2 * d + 2 * w, d],  # south/back RU 10
            [2 * d + w, d],  # south/back LU 11
            [d + w, d + h],  # west/left LD 12
            [2 * d + w, d + h],  # west/left RD 13
            [2 * d + w, d],  # west/left RU 14
            [d + w, d],  # west/left LU 15
            [d, d],  # up/up LD 16
            [d + w, d],  # up/up RD 17
            [d + w, 0],  # up/up RU 18
            [d, 0],  # up/up LU 19
            [d + w, d],  # down/down LD 20
            [d + 2 * w, d],  # down/down RD 21
            [d + 2 * w, 0],  # down/down RU 22
            [d + w, 0],  # down/down LU 23
        ], dtype=np.float64)
        # Shift the expected values so they start from the minimal point
        # instead of 0
        expected_shape += min_loop_crds

        expected_shape_mirror = expected_shape[[
            1, 0, 3, 2,  # Mirror front
            13, 12, 15, 14,  # Mirror left (and swap with right)
            9, 8, 11, 10,  # Mirror back
            5, 4, 7, 6,  # Mirror right (and swap with left)
            17, 16, 19, 18,  # Mirror up
            21, 20, 23, 22,  # Mirror down
        ]]

        real_shape = np.array([
            self._get_uv(uv_layer, cube_polygons.north, '---'),  # north/front LD
            self._get_uv(uv_layer, cube_polygons.north, '+--'),  # north/front RD
            self._get_uv(uv_layer, cube_polygons.north, '+-+'),  # north/front RU
            self._get_uv(uv_layer, cube_polygons.north, '--+'),  # north/front LU
            self._get_uv(uv_layer, cube_polygons.east, '-+-'),  # east/right LD
            self._get_uv(uv_layer, cube_polygons.east, '---'),  # east/right RD
            self._get_uv(uv_layer, cube_polygons.east, '--+'),  # east/right RU
            self._get_uv(uv_layer, cube_polygons.east, '-++'),  # east/right LU
            self._get_uv(uv_layer, cube_polygons.south, '++-'),  # south/back LD
            self._get_uv(uv_layer, cube_polygons.south, '-+-'),  # south/back RD
            self._get_uv(uv_layer, cube_polygons.south, '-++'),  # south/back RU
            self._get_uv(uv_layer, cube_polygons.south, '+++'),  # south/back LU
            self._get_uv(uv_layer, cube_polygons.west, '+--'),  # west/left LD
            self._get_uv(uv_layer, cube_polygons.west, '++-'),  # west/left RD
            self._get_uv(uv_layer, cube_polygons.west, '+++'),  # west/left RU
            self._get_uv(uv_layer, cube_polygons.west, '+-+'),  # west/left LU
            self._get_uv(uv_layer, cube_polygons.up, '--+'),  # up/up LD
            self._get_uv(uv_layer, cube_polygons.up, '+-+'),  # up/up RD
            self._get_uv(uv_layer, cube_polygons.up, '+++'),  # up/up RU
            self._get_uv(uv_layer, cube_polygons.up, '-++'),  # up/up LU
            self._get_uv(uv_layer, cube_polygons.down, '---'),  # down/down LD
            self._get_uv(uv_layer, cube_polygons.down, '+--'),  # down/down RD
            self._get_uv(uv_layer, cube_polygons.down, '++-'),  # down/down RU
            self._get_uv(uv_layer, cube_polygons.down, '-+-'),  # down/down LU
        ], dtype=np.float64)

        mirror = False
        if not np.isclose(expected_shape, real_shape).all():
            if not np.isclose(expected_shape_mirror, real_shape).all():
                raise ExporterException()
            mirror = True

        # Return the JSON and mirror
        return [round(i, 3) for i in min_loop_crds], mirror

    def _get_per_face_uv_export(
            self, cube_polygons: CubePolygons,
            uv_layer: bpy.types.MeshUVLoopLayer) -> Tuple[Any, bool]:
        result = {}

        def map_face(cube_polygon: CubePolygon, side_name: str):
            crds = cube_polygon.uv_layer_coordinates(uv_layer)

            # If fully out of the texture
            if ((crds < 0) | (crds > 1)).all():
                return
            is_valid, _, _ = (
                CubePolygon.validate_rectangle_uv(crds))
            if not is_valid:
                raise ExporterException(
                    f'{side_name} face has invalid UV-mapping')

            left_top = self.blend_to_mc_converter.convert(crds[3])
            right_bottom = self.blend_to_mc_converter.convert(crds[1])

            result[side_name] = {
                "uv": [round(i, 3) for i in left_top],
                "uv_size": [round(i, 3) for i in right_bottom-left_top],
            }

        map_face(cube_polygons.north, "north")
        map_face(cube_polygons.east, "east")
        map_face(cube_polygons.south, "south")
        map_face(cube_polygons.west, "west")
        map_face(cube_polygons.up, "up")
        map_face(cube_polygons.down, "down")

        return result, False
