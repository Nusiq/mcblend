'''
Functions related to exporting models.
'''
from __future__ import annotations

from typing import List, Dict, Tuple, Any, NamedTuple, Deque, Optional
from dataclasses import dataclass, field
from collections import deque

import numpy as np

import bpy
import bpy_types

from .common import (
    MINECRAFT_SCALE_FACTOR, McblendObject, McblendObjectGroup, MCObjType,
    cyclic_equiv, CubePolygons, CubePolygon
)
from .json_tools import get_vect_json
from .exception import NoCubePolygonsException
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
                try:
                    self.bones.append(BoneExport(objprop, self))
                except ValueError:
                    pass
        finally:
            context.scene.frame_set(original_frame)

    def json(self) -> Dict:
        '''
        Creates a dictionary that represents the Minecraft model JSON file.

        # Returns:
        `Dict` - Minecraft model.
        '''
        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": f"geometry.{self.model_name}",
                        "texture_width": self.texture_width,
                        "texture_height": self.texture_height,
                        "visible_bounds_width": 10,
                        "visible_bounds_height": 10,
                        "visible_bounds_offset": [0, 2, 0]
                    },
                    "bones": [bone.json() for bone in self.bones]
                }
            ]
        }


class BoneExport:
    '''
    Object that represents a Bone during model export.
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

        # Set fields values
        self.thisobj = bone
        self.cube_objs = cubes
        self.locator_objs = locators

        # Load other properties
        # name ,parent ,pivot ,rotation,
        # cubes: List[size, pivot, origin, rotation, inflate, mirror, uv],
        # locators: Dict[origin],
        self.load()

    def load(self):
        # TODO - documentation

        # Prepare lists, dictionaries etc.
        self.cubes: List[CubeExport] = []
        self.locators: Dict[str, LocatorExport] = {}
        uv_factory = UvExportFactory(
            (self.model.texture_width, self.model.texture_height)
        )

        def _scale(objprop: McblendObject) -> np.ndarray:
            '''Scale of a bone'''
            _, _, scale = objprop.obj_matrix_world.decompose()
            return np.array(scale.xzy)

        # Set name
        self.name = self.thisobj.obj_name

        # Set parent
        if self.thisobj.parent is not None:
            self.parent: Optional[str] = self.thisobj.parent.obj_name
        else:
            self.parent = None

        # Set rotation and pivot
        b_rot = self.thisobj.get_mcrotation(self.thisobj.parent)
        b_pivot = self.thisobj.mcpivot * MINECRAFT_SCALE_FACTOR
        self.pivot = b_pivot
        self.rotation = b_rot

        # Set locators
        for locatorprop in self.locator_objs:
            _l_scale = _scale(locatorprop)
            l_pivot = locatorprop.mcpivot * MINECRAFT_SCALE_FACTOR
            l_origin = l_pivot + (
                locatorprop.mccube_position *
                _l_scale * MINECRAFT_SCALE_FACTOR
            )
            self.locators[locatorprop.obj_name] = LocatorExport(l_origin)

        # Set cubes
        for cubeprop in self.cube_objs:
            _c_scale = _scale(cubeprop)
            c_size = cubeprop.mcube_size * _c_scale * MINECRAFT_SCALE_FACTOR
            c_pivot = cubeprop.mcpivot * MINECRAFT_SCALE_FACTOR
            c_origin = c_pivot + (
                cubeprop.mccube_position * _c_scale * MINECRAFT_SCALE_FACTOR
            )
            c_rot = cubeprop.get_mcrotation(self.thisobj)

            if cubeprop.mc_inflate != 0:
                c_size = c_size - cubeprop.mc_inflate*2
                c_origin = c_origin + cubeprop.mc_inflate

            uv = uv_factory.get_uv_export(cubeprop)

            cube = CubeExport(size=c_size, pivot=c_pivot, origin=c_origin,
                    rotation=c_rot, inflate=cubeprop.mc_inflate,
                    mirror=cubeprop.mc_mirror, uv=uv)
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
    # TODO - documentation
    origin: np.ndarray

    def json(self):
        # TODO - documentation
        return get_vect_json(origin)

@dataclass
class CubeExport:
    # TODO - documentation
    size: np.ndarray
    pivot: np.ndarray
    origin: np.ndarray
    rotation: np.ndarray
    inflate: float
    mirror: bool
    uv: UvExport

    def json(self):
        # TODO - documentation
        cube_dict = {
            'uv': self.uv.json(),
            'size': [round(i) for i in get_vect_json(self.size)],
            'origin': get_vect_json(self.origin),
            'pivot': get_vect_json(self.pivot),
            'rotation': [  # Change -180 in rotations to 180
                i if i != -180 else 180
                for i in get_vect_json(self.rotation)
            ]
        }
        if self.inflate != 0:
            cube_dict['inflate'] = self.inflate
        if self.mirror:
            cube_dict['mirror'] = True
        return cube_dict

class UvExport:
    '''
    Base class for creating the UV part of exported cube.
    '''
    def json(self) -> Any:
        '''
        Returns josonable object that represents a single uv of a cube in
        Minecraft model.
        '''
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
        return {
            "north": self._one_face_uv(self.cube_polygons.north, '--+', '+--'),
            "east": self._one_face_uv(self.cube_polygons.east, '-++', '---'),
            "south": self._one_face_uv(self.cube_polygons.south, '+++', '-+-'),
            "west": self._one_face_uv(self.cube_polygons.west, '+-+', '++-'),
            "up": self._one_face_uv(self.cube_polygons.up, '-++', '+-+'),
            "down": self._one_face_uv(self.cube_polygons.down, '+--', '-+-')
        }

    def _one_face_uv(self, cube_polygon: CubePolygon, corner1_name: str,
            corner2_name: str) -> Dict:
        face: bpy_types.MeshPolygon = cube_polygon.side
        corner1_index = cube_polygon.order.index(corner1_name)
        corner2_index = cube_polygon.order.index(corner2_name)

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

# class CubeUvExport(UvExport):
#     '''
#     Class for standard Minecraft UV-mapping:
#     Single vector with UV-values (the shape of the faces is implicitly
#     determined by the dimensions of the cuboid)
#     '''

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

    def get_uv_export(self, mcobj: McblendObject) -> UvExport:
        try:
            polygons = mcobj.cube_polygons()
            return PerFaceUvExport(
                polygons, mcobj.obj_data.uv_layers.active,
                self.blend_to_mc_converter
            )
        except NoCubePolygonsException as e:
            return UvExport()
