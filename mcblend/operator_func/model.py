'''
Functions related to exporting models.
'''
from __future__ import annotations

from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field

import numpy as np

import bpy
import bpy_types

from .common import (
    MINECRAFT_SCALE_FACTOR, McblendObject, McblendObjectGroup, MCObjType,
    CubePolygons, CubePolygon
)
from .json_tools import get_vect_json
from .exception import NoCubePolygonsException, NotAStandardUvException
from .uv import CoordinatesConverter


@dataclass
class ModelExport:
    '''
    Object that represents model during export.

    # Properties:
    - `model_name: str` - name of the model
    - `texture_width: int` - texture width Minecraft property
    - `texture_height: int` - texture height Minecraft property
    '''
    model_name: str
    texture_width: int
    texture_height: int
    visible_bounds_offset: Tuple[float, float, float]
    visible_bounds_width: float
    visible_bounds_height: float
    bones: List[BoneExport] = field(default_factory=list)

    def load(
            self, object_properties: McblendObjectGroup,
            context: bpy_types.Context
        ):
        '''
        Populates the self.poses dictionary.

        # Properties:
        - `object_properties: McblendObjectGroup` - the
        properties of all of the Minecraft cubes and bones.
        - `context: bpy_types.Context` - the context of running the operator.
        '''
        bpy.ops.screen.animation_cancel()
        original_frame = context.scene.frame_current
        try:
            context.scene.frame_set(0)
            for _, objprop in object_properties.items():
                if objprop.mctype in [MCObjType.BONE, MCObjType.BOTH]:
                    self.bones.append(BoneExport(objprop, self))
        finally:
            context.scene.frame_set(original_frame)

    def json(self) -> Dict:
        '''
        Creates a dictionary that represents the Minecraft model JSON file.

        # Returns:
        `Dict` - Minecraft model.
        '''
        result: Dict = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": f"geometry.{self.model_name}",
                        "visible_bounds_width": round(self.visible_bounds_width, 3),
                        "visible_bounds_height": round(self.visible_bounds_height, 3),
                        "visible_bounds_offset": get_vect_json(self.visible_bounds_offset)
                    },
                    "bones": [bone.json() for bone in self.bones]
                }
            ]
        }
        if self.texture_width > 0:  # Dont't export invalid values
            result["minecraft:geometry"][0]["description"][
                "texture_width"] = self.texture_width
        if self.texture_height > 0:  # Dont't export invalid values
            result["minecraft:geometry"][0]["description"][
                "texture_height"] = self.texture_height
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

    '''
    def __init__(self, bone: McblendObject, model: ModelExport):
        '''
        Creates BoneExport. If the input value of BONE or BOTH McObjectType
        than ValueError is raised.
        '''
        self.model = model
        # Test if bone is valid input object
        if bone.mctype not in [MCObjType.BONE, MCObjType.BOTH]:
            raise ValueError('Input object is not a bone.')

        # Create cubes and locators list
        cubes: List[McblendObject] = []
        if bone.mctype == MCObjType.BOTH:  # Else MCObjType == BOTH
            cubes.append(bone)
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
            self.locators[locatorprop.obj_name] = LocatorExport(l_origin)

        # Set cubes
        for cubeprop in cube_objs:
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

            uv = uv_factory.get_uv_export(cubeprop, c_size)

            cube = CubeExport(
                size=c_size, pivot=c_pivot, origin=c_origin,
                rotation=c_rot, inflate=cubeprop.inflate, uv=uv)
            self.cubes.append(cube)


    def json(self) -> Dict:
        '''
        Returns the dictionary that represents a single mcbone in json file
        of model.

        # Returns:
        `Dict` - the single bone from Minecraft model.
        '''
        # Basic bone properties
        mcbone: Dict = {'name': self.name, 'cubes': []}
        if self.parent is not None:
            mcbone['parent'] = self.parent
        mcbone['pivot'] = get_vect_json(self.pivot)
        mcbone['rotation'] = get_vect_json(self.rotation)

        # Locators
        if len(self.locators) > 0:
            mcbone['locators'] = {}
            for name, locator in self.locators.items():
                mcbone['locators'][name] = locator.json()

        # Cubess
        for cube in self.cubes:
            mcbone['cubes'].append(cube.json())

        return mcbone

@dataclass
class LocatorExport:
    '''Object that represents a Locator during model export.'''
    origin: np.ndarray

    def json(self):
        '''Returns json representation of this object'''
        return get_vect_json(self.origin)

@dataclass
class CubeExport:
    '''Object that represents a cube during model export.'''
    size: np.ndarray
    pivot: np.ndarray
    origin: np.ndarray
    rotation: np.ndarray
    inflate: float
    uv: UvExport

    def json(self):
        '''Returns json representation of this object'''
        cube_dict = {
            'uv': self.uv.json(),
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
        if self.uv.mirror:
            cube_dict['mirror'] = True
        return cube_dict

class UvExport:
    '''
    Base class for creating the UV part of exported cube.
    '''
    def __init__(self):
        # Mirror is used only for StandardCubeUvExport but any other UV has to
        # be able to return False when asked about mirror property
        self.mirror = False

    def json(self) -> Any:
        '''
        Returns josonable object that represents a single uv of a cube in
        Minecraft model.
        '''
        # pylint: disable=no-self-use
        return [0, 0]

class PerFaceUvExport(UvExport):
    '''
    UvExport for per face UV-mapping (the uv mapping of a cube which maps
    every UV face separately).
    '''
    def __init__(
            self, cube_polygons: CubePolygons,
            uv_layer: bpy.types.MeshUVLoopLayer,
            blend_to_mc_converter: CoordinatesConverter):
        super().__init__()
        self.cube_polygons = cube_polygons
        self.uv_layer = uv_layer
        self.converter = blend_to_mc_converter

    def json(self):
        result = {}

        if not self._is_face_uv_outside(self.cube_polygons.north):
            result["north"] = self._one_face_uv(
                self.cube_polygons.north, '--+', '+--')
        if not self._is_face_uv_outside(self.cube_polygons.east):
            result["east"] = self._one_face_uv(
                self.cube_polygons.east, '-++', '---')
        if not self._is_face_uv_outside(self.cube_polygons.south):
            result["south"] = self._one_face_uv(
                self.cube_polygons.south, '+++', '-+-')
        if not self._is_face_uv_outside(self.cube_polygons.west):
            result["west"] = self._one_face_uv(
                self.cube_polygons.west, '+-+', '++-')
        if not self._is_face_uv_outside(self.cube_polygons.up):
            result["up"] = self._one_face_uv(
                self.cube_polygons.up, '-++', '+-+')
        if not self._is_face_uv_outside(self.cube_polygons.down):
            result["down"] = self._one_face_uv(
                self.cube_polygons.down, '+--', '-+-')

        return result

    def _is_face_uv_outside(self, cube_polygon):
        '''Tests if UV face is completly outside of the texture'''
        face: bpy_types.MeshPolygon = cube_polygon.side
        for loop_index in face.loop_indices:
            curr_loop = np.array(self.uv_layer.data[loop_index].uv)
            if not ((curr_loop < 0).any() or (curr_loop > 1).any()):
                return False  # Something isn't outside
        return True  # Went through the loop (everything is outside)

    def _one_face_uv(
            self, cube_polygon: CubePolygon, corner1_name: str,
            corner2_name: str) -> Dict:
        face: bpy_types.MeshPolygon = cube_polygon.side
        corner1_index = cube_polygon.orientation.index(corner1_name)
        corner2_index = cube_polygon.orientation.index(corner2_name)

        corner1_crds = np.array(self.converter.convert(
            self.uv_layer.data[face.loop_indices[corner1_index]].uv
        ))
        corner2_crds = np.array(self.converter.convert(
            self.uv_layer.data[face.loop_indices[corner2_index]].uv
        ))
        uv = corner1_crds
        uv_size = corner2_crds-corner1_crds

        return {
            "uv": [round(i, 3) for i in uv],
            "uv_size": [round(i, 3) for i in uv_size],
        }

class StandardCubeUvExport(UvExport):
    '''
    Class for standard Minecraft UV-mapping:
    Single vector with UV-values (the shape of the faces is implicitly
    determined by the dimensions of the cuboid)
    '''
    def __init__(
            self, cube_polygons: CubePolygons,
            uv_layer: bpy.types.MeshUVLoopLayer, cube_size: np.array,
            blend_to_mc_converter: CoordinatesConverter):
        super().__init__()
        self.cube_size = cube_size
        self.cube_polygons = cube_polygons
        self.uv_layer = uv_layer
        self.converter = blend_to_mc_converter

        # test if the shape of the  UV is the standard Minecraft shape
        self.assert_standard_uv_shape()

    def _uv_from_name(
            self, cube_polygon: CubePolygon, name: str) -> np.ndarray:
        '''
        Helper function used to get certain UV coordinates from a face by
        its name.
        '''
        face: bpy_types.MeshPolygon = cube_polygon.side
        name_index = cube_polygon.orientation.index(name)

        uv_layer_data_index = face.loop_indices[name_index]
        return self.converter.convert(
            np.array(self.uv_layer.data[uv_layer_data_index].uv)
        )

    def assert_standard_uv_shape(self):
        '''Asserts that this object has cubic shape'''
        # Get min and max value of he loop coordinates
        loop_crds_list: List[np.array] = []
        for loop in self.uv_layer.data:
            loop_crds_list.append(
                self.converter.convert(np.array(loop.uv))
            )
        loop_crds_arr: np.ndarray = np.vstack(loop_crds_list)
        min_loop_crds = loop_crds_arr.min(0)
        # max_loop_crds = loop_crds_arr.max(0)

        # Depth width height
        # first round with get_json_vect to avoid numerical errors and than
        # round down to int (like minecraft does).
        w, h, d = [
            int(i) for i in
            get_vect_json(self.cube_size)]
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
            self._uv_from_name(self.cube_polygons.north, '---'),  # north/front LD
            self._uv_from_name(self.cube_polygons.north, '+--'),  # north/front RD
            self._uv_from_name(self.cube_polygons.north, '+-+'),  # north/front RU
            self._uv_from_name(self.cube_polygons.north, '--+'),  # north/front LU
            self._uv_from_name(self.cube_polygons.east, '-+-'),  # east/right LD
            self._uv_from_name(self.cube_polygons.east, '---'),  # east/right RD
            self._uv_from_name(self.cube_polygons.east, '--+'),  # east/right RU
            self._uv_from_name(self.cube_polygons.east, '-++'),  # east/right LU
            self._uv_from_name(self.cube_polygons.south, '++-'),  # south/back LD
            self._uv_from_name(self.cube_polygons.south, '-+-'),  # south/back RD
            self._uv_from_name(self.cube_polygons.south, '-++'),  # south/back RU
            self._uv_from_name(self.cube_polygons.south, '+++'),  # south/back LU
            self._uv_from_name(self.cube_polygons.west, '+--'),  # west/left LD
            self._uv_from_name(self.cube_polygons.west, '++-'),  # west/left RD
            self._uv_from_name(self.cube_polygons.west, '+++'),  # west/left RU
            self._uv_from_name(self.cube_polygons.west, '+-+'),  # west/left LU
            self._uv_from_name(self.cube_polygons.up, '--+'),  # up/up LD
            self._uv_from_name(self.cube_polygons.up, '+-+'),  # up/up RD
            self._uv_from_name(self.cube_polygons.up, '+++'),  # up/up RU
            self._uv_from_name(self.cube_polygons.up, '-++'),  # up/up LU
            self._uv_from_name(self.cube_polygons.down, '---'),  # down/down LD
            self._uv_from_name(self.cube_polygons.down, '+--'),  # down/down RD
            self._uv_from_name(self.cube_polygons.down, '++-'),  # down/down RU
            self._uv_from_name(self.cube_polygons.down, '-+-'),  # down/down LU
        ], dtype=np.float64)

        if not np.isclose(expected_shape, real_shape).all():
            if not np.isclose(expected_shape_mirror, real_shape).all():
                raise NotAStandardUvException()
            self.mirror = True

    def json(self):
        loop_crds_list: List[np.array] = []
        for loop in self.uv_layer.data:
            loop_crds_list.append(
                self.converter.convert(np.array(loop.uv))
            )
        loop_crds_arr: np.ndarray = np.vstack(loop_crds_list)
        min_loop_crds = loop_crds_arr.min(0)
        return [round(i, 3) for i in min_loop_crds]

class UvExportFactory:
    '''
    Used for creating the UvExport objects. Decides which subtype of the
    UvExport object should be used.
    '''
    def __init__(self, texture_size: Tuple[int, int]):
        self.blend_to_mc_converter = CoordinatesConverter(
            np.array([[0, 1], [1, 0]]),
            np.array([[0, texture_size[0]], [0, texture_size[1]]])
        )
        self.mc_to_blend_converter = CoordinatesConverter(
            np.array([[0, texture_size[0]], [0, texture_size[1]]]),
            np.array([[0, 1], [1, 0]])
        )

    def get_uv_export(
            self, mcobj: McblendObject, cube_size: np.ndarray) -> UvExport:
        '''
        Creates UvExport object for given MclbendObject.

        - `mcobj: McblendObject` - object that needs UvExport
        - `cube_size: np.ndarray` - size of the cube in minecraft coordinates
          system
        '''
        layer: Optional[bpy.types.MeshUVLoopLayer] = (
            mcobj.obj_data.uv_layers.active)
        if layer is None:  # Make sure that UV exists
            return UvExport()
        try:
            polygons = mcobj.cube_polygons()
        except NoCubePolygonsException:
            return UvExport()
        try:
            return StandardCubeUvExport(
                polygons, layer, cube_size, self.blend_to_mc_converter)
        except NotAStandardUvException:
            return PerFaceUvExport(polygons, layer, self.blend_to_mc_converter)
