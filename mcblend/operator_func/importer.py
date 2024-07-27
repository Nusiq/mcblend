'''
Functions and objects related to importing Minecraft models to Blender.
'''
from __future__ import annotations

import math  # pyright: ignore[reportShadowedImports]
from typing import (
    Dict, List, Optional, Any, Tuple, Set, Union, TYPE_CHECKING, cast)
from enum import Enum

import numpy as np

import mathutils
from bpy.types import (
    Object, MeshUVLoopLayer, Armature, ArmatureEditBones, Mesh)
import bpy

from .common import (
    MINECRAFT_SCALE_FACTOR, CubePolygons, CubePolygon, MeshType)
from .extra_types import Vector3di, Vector3d, Vector2d
from .uv import CoordinatesConverter
from .exception import ImporterException
from .typed_bpy_access import get_mcblend

class ErrorLevel(Enum):
    '''
    Used by ModelLoader to indicate that certain errors should break execution
    or just show a warning.
    '''
    ERROR = 0
    WARNING = 1

def pick_version_parser(parsers: Tuple[str, ...], version: str):
    '''
    Picks the earliest possible format_version greater or equal to the known
    version ot of list of parser names for different format versions.

    :param parsers: The list of format_versions that identify the parser to
        use for parsing an object.
    '''
    def to_tuple(version: str) -> Tuple[int]:
        try:
            return tuple(  # type: ignore
                map(int, version.split('.')))
        except Exception as e:
            raise ImporterException(
                f'Unable to parse format version number: {version}') from e

    t_parsers = [to_tuple(parser) for parser in parsers]
    t_parsers.sort(reverse=True)
    t_version = to_tuple(version)

    best_choice = None
    for t_parser in t_parsers:
        if t_parser <= t_version:
            best_choice = t_parser
            break
    if best_choice is None:
        raise ImporterException(
            f'Unsupported format version: {version}')
    return '.'.join([str(i) for i in best_choice])


class ModelLoader:
    '''
    Interface loads model from a JSON dict with Minecraft model.
    Fills missing, optional data with default values.

    :param data: The JSON dict with models file.
    :param geometry_name: Optional - the name of the geometry to load.
    '''
    data: dict[str, Any]
    warnings: list[str]
    format_version: str
    parser_version: str
    geometry: dict[str, Any]
    geometry_path: list[str | int]

    def __init__(self, data: dict[str, Any], geometry_name: str = ""):
        self.data = data
        # List of warnings about problems related to loading the model
        self.warnings = []
        self.format_version, self.parser_version = self._load_format_version(
            data)
        geometry, geometry_path = self._load_geometry(
            geometry_name, self.data)

        self.description = self._load_description(
            geometry, geometry_path)
        self.bones = self._load_bones(
            geometry['bones'], geometry_path + ['bones'])

    def append_warning(self, warning: str, json_path: List[Union[str, int]]):
        '''Appends warning about problem with model loading.'''
        nice_path = '->'.join([str(i) for i in json_path])
        self.warnings.append(f'{nice_path}::{warning}')

    def _error_level_handler(
            self, message: str, error_level: ErrorLevel=ErrorLevel.ERROR):
        '''
        Adds warning or rises an exception with the message, based on the error
        level.
        '''
        if error_level == ErrorLevel.ERROR:
            raise ImporterException(message)
        self.warnings.append(message)

    def _assert_vector_type(
            self, name: str, obj: Any, length: int, types: Tuple[type, ...],
            json_path: List[str | int], error_level: ErrorLevel=ErrorLevel.ERROR,
            more: str=""
        ) -> bool:
        '''
        Asserts that object is an array of specific length with specific type
        of items.
        If assertion fails:
        - when error level is ERROR, rises an exception.
        - when error level is WARNING, appends warning and returns False.
        otherwise returns True.
        '''
        if not isinstance(obj, list):
            nice_path = '->'.join([str(i) for i in json_path])
            msg = f'{nice_path}::{name} is not a list.'
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        obj = cast(List, obj)  # type: ignore
        if not len(obj) == length:
            nice_path = '->'.join([str(i) for i in json_path])
            msg = (
                f'{nice_path}::{name} has invalid length '
                f'{len(obj)} != {length}.'
            )
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        if not all(isinstance(i, types) for i in obj):
            nice_path = '->'.join([str(i) for i in json_path])
            msg = f'{nice_path}::{name} is not instance of 'f'List[{types}].'
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        return True

    def _assert_required_keys(
            self, what: str, has_keys: Set[str], required_keys: Set[str],
            json_path: List[str | int], error_level: ErrorLevel=ErrorLevel.ERROR,
            more: str="") -> bool:
        '''
        Asserts that object has required keys.
        If assertion fails:
        - when error level is ERROR, rises an exception.
        - when error level is WARNING, appends warning and returns False.
        otherwise returns True.
        '''
        missing_keys = required_keys - has_keys
        if len(missing_keys) != 0:
            nice_path = '->'.join([str(i) for i in json_path])
            msg = f'{nice_path}::{what} is missing properties: {missing_keys}.'
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        return True

    def _assert_type(
            self, name: str, obj: Any, types: Tuple[Any, ...],
            json_path: List[str | int],
            error_level: ErrorLevel=ErrorLevel.ERROR, more: str="") -> bool:
        '''
        Asserts that object is instance of specific type.
        If assertion fails:
        - when error level is ERROR, rises an exception.
        - when error level is WARNING, appends warning and returns False.
        otherwise returns True.
        '''
        if not isinstance(obj, types):
            nice_path = '->'.join([str(i) for i in json_path])
            if len(types) == 1:
                msg = (
                    f'{nice_path}::{name} ({type(name)}) is not instance of '
                    f'{types[0]}.'
                )
                if more:
                    msg += f' {more}'
                self._error_level_handler(msg, error_level)
            else:
                msg = (
                    f'{nice_path}::{name} ({type(name)}) is not instance of '
                    f'any of the acceptable types: {types}.'
                )
                if more:
                    msg += f' {more}'
                self._error_level_handler(msg, error_level)
            return False
        return True

    def _assert_acceptable_keys(
            self, what: str, has_keys: Set[str], accepted_keys: Set[str],
            json_path: List[str | int],
            error_level: ErrorLevel=ErrorLevel.ERROR,
            more: str="") -> bool:
        '''
        Appends warning if object have keys that aren't in the accepted set.
        If assertion fails:
        - when error level is ERROR, rises an exception.
        - when error level is WARNING, appends warning and returns False.
        otherwise returns True.
        '''
        additional_keys = has_keys - accepted_keys
        nice_path = '->'.join([str(i) for i in json_path])
        if len(additional_keys) > 1:
            msg = (
                f'{nice_path}::{what} has unexpected properties: '
                f'{", ".join(additional_keys)}.')
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        if len(additional_keys) == 1:
            msg = (
                f'{nice_path}::{what} has unexpected '
                f'property: {additional_keys.pop()}.'
            )
            if more:
                msg += f' {more}'
            self._error_level_handler(msg, error_level)
            return False
        return True

    def _load_format_version(self, data: Dict[str, Any]) -> Tuple[str, str]:
        '''
        Returns the version of the model from JSON file loaded into data.

        :param data: JSON dict with model file.
        '''
        if 'format_version' in data:
            parser_version = pick_version_parser(
                ('1.16.0', '1.12.0', '1.8.0'), data['format_version'])
            true_format_version = data['format_version']
        elif 'minecraft:geometry' in data:  # Based on files structure
            parser_version = '1.16.0'
            true_format_version = '1.16.0'
        else:  # Based on files structure
            parser_version = '1.8.0'
            true_format_version = '1.8.0'

        if parser_version in ('1.16.0', '1.12.0'):
            self._assert_required_keys(
                'model file', set(data.keys()),
                {'minecraft:geometry'}, [])
            self._assert_acceptable_keys(
                'model file', set(data.keys()),
                {'minecraft:geometry', 'format_version', 'cape'}, [],
                ErrorLevel.WARNING)
            return true_format_version, parser_version
        if parser_version == '1.8.0':
            # All geometries must start with geometry.
            for k in data.keys():  # key must be string because its from json
                if not (
                        k.startswith('geometry.') or
                        k in ['debug', 'format_version']):
                    self.append_warning(
                        "Invalid geomtetry name. All 1.8.0 model names must "
                        "start with 'geometry.' prefix.", [k])
            return true_format_version, parser_version
        raise ImporterException('Unsupported format version')

    def _load_geometry(
            self, geometry_name: str,
            data: Any) -> Tuple[Dict[str, Any], List[str | int]]:
        '''
        Finds and returns geometry with specific name from list of geometries
        from JSON dict with models. Returns the geometry dict with
        all of the missing default values added and the JSON path to the
        geometry.

        :param geometry_name: The name of geometry
        :param data: Root object of the JSON.
        '''
        if self.parser_version in ('1.16.0', '1.12.0'):
            result = None
            geometries = data['minecraft:geometry']
            path: List[str | int] = ['minecraft:geometry']
            self._assert_type(
                'geometries', geometries, (list,), path)  # type: ignore
            for i, geometry in enumerate(geometries):
                path = ['minecraft:geometry', i]
                if not self._assert_type(
                        'geometry', geometry, (dict,), path,  # type: ignore
                        ErrorLevel.WARNING):
                    continue
                if not self._assert_required_keys(
                        'geometry', set(geometry.keys()),
                        {'description', 'bones'}, path, ErrorLevel.WARNING):
                    continue
                self._assert_acceptable_keys(
                    'geometry', set(geometry.keys()), {'description', 'bones'},
                    path, ErrorLevel.WARNING)
                desc = geometry['description']
                if 'identifier' not in desc:
                    self.append_warning(
                        "description is missing identifier", path)
                    continue
                identifier = desc['identifier']
                if geometry_name  == '' and result is None:
                    result = geometry, path
                elif geometry_name == identifier:
                    result = geometry, path
            # Return from 1.16.0 or 1.12.0
            if result is not None:
                return result
            raise ImporterException(
                f'Unable to find geometry called geometry.{geometry_name}')

        if self.parser_version == '1.8.0':
            result = None
            geometries = data
            path = []
            self._assert_type(
                'geometries', geometries, (dict,), path)  # type: ignore
            for k, geometry in geometries.items():
                if k in ('format_version', 'debug'):
                    continue
                path = [k]
                if not self._assert_type(
                        'geometry', geometry, (dict,), # type: ignore
                        path, ErrorLevel.WARNING):
                    continue
                self._assert_acceptable_keys(
                    'geometry', set(geometry.keys()),
                    {
                        "debug", "visible_bounds_width",
                        "visible_bounds_height", "visible_bounds_offset",
                        "texturewidth", "textureheight", "cape", "bones"
                    }, path, ErrorLevel.WARNING)
                identifier = k
                if geometry_name  == '' and result is None:
                    result = geometry, path
                elif geometry_name == identifier:
                    result = geometry, path
            # Return from 1.8.0
            if result is not None:
                return result
            raise ImporterException(
                f'Unable to find geometry called geometry.{geometry_name}')
        raise ImporterException(
            f'Unsupported format version: {self.format_version}')

    def _load_description(self, geometry: Any, geometry_path: List[str | int]) -> Dict[str, Any]:
        '''
        Returns the description of the geometry.

        :param geometry: The geometry with description.
        :param geometry_path: The JSON path to the geometry (used for error
            messages)
        '''
        result: Dict[str, Any] = {
            "texture_width" : 64,
            "texture_height" : 64,
            "visible_bounds_offset" : [0.0, 0.0, 0.0],
            "visible_bounds_width" : 1,
            "visible_bounds_height": 1
        }
        if self.parser_version in ('1.16.0', '1.12.0'):
            desc = geometry['description']
            path = geometry_path + ['description']

            self._assert_required_keys(
                'description', set(desc.keys()), {'identifier'}, path)
            acceptable_keys = {
                'identifier', 'texture_width', 'texture_height',
                'visible_bounds_offset', 'visible_bounds_width',
                'visible_bounds_height'}
            self._assert_acceptable_keys(
                'description', set(desc.keys()), acceptable_keys, path,
                ErrorLevel.WARNING)

            self._assert_type(
                'identifier', desc['identifier'], (str,),
                geometry_path + ['identifier'])
            result['identifier'] = desc['identifier']
            for what in ('texture_width', 'texture_height'):
                if what in desc:
                    obj, obj_path = desc[what], geometry_path + [what]
                    success = self._assert_type(
                        what, obj, (int, float), obj_path, ErrorLevel.WARNING,
                        more="Replaced with default value: 64.")
                    success = success and self._assert_type(
                        what, obj, (int,), obj_path, ErrorLevel.WARNING,
                        more="Rounded down to nearest integer.")
                    if success:
                        result[what] = int(desc[what])
            if 'visible_bounds_offset' in desc:
                what = 'visible_bounds_offset'
                obj, obj_path = desc[what], geometry_path + [what]
                success = self._assert_vector_type(
                    what, obj, 3, (int, float), obj_path, ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0].")
                if success:
                    result[what] = desc[what]
            for what in ('visible_bounds_width', 'visible_bounds_height'):
                if what in desc:
                    obj, obj_path = desc[what], geometry_path + [what]
                    success = self._assert_type(
                        what, obj, (int, float), obj_path, ErrorLevel.WARNING,
                        more="Replaced with default value: 1.")
                    if success:
                        result[what] = desc[what]
            return result
        if self.parser_version == '1.8.0':
            desc = geometry
            path = geometry_path

            acceptable_keys = {
                "debug", "visible_bounds_width",
                "visible_bounds_height", "visible_bounds_offset",
                "texturewidth", "textureheight", "cape", "bones"}
            self._assert_acceptable_keys(
                'geometry', set(desc.keys()), acceptable_keys, path,
                ErrorLevel.WARNING)

            self._assert_type(
                'identifier', path[-1], (str,),
                geometry_path + ['identifier'])
            result['identifier'] = path[-1]
            if 'debug' in desc:
                self.append_warning(
                    "Debug property is not supported. Ignored.",
                    geometry_path + ["debug"])
            for what, what_new in (
                    ('texturewidth', 'texture_width'),
                    ('textureheight', 'texture_height')):
                if what in desc:
                    success = self._assert_type(
                        what, desc[what], (int, float),
                        geometry_path + [what], ErrorLevel.WARNING,
                        more="Replaced with default value: 64.")
                    success = success and self._assert_type(
                        what, desc[what], (int,),
                        geometry_path + [what], ErrorLevel.WARNING,
                        more="Rounded down to nearest integer.")
                    if success:
                        # The result uses different name than the models
                        # in format version 1.8.0 (e.g texture_width vs
                        # texturewidth)
                        result[what_new] = int(desc[what])
            if 'visible_bounds_offset' in desc:
                self._assert_vector_type(
                    'visible_bounds_offset', desc['visible_bounds_offset'], 3,
                    (int, float), geometry_path + ['visible_bounds_offset'])
                result['visible_bounds_offset'] = desc['visible_bounds_offset']
            for what in ('visible_bounds_width', 'visible_bounds_height'):
                if 'visible_bounds_width' in desc:
                    what = 'visible_bounds_width'
                    obj, obj_path = desc[what], geometry_path + [what]
                    success = self._assert_type(
                        what, obj, (int, float), obj_path, ErrorLevel.WARNING,
                        more="Replaced with default value: 1.")
                    if success:
                        result[what] = desc[what]
            return result
        raise ImporterException('Unsupported format version')

    def _load_bones(
            self, bones: Any, bones_path: List[str | int]
    ) -> List[Dict[str, Any]]:
        '''
        Returns the bones from a list of bones, adds missing default values.

        :param bones: List of bones.
        :param bones_path: Path to the bones list (used for error messages).
        '''
        result: List[Dict[str, Any]] = []
        if self.parser_version in ('1.16.0', '1.12.0', '1.8.0'):
            self._assert_type(
                'bones property', bones, (list,), bones_path)  # type: ignore
            for i, bone in enumerate(bones):
                bone_path = bones_path + [i]
                result.append(self._load_bone(bone, bone_path))
            return result
        raise ImporterException('Unsupported format version')

    def _load_bone(
            self, bone: Any, bone_path: List[str | int]) -> Dict[str, Any]:
        '''
        Returns a bone, adds all of the missing default values of the
        properties.

        :param bone: Part of the json file that has the inforation about the
            bone.
        :param bone_path: Path to the bone (used for error messages).
        '''
        result: Dict[str, Any] = {
            "parent": None,  # str
            "pivot" : [0, 0, 0],  # List[float] len=3
            "rotation" : [0, 0, 0],  # List[float] len=3
            "mirror" : False,  # bool
            "inflate": 0.0,  # float
            "debug": False,  # bool
            "cubes" : [],  # List[Dict]
            "locators": {},  # Dict[...]
            "poly_mesh": None,  # Dict
            "texture_meshes": [],  # List[Dict]
            "binding": None, # str
            # "render_group_id": 0,  # int >= 0
        }
        if self.parser_version in ('1.16.0', '1.12.0'):
            self._assert_type('bone', bone, (dict,), bone_path)  # type: ignore


            self._assert_required_keys(
                'bone', set(bone.keys()), {'name'}, bone_path)
            acceptable_keys = {
                'name', 'parent', 'pivot', 'rotation', 'mirror', 'inflate',
                'cubes', 'locators', 'poly_mesh'}
            # 'render_group_id', 'debug', 'texture_meshes'
            if self.parser_version == '1.16.0':
                acceptable_keys.add('binding')

            self._assert_acceptable_keys(
                'bone', set(bone.keys()), acceptable_keys, bone_path,
                ErrorLevel.WARNING)

            if 'name' in bone:
                # This property is a minimal requirement. ErrorLevel: ERROR
                self._assert_type(
                    'name', bone['name'], (str,), bone_path + ['name'])
                result['name'] = bone['name']
            if 'binding' in bone:
                success = self._assert_type(
                    'binding', bone['binding'], (str,),
                    bone_path + ['binding'], ErrorLevel.WARNING,
                    more="Skipped.")
                if success:
                    result['binding'] = bone['binding']
            if 'parent' in bone:
                success = self._assert_type(
                    'parent', bone['parent'], (str,), bone_path + ['parent'],
                    ErrorLevel.WARNING, more="Skipped.")
                if success:
                    if 'name' in bone and bone['name'] == bone['parent']:
                        self.append_warning(
                            f"Bone {bone['name']} is parent is itself."
                                " Skipped.",
                            bone_path + ['parent'])
                    else:
                        result['parent'] = bone['parent']
            if 'pivot' in bone:
                success = self._assert_vector_type(
                    'pivot', bone['pivot'], 3, (int, float),
                    bone_path + ['pivot'], ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0].")
                if success:
                    result['pivot'] = bone['pivot']
            if 'rotation' in bone:
                success = self._assert_vector_type(
                    'rotation', bone['rotation'], 3, (int, float),
                    bone_path + ['rotation'], ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0].")
                if success:
                    result['rotation'] = bone['rotation']
            if 'mirror' in bone:
                success = self._assert_type(
                    'mirror', bone['mirror'], (bool,), bone_path + ['mirror'],
                    ErrorLevel.WARNING,
                    more="Replaced with default value: false.")
                if success:
                    result['mirror'] = bone['mirror']
            if 'inflate' in bone:
                success = self._assert_type(
                    'inflate', bone['inflate'], (float, int),
                    bone_path + ['inflate'], ErrorLevel.WARNING,
                    more="Skipped.")
                if success:
                    result['inflate'] = bone['inflate']
            if 'debug' in bone:
                self.append_warning(
                    "Debug property is not supported. Ignored.",
                    bone_path + ["debug"])
            if 'cubes' in bone:
                # default mirror for cube is the bones mirror property
                result['cubes'] = self._load_cubes(
                    bone['cubes'], bone_path + ['cubes'], result['mirror'],
                    result['inflate'])
            if 'locators' in bone:
                result['locators'] = self._load_locators(
                    bone['locators'], bone_path + ['locators'])
            if 'poly_mesh' in bone:
                result['poly_mesh'] = self._load_poly_mesh(
                    bone['poly_mesh'], bone_path + ['poly_mesh'])
            return result
        if self.parser_version == '1.8.0':
            self._assert_type('bone', bone, (dict,), bone_path)  # type: ignore

            self._assert_required_keys(
                'bone', set(bone.keys()), {'name'}, bone_path)
            acceptable_keys = {
                'name', 'parent', 'pivot', 'rotation',
                'mirror', 'inflate', 'cubes', 'locators',
                'poly_mesh'}
            # 'bind_pose_rotation', 'neverRender', 'debug', 'render_group_id',
            # 'reset', 'texture_meshes'
            self._assert_acceptable_keys(
                'bone', set(bone.keys()), acceptable_keys, bone_path,
                ErrorLevel.WARNING)

            if 'name' in bone:
                # This property is a minimal requirement. ErrorLevel: ERROR
                self._assert_type(
                    'name', bone['name'], (str,), bone_path + ['name'])
                result['name'] = bone['name']
            if 'parent' in bone:
                success = self._assert_type(
                    'parent', bone['parent'], (str,), bone_path + ['parent'],
                    ErrorLevel.WARNING, more="Skipped.")
                if success:
                    result['parent'] = bone['parent']
            if 'pivot' in bone:
                success = self._assert_vector_type(
                    'pivot', bone['pivot'], 3, (int, float),
                    bone_path + ['pivot'], ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0].")
                if success:
                    result['pivot'] = bone['pivot']
            if 'rotation' in bone:
                success = self._assert_vector_type(
                    'rotation', bone['rotation'], 3, (int, float),
                    bone_path + ['rotation'], ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0].")
                if success:
                    result['rotation'] = bone['rotation']
            if 'mirror' in bone:
                success = self._assert_type(
                    'mirror', bone['mirror'], (bool,), bone_path + ['mirror'],
                    ErrorLevel.WARNING,
                    more="Replaced with default value: false.")
                if success:
                    result['mirror'] = bone['mirror']
            if 'inflate' in bone:
                success = self._assert_type(
                    'inflate', bone['inflate'], (float, int),
                    bone_path + ['inflate'], ErrorLevel.WARNING,
                    more="Skipped.")
                if success:
                    result['inflate'] = bone['inflate']
            if 'cubes' in bone:
                # default mirror for cube is the bones mirror property
                result['cubes'] = self._load_cubes(
                    bone['cubes'], bone_path + ['cubes'], result['mirror'],
                    result['inflate'])
            if 'locators' in bone:
                result['locators'] = self._load_locators(
                    bone['locators'], bone_path + ['locators'])
            if 'poly_mesh' in bone:
                result['poly_mesh'] = self._load_poly_mesh(
                    bone['poly_mesh'], bone_path + ['poly_mesh'])
            return result
        raise ImporterException('Unsupported format version')

    def _load_cubes(
            self, cubes: Any, cubes_path: List[Any], default_mirror: bool,
            default_inflate: float) -> List[Dict[str, Any]]:
        '''
        Returns the cubes from the list of cubes, add missing default values.

        :param cubes: List of cubes.
        :param cubes_path: Path to the cubes list (used for error messages).
        :param default_mirror: Mirror value of a bone that owns this list
            of cubes.
        '''
        result: List[Dict[str, Any]] = []
        if self.parser_version in ('1.16.0', '1.12.0', '1.8.0'):
            if not self._assert_type(
                    'cubes property', cubes, (list,),  # type: ignore
                    cubes_path, ErrorLevel.WARNING, more="Skipped."):
                return result
            for i, cube in enumerate(cubes):
                cube_path = cubes_path + [i]
                result.append(
                    self._load_cube(
                        cube, cube_path, default_mirror,
                        default_inflate))
            return result
        raise ImporterException('Unsupported format version')

    def _create_default_uv(
            self, size: Vector3d, mirror: bool,
            uv: Vector2d = (0.0, 0.0)) -> Dict[str, Any]:
        '''
        Creates default UV dictionary (in per-face UV mapping format) based on
        some other properties of a cube.

        :param size: The size of the cube.
        :param mirror: The mirror property of the cube.
        :param uv: Optional - the UV property of the cube (if the cube uses the
            standard Minecraft UV mapping format).
        '''
        width, height, depth = (int(i) for i in size)

        def _face(size: Vector2d, uv: Vector2d):
            return {"uv_size": size, "uv": uv}

        face1 = _face((depth, height), (uv[0], uv[1] + depth))
        face2 = _face((width, height), (uv[0]+depth, uv[1] + depth))
        face3 = _face((depth, height), (uv[0]+depth + width, uv[1] + depth))
        face4 = _face((width, height), (uv[0]+2*depth + width, uv[1] + depth))
        face5 = _face((width, depth), (uv[0]+depth, uv[1]))
        face6 = _face((width, -depth), (uv[0]+depth + width, uv[1] + depth))
        if mirror:
            face_west, face_east = face1, face3
        else:
            face_east, face_west = face1, face3
        # No mirror: | # Mirror:
        #   5 6      | #   5 6
        # 1 2 3 4    | # 3 2 1 4
        result: Dict[str, Any] = {
            "north": face2, "south": face4, "east": face_east,
            "west": face_west, "up": face5, "down": face6}
        return result

    def _load_cube(
            self, cube: Any, cube_path: List[str | int], default_mirror: bool,
            default_inflate: float) -> Dict[str, Any]:
        '''
        Returns a cube with added all of the missing default values of the
        properties.

        :param cube: Part of the JSON dict that has the inforation about the
            cube.
        :param cube_path: JSON path to the cube (used for error messages).
        :param default_mirror: Mirror value of a bone that owns this cube.
        '''
        result: Dict[str, Any] = {
            "origin" : (0, 0, 0),  # Listfloat] len=3
            "size" : (0, 0, 0),  # Listfloat] len=3
            "rotation" : (0, 0, 0),  # Listfloat] len=3
            "pivot" : (0, 0, 0),  # Listfloat] len=3
            "inflate" : default_inflate,  # float
            "mirror" : default_mirror,  # mirror

            # Default UV value is based on the size and mirror of the cube
            # before return statement
            "uv": None
        }
        if self.parser_version in ('1.16.0', '1.12.0'):
            self._assert_type('cube', cube, (dict,), cube_path)  # type: ignore
            # There is no required keys {} is a valid cube
            acceptable_keys = {
                "mirror", "inflate", "pivot", "rotation", "origin",
                "size", "uv"}
            self._assert_acceptable_keys(
                'cube', set(cube.keys()), acceptable_keys, cube_path,
                ErrorLevel.WARNING)
            for k in ('origin', 'size', 'rotation', 'pivot'):
                if k in cube:
                    success = self._assert_vector_type(
                        k, cube[k], 3, (int, float),
                        cube_path + [k], ErrorLevel.WARNING,
                        more="Replaced with default value: [0, 0, 0]")
                    if success:
                        result[k] = cube[k]

            if 'inflate' in cube:
                success = self._assert_type(
                    'inflate', cube['inflate'], (int, float),
                    cube_path + ['inflate'], ErrorLevel.WARNING,
                    more="Replaced with default value.")
                if success:
                    result['inflate'] = cube['inflate']
            if 'mirror' in cube:
                success = self._assert_type(
                    'mirror', cube['mirror'], (bool,), cube_path + ['mirror'],
                    ErrorLevel.WARNING, more="Replaced with default value.")
                if success:
                    result['mirror'] = cube['mirror']
            if 'uv' in cube:
                success = self._assert_type(
                    'uv', cube['uv'],
                    (list, dict),  # type: ignore
                    cube_path + ['uv'],
                    ErrorLevel.WARNING, more="Replaced with default value.")
                if success:
                    if isinstance(cube['uv'], dict):
                        result['uv'] = self._load_uv(
                            cube['uv'], cube_path + ['uv'],
                            tuple(result['size'])  # type: ignore
                        )
                    elif isinstance(cube['uv'], list):
                        success = self._assert_vector_type(
                            'uv', cube['uv'], 2, (int, float),
                            cube_path + ['uv'], ErrorLevel.WARNING,
                            more="Replaced with default value.")
                        if success:
                            result['uv'] = self._create_default_uv(
                                tuple(result['size']),  # type: ignore
                                result['mirror'],  # type: ignore
                                tuple(cube['uv']))  # type: ignore
            # Create default UV based on size and mirror
            if result['uv'] is None:
                result['uv'] = self._create_default_uv(
                    tuple(result['size']),  # type: ignore
                    result['mirror'])  # type: ignore
            return result
        if self.parser_version == '1.8.0':
            self._assert_type('cube', cube, (dict,), cube_path)  # type: ignore
            # There is no required keys {} is a valid cube
            acceptable_keys = {"origin", "size", "uv", "inflate", "mirror"}
            self._assert_acceptable_keys(
                'cube', set(cube.keys()), acceptable_keys, cube_path,
                ErrorLevel.WARNING)
            for k in ('origin', 'size'):
                if k in cube:
                    success = self._assert_vector_type(
                        k, cube[k], 3, (int, float),
                        cube_path + [k], ErrorLevel.WARNING,
                        more="Replaced with default value: [0, 0, 0]")
                    if success:
                        result[k] = cube[k]

            if 'inflate' in cube:
                success = self._assert_type(
                    'inflate', cube['inflate'], (int, float),
                    cube_path + ['inflate'], ErrorLevel.WARNING,
                    more="Replaced with default value.")
                if success:
                    result['inflate'] = cube['inflate']
            if 'mirror' in cube:
                success = self._assert_type(
                    'mirror', cube['mirror'], (bool,), cube_path + ['mirror'],
                    ErrorLevel.WARNING, more="Replaced with default value.")
                if success:
                    result['mirror'] = cube['mirror']
            if 'uv' in cube:
                success = self._assert_type(
                    'uv', cube['uv'], (list,),  # type: ignore
                    cube_path + ['uv'],
                    ErrorLevel.WARNING, more="Replaced with default value.")
                success = success and self._assert_vector_type(
                    'uv', cube['uv'], 2, (int, float), cube_path + ['uv'],
                    ErrorLevel.WARNING, more="Replaced with default value.")
                if success:
                    result['uv'] = self._create_default_uv(
                        tuple(result['size']),  # type: ignore
                        result['mirror'],  # type: ignore
                        tuple(cube['uv']))  # type: ignore
            # Create default UV based on size and mirror
            if result['uv'] is None:
                result['uv'] = result['uv'] = self._create_default_uv(
                    tuple(result['size']),  # type: ignore
                    result['mirror'])  # type: ignore
            return result
        raise ImporterException('Unsupported format version')

    def _load_poly_mesh(
            self, poly_mesh: Any,
            poly_mesh_path: List[str | int]) -> Dict[str, Any]:
        '''
        Returns a polymesh with added all of the missing default values of the
        properties.

        :param poly_mesh: Part of the JSON dict that has the inforation about
            the polymesh.
        :param poly_mesh_path: JSON path to the polymesh (used for error
            messages).
        '''
        result: Dict[str, Any] = {
            'normalized_uvs': False,
            'positions': [],
            'normals': [],
            'uvs': [],
            'polys': [],  # 'tri_list' or 'quad_list" or list with data
        }
        if self.parser_version in ('1.16.0', '1.12.0', '1.8.0'):
            success = self._assert_type(
                'poly_mesh', poly_mesh,
                (dict,),  # type: ignore
                poly_mesh_path,
                ErrorLevel.WARNING, more="Replaced with default value.")
            if not success:
                return result
            # There is no required keys {} is a valid poly_mesh
            success = self._assert_required_keys(
                'poly_mesh', set(poly_mesh.keys()), {'polys'}, poly_mesh_path,
                ErrorLevel.WARNING, more="Replaced with default value.")
            if not success:
                return result
            acceptable_keys = {
                "normalized_uvs", "positions", "normals", "uvs", "polys"}
            self._assert_acceptable_keys(
                'poly_mesh', set(poly_mesh.keys()), acceptable_keys,
                poly_mesh_path, ErrorLevel.WARNING)
            # Acceptable keys
            if 'normalized_uvs' in poly_mesh:
                success = self._assert_type(
                    'normalized_uvs', poly_mesh['normalized_uvs'], (bool,),
                    poly_mesh_path + ['normalized_uvs'], ErrorLevel.WARNING,
                    more="Replaced with default value: false")
                if success:
                    result['normalized_uvs'] = poly_mesh['normalized_uvs']
            if 'positions' in poly_mesh:
                positions = poly_mesh['positions']
                positions_path = poly_mesh_path + ['position']
                success = self._assert_type(
                    'positions', positions,
                    (list,),  # type: ignore
                    positions_path,
                    ErrorLevel.WARNING, more="Ignored.")
                if success:
                    for position_id, position in enumerate(positions):
                        success = self._assert_vector_type(
                            'position', position, 3, (float, int,),
                            positions_path + [position_id], ErrorLevel.WARNING,
                            more="Ignored entire polymesh positions list.")
                        if not success:
                            result['positions'] = []
                            break
                        result['positions'].append(tuple(position))  # type: ignore
            if 'normals' in poly_mesh:
                normals = poly_mesh['normals']
                normals_path = poly_mesh_path + ['normal']
                success = self._assert_type(
                    'normals', normals, (list,),  # type: ignore
                    normals_path,
                    ErrorLevel.WARNING, more="Ignored.")
                if success:
                    for normal_id, normal in enumerate(normals):
                        success = self._assert_vector_type(
                            'normal', normal, 3, (float, int,),
                            normals_path + [normal_id], ErrorLevel.WARNING,
                            more="Ignored entire polymesh normals list.")
                        if not success:
                            result['normals'] = []
                            break
                        result['normals'].append(tuple(normal))  # type: ignore
            if 'uvs' in poly_mesh:
                uvs = poly_mesh['uvs']
                uvs_path = poly_mesh_path + ['uv']
                success = self._assert_type(
                    'uvs', uvs, (list,),  # type: ignore
                    uvs_path, ErrorLevel.WARNING,
                    more="Ignored.")
                if success:
                    for uv_id, uv in enumerate(uvs):
                        self._assert_vector_type(
                            'uv', uv, 2, (float, int,),
                            uvs_path + [uv_id], ErrorLevel.WARNING,
                            more="Ignored entire polymesh uvs list.")
                        if not success:
                            result['uvs'] = []
                            break
                        result['uvs'].append(tuple(uv))  # type: ignore
            # Required keys
            self._assert_type(
                'polys', poly_mesh['polys'], (str, list),  # type: ignore
                poly_mesh_path + ['polys'])
            if isinstance(poly_mesh['polys'], str):
                result['polys'] = self._create_default_polys(
                    poly_mesh['polys'],
                    result['positions'],  # type: ignore
                    result['normals'],  # type: ignore
                    result['uvs'],  # type: ignore
                    poly_mesh_path)
            elif isinstance(poly_mesh['polys'], list):
                polys_path = poly_mesh_path + ['polys']
                for poly_id, poly in enumerate(poly_mesh['polys']):
                    curr_result_poly: List[Vector3di] = []
                    poly_path = polys_path + [poly_id]
                    success = self._assert_type(
                        'poly', poly, (list,),  # type: ignore
                        poly_path, ErrorLevel.WARNING,
                        more="Ignored polygon.")
                    if not success:
                        continue
                    result['polys'].append(curr_result_poly)  # type: ignore
                    for poly_vertex_id, poly_vertex in enumerate(poly):
                        success = self._assert_vector_type(
                            'vertex', poly_vertex, 3, (int,),
                            poly_path + [poly_vertex_id], ErrorLevel.WARNING,
                            more="Replaced with default value: [0, 0, 0]")
                        if success:
                            curr_result_poly.append(
                                tuple(poly_vertex))  # type: ignore
                        else:
                            curr_result_poly.append((0, 0, 0))
            return result
        raise ImporterException('Unsupported format version')

    def _create_default_polys(
            self, grouping_mode: str, positions: List[List[float]],
            normals: List[List[float]], uvs: List[List[float]],
            poly_mesh_path: List[str | int]
            ) -> List[List[List[int]]]:
        '''
        Creates default "polys" property of a polymesh for "tri_list" or
        "quad_list" mode. Checks if positions, normals and uv are the same
        length and can be divided by 3 (for tri_list mode) or 4 (for quad_list
        mode). Rises an exception if the creating default polys list is
        impossible with input data.

        :param grouping_mode: a string with grouping mode. It should be either
            'tri_list' or 'quad_list' otherwise an exception is risen.
        :param positions: list of positions of the vertices.
        :param normals: list of normals of the loops.
        :param uvs: list of the uv coordinates of the loops.
        :parma poly_mesh_path: the JSON path to the poly_mesh that contains
            this polys property.
        '''
        # Get polygon group size (three or four items)
        if grouping_mode == 'tri_list':
            group_size = 3
        elif grouping_mode == 'quad_list':
            group_size = 4
        else:
            raise ImporterException(
                f'{poly_mesh_path + ["polys"]}::{"polys"} is not an a list of '
                'polys or a literal string "quad_list" or "tri_list"')
        # Check if positions, normals and uvs are the same lengths
        pos_length = len(positions)
        if not pos_length == len(normals) == len(uvs):
            raise ImporterException(
                f'{poly_mesh_path}::"positions", "normals" and "uvs" are not '
                'the same lengths. They must be the same lengths in "tri_list"'
                ' and "quad_list" polys grouping mode.')
        # Check if list length is divisible by the group_size
        if not pos_length % group_size == 0:
            raise ImporterException(
                f'{poly_mesh_path}::"positions" list length must be '
                f'divisible by {group_size} when you use grouping mode: '
                f'{grouping_mode}.')
        # Build default polys property in list format
        result = np.repeat(
            range(pos_length), 3
        ).reshape(
            -1, group_size, 3
        ).tolist()
        return result

    def _load_uv(
            self, uv: Any, uv_path: List[str | int],
            cube_size: Vector3d) -> Dict[str, Any]:
        '''
        Returns UV and adds all of the missing default values of its
        properties.

        :param uv: Part of the JSON dict that has the inforation about the uv.
        :param uv_path: Path to the UV (used for error messages).
        :param cube_size: Size of the cube which is being mapped (used for
            getting default UV values).
        '''
        width, height, depth = cube_size
        def _face(size: Vector2d, uv: Vector2d):
            return {"uv_size": size, "uv": uv}
        result = {
            # Faces outside of the texture are invisible and should be skipped
            # on export
            "north": _face((0, 0), (0, -1)),
            "south": _face((0, 0), (0, -1)),
            "east": _face((0, 0), (0, -1)),
            "west": _face((0, 0), (0, -1)),
            "up": _face((0, 0), (0, -1)),
            "down": _face((0, 0), (0, -1))
        }

        if self.parser_version in ('1.16.0', '1.12.0'):
            success = self._assert_type(
                'uv', uv, (dict,),  # type: ignore
                uv_path, ErrorLevel.WARNING,
                more="Replaced with default value.")
            if not success:
                return result
            # There is no required keys {} is a valid UV
            acceptable_keys = {"north", "south", "east", "west", "up", "down"}
            self._assert_acceptable_keys(
                'uv', set(uv.keys()), acceptable_keys, uv_path,
                ErrorLevel.WARNING)
            sides = (
                ("north", (depth, height)),
                ("south", (width, height)),
                ("east", (depth, height)),
                ("west", (width, height)),
                ("up", (width, depth)),
                ("down", (width, depth)),
            )
            for k, dimensions in sides:
                if k in uv:
                    result[k] = self._load_uv_face(
                        uv[k], uv_path + [k], dimensions)
            return result
        raise ImporterException('Unsupported format version')

    def _load_uv_face(
            self, uv_face: Any, uv_face_path: List[str | int],
            default_size: Vector2d) -> Dict[str, Any]:
        '''
        Returns UV and adds all of the missing default values of its
        properties.

        :param uv_face: Part of the JSON dict that has the inforation about the
          uv face.
        :param uv_face_path: Path to the uv face (used for error messages).
        :param default_size: Default size of the UV face.
        '''
        result = {
            "uv_size": default_size, "uv": [0, 0]
        }
        if self.parser_version in ('1.16.0', '1.12.0'):
            success = self._assert_type(
                'uv_face', uv_face, (dict,),  # type: ignore
                uv_face_path, ErrorLevel.WARNING,
                more="Replaced with default value.")
            if not success:
                return result
            self._assert_required_keys(
                'uv', set(uv_face.keys()), {'uv'}, uv_face_path,
                ErrorLevel.WARNING,
                more="Replaced with default value [0, 0]")
            self._assert_acceptable_keys(
                'uv_face', set(uv_face.keys()),
                {"uv", "uv_size"}, uv_face_path,
                ErrorLevel.WARNING)
            # "material_instance"

            success = self._assert_vector_type(
                'uv', uv_face['uv'], 2, (int, float),
                uv_face_path + ['uv'], error_level=ErrorLevel.WARNING,
                more="Replaced with default value [0, 0]")
            if success:
                result["uv"] = uv_face["uv"]
            if "uv_size" in uv_face:
                success = self._assert_vector_type(
                    'uv_size', uv_face['uv_size'], 2, (int, float),
                    uv_face_path + ['uv_size'], ErrorLevel.WARNING,
                    more=f"Replaced with default value {default_size}")
                if success:
                    result["uv_size"] = uv_face["uv_size"]
            return result
        raise ImporterException('Unsupported format version')

    def _load_locators(
            self, locators: Any,
            locators_path: List[str | int]) -> Dict[str, Any]:
        '''
        Returns the locators from the list of locators with added missing
        default values.

        :param locators: List of the locators.
        :param locators_path: Path to the locators list (used for error
            messages)
        '''
        result: Dict[str, Any] = {}
        if self.parser_version in ['1.16.0', '1.12.0', '1.8.0']:
            success = self._assert_type(
                'locators property', locators, (dict,),  # type: ignore
                locators_path, ErrorLevel.WARNING, more="Ignored.")
            if not success:
                return result
            for i, locator in locators.items():
                locator_path = locators_path + [i]
                result[i] = self._load_locator(locator, locator_path)
            return result
        raise ImporterException('Unsupported format version')

    def _load_locator(
            self, locator: Any, locator_path: List[str | int]) -> Any:
        '''
        Returns the locator with added missing default values.

        :param locator: The locator
        :param locator_path: Path to the locator
        '''
        if self.parser_version in ['1.16.0', '1.12.0']:
            result: Dict[str, Any] = {"offset": [0, 0, 0], "rotation": [0, 0, 0]}
            if isinstance(locator, list):
                success = self._assert_vector_type(
                    'locator', locator, 3, (int, float), locator_path,
                    ErrorLevel.WARNING,
                    more="Replaced with default value: [0, 0, 0]")
                if not success:
                    return result
                return {"offset": locator, "rotation": [0, 0, 0]}  # type: ignore

            if isinstance(locator, dict):
                self._assert_acceptable_keys(
                    'locator',
                    set(locator.keys()),  # type: ignore
                    {'offset', 'rotation'},
                    locator_path, ErrorLevel.WARNING)
                if "offset" in locator:
                    success = self._assert_vector_type(
                        'offset', locator['offset'], 3, (int, float),
                        locator_path + ['offset'], ErrorLevel.WARNING,
                        more="Replaced with default value: [0, 0, 0]")
                    if success:
                        result["offset"] = locator["offset"]
                if "rotation" in locator:
                    success = self._assert_vector_type(
                        'rotation', locator['rotation'], 3, (int, float),
                        locator_path + ['rotation'], ErrorLevel.WARNING,
                        more="Replaced with default value: [0, 0, 0]")
                    if success:
                        result["rotation"] = locator["rotation"]
                return result
            self.append_warning(
                'locator is not a list or dict. Replaced with default value.',
                locator_path)
            return result
        if self.parser_version == '1.8.0':
            success = self._assert_vector_type(
                'locator', locator, 3, (int, float), locator_path,
                ErrorLevel.WARNING,
                more="Replaced with default value: [0, 0, 0]")
            if not success:
                return {"offset": [0, 0, 0], "rotation": [0, 0, 0]}
            return {"offset": locator, "rotation": [0, 0, 0]}
        raise ImporterException('Unsupported format version')


class ImportLocator:
    '''
    Represents Minecraft locator during import operation.

    :param name: Name of the locator.
    :param position: The position of the locator.
    '''
    name: str
    position: Vector3d
    rotation: Vector3d
    blend_empty: Optional[Object]

    def __init__(self, name: str, position: Vector3d, rotation: Vector3d):
        self.name = name
        self.position = position
        self.rotation = rotation
        self.blend_empty = None


class ImportCube:
    '''
    Represents minecraft cube during import operation.

    :param data: The part of the Minecraft model JSON dict that represents this
        cube.
    '''
    blend_cube: Optional[Object]
    uv: Dict[str, Any]
    mirror: bool
    inflate: bool
    origin: Vector3d
    pivot: Vector3d
    size: Vector3d
    rotation: Vector3d

    def __init__(self, data: Dict[str, Any]):
        '''
        Creates ImportCube object created from a dictionary (part of the JSON)
        file in the model.

        # Arguments:
        - `data: Dict` - the part of the Minecraft model JSON file that
        represents the cube.
        '''
        self.blend_cube = None

        self.uv = data['uv']
        self.mirror = data['mirror']
        self.inflate = data['inflate']
        self.origin = tuple(  # type: ignore
            data['origin'])
        self.pivot = tuple(  # type: ignore
            data['pivot'])
        self.size = tuple(  # type: ignore
            data['size'])
        self.rotation = tuple(  # type: ignore
            data['rotation'])


class ImportPolyMesh:
    '''
    Represents Minecraft poly_mesh during import operation.

    :param data: The part of the Minecraft model JSON dict that represents this
        poly_mesh.
    '''
    blend_object: Optional[Object]
    normalized_uvs: bool
    positions: List[Vector3d]
    normals: List[Vector3d]
    uvs: List[Vector2d]
    polys: List[List[Vector3di]]

    def __init__(
            self, data: Dict[str, Any]):
        '''
        Creates ImportPolyMesh object created from a dictionary (part of the
        JSON) file in the model.

        :param data: The part of the Minecraft model JSON file that represents
        the poly_mesh.
        '''
        self.blend_object = None
        self.normalized_uvs = data['normalized_uvs']
        self.positions = data['positions']
        self.normals = data['normals']
        self.uvs = data['uvs']
        self.polys = data['polys']


class ImportBone:
    '''
    Represents Minecraft bone during import operation.

    :param data: The part of the Minecraft model JSON dict that represents the
        bone.
    '''
    blend_empty: Object | None
    name: str
    parent: str
    binding: str
    cubes: list[ImportCube]
    poly_mesh: ImportPolyMesh | None
    locators: list[ImportLocator]
    pivot: Vector3d
    rotation: Vector3d
    mirror: bool

    def __init__(self, data: Dict[str, Any]):
        self.blend_empty: Optional[Object] = None

        # Locators
        locators: List[ImportLocator] = []
        for k, v in data['locators'].items():
            locators.append(
                ImportLocator(k, v['offset'], v['rotation']))  # type: ignore
        # Cubes
        import_cubes: List[ImportCube] = []
        for cube in data['cubes']:
            import_cubes.append(ImportCube(cube))

        self.name = data['name']
        self.parent = data['parent']
        self.binding = data['binding']
        self.cubes = import_cubes
        self.poly_mesh = None
        if data['poly_mesh'] is not None:
            self.poly_mesh = ImportPolyMesh(data['poly_mesh'])
        self.locators = locators
        self.pivot = tuple(  # type: ignore
            data['pivot'])
        self.rotation = tuple(  # type: ignore
            data['rotation'])
        self.mirror = data['mirror']


class ImportGeometry:
    '''
    Represents whole Minecraft geometry during import operation.

    :param loader: Loader object with all of the required model properties.
    '''
    identifier: str
    texture_width: int
    texture_height: int
    visible_bounds_offset: Vector3d
    visible_bounds_width: float
    visible_bounds_height: float
    bones: dict[str, ImportBone]
    uv_converter: CoordinatesConverter

    def __init__(self, loader: ModelLoader):
        # Set the values
        self.identifier = loader.description['identifier']
        self.texture_width = int(loader.description['texture_width'])
        self.texture_height = int(loader.description['texture_height'])
        self.visible_bounds_offset = loader.description[
            'visible_bounds_offset']
        self.visible_bounds_width = loader.description['visible_bounds_width']
        self.visible_bounds_height = loader.description[
            'visible_bounds_height']
        self.bones = {}
        self.uv_converter = CoordinatesConverter(
            np.array([[0, self.texture_width], [0, self.texture_height]]),
            np.array([[0, 1], [1, 0]])
        )

        # Read bones
        for bone in loader.bones:
            import_bone = ImportBone(bone)
            self.bones[import_bone.name] = import_bone

    def build_with_empties(
            self, context: bpy.types.Context) -> Object:
        '''
        Builds the geometry in Blender. Uses empties to represent Minecraft
        bones.

        :param context: The context of running the operator.
        :returns: the armature which represents imported model. Root parent
            of created objects
        '''

        # Build armature:
        # Create empty armature and enter edit mode:
        bpy.ops.object.armature_add(  # pyright: ignore[reportUnknownMemberType]
            enter_editmode=True, align='WORLD', location=[0, 0, 0])
        bpy.ops.armature.select_all(  # pyright: ignore[reportUnknownMemberType]
            action='SELECT')
        bpy.ops.armature.delete()  # pyright: ignore[reportUnknownMemberType]
        bpy.ops.object.mode_set(  # pyright: ignore[reportUnknownMemberType]
            mode='OBJECT')
        # TODO - build the armature without using bpy.ops for better
        # performance

        # Save the armature
        armature: Object = cast(Object, context.object)

        # Create objects - and set their pivots
        for bone in self.bones.values():
            # 1. Spawn bone (empty)
            bpy.ops.object.empty_add(  # pyright: ignore[reportUnknownMemberType]
                type='SPHERE', location=[0, 0, 0], radius=0.2)

            # Must be an 'Object' because it has just been created:
            bone_obj: Object = cast(Object, context.object)
            bone.blend_empty = bone_obj

            _mc_pivot(bone_obj, bone.pivot)  # 2. Apply translation
            bone_obj.name = bone.name  # 3. Apply custom properties
            for cube in bone.cubes:
                # 1. Spawn cube
                bpy.ops.mesh.primitive_cube_add(  # pyright: ignore[reportUnknownMemberType]
                    size=1, enter_editmode=False, location=[0, 0, 0]
                )
                # Must be an 'Object' because it has just been created:
                cube_obj: Object = cast(Object, context.object)
                cube.blend_cube  = cube_obj

                # 2. Set uv
                # warning! Moving this code below cube transformation would
                # break it because bound_box is not getting updated properly
                # before the end of running of the opperator.
                get_mcblend(cube_obj).mirror = cube.mirror

                # This should never happen, primitive_cube_add should always
                # add UV layer to the object
                if cube_obj.data.uv_layers.active is None:
                    raise ImporterException('No UV layer found in the cube!')
                _set_uv(
                    self.uv_converter,
                    CubePolygons.build(cube_obj, cube.mirror),
                    cube.uv, cube_obj.data.uv_layers.active)

                # 3. Set size & inflate
                get_mcblend(cube.blend_cube).inflate = (
                    cube.inflate)
                _mc_set_size(cube_obj, cube.size, inflate=cube.inflate)
                _mc_pivot(cube_obj, cube.pivot)  # 4. Move pivot
                # 5. Apply translation
                _mc_translate(cube_obj, cube.origin, cube.size, cube.pivot)

            if bone.poly_mesh is not None:
                # 1. Unpack the data to format suitable for creating Blender
                # mesh
                blender_polygons: List[List[int]] = []
                blender_normals: List[mathutils.Vector] = []
                blender_uvs: List[Vector2d] = []
                blender_vertices: List[Vector3d] = []

                for vertex in bone.poly_mesh.positions:
                    blender_vertices.append((
                            vertex[0] / MINECRAFT_SCALE_FACTOR,
                            vertex[2] / MINECRAFT_SCALE_FACTOR,
                            vertex[1] / MINECRAFT_SCALE_FACTOR))
                for poly in bone.poly_mesh.polys:
                    curr_polygon: List[int] = []
                    for vertex_id, normal_id, uv_id in poly:
                        if vertex_id in curr_polygon:
                            # vertex can appear only once per polygon. The
                            # exporter sometimes adds vertex twice to exported
                            # meshes because Minecraft can't handle triangles
                            # properly. A polygon that uses same vertex twice
                            # won't work in Blender.
                            continue
                        curr_polygon.append(vertex_id)
                        curr_normal = bone.poly_mesh.normals[normal_id]
                        blender_normals.append(
                            mathutils.Vector((
                                curr_normal[0],
                                curr_normal[2],
                                curr_normal[1])
                            ).normalized()
                        )
                        blender_uvs.append(bone.poly_mesh.uvs[uv_id])
                    blender_polygons.append(curr_polygon)

                # 2. Create mesh
                mesh = bpy.data.meshes.new(name='poly_mesh')
                mesh.from_pydata(  # pyright: ignore[reportUnknownMemberType]
                    blender_vertices, [], blender_polygons)

                if not mesh.validate():  # Valid geometry
                    # 3. Create an object and connect mesh to it, mark as
                    # polymesh
                    poly_mesh_obj = bpy.data.objects.new('poly_mesh', mesh)
                    context.collection.objects.link(poly_mesh_obj)
                    bone.poly_mesh.blend_object = poly_mesh_obj
                    get_mcblend(poly_mesh_obj).mesh_type = (
                        MeshType.POLY_MESH.value)

                    # 4. Set mesh normals and UVs
                    # TODO -verify this code:
                    # Removed for Blender 4.1. May cause issues.
                    # https://developer.blender.org/docs/release_notes/4.1/python_api/#breaking-changes
                    # mesh.create_normals_split()
                    # mesh.use_auto_smooth = True
                    mesh.normals_split_custom_set(
                        blender_normals)  # type: ignore

                    if mesh.uv_layers.active is None:
                        uv_layer = mesh.uv_layers.new().data
                    else:
                        uv_layer = mesh.uv_layers.active.data
                    for i, uv in enumerate(blender_uvs):
                        uv_layer[i].uv = cast(list[float],uv)
                else:
                    del mesh
                    raise ImporterException(
                        'Invalid poly_mesh geometry!')

            for locator in bone.locators:
                # 1. Spawn locator (empty)
                bpy.ops.object.empty_add(  # pyright: ignore[reportUnknownMemberType]
                    type='SPHERE', location=[0, 0, 0], radius=0.1)
                locator_obj: Object = cast(Object, context.object)
                locator.blend_empty = locator_obj 
                # 2. Apply translation
                _mc_pivot(locator_obj, locator.position)
                _mc_rotate(locator_obj, locator.rotation)
                # 3. Apply custom properties
                locator_obj.name = locator.name

        # Parent objects (keep offset)
        for bone in self.bones.values():
            assert bone.blend_empty is not None
            bone_obj = bone.blend_empty
            # 1. Parent bone keep transform
            if (
                    bone.parent is not None and
                    bone.parent in self.bones):
                parent_obj = cast(Object, self.bones[
                    bone.parent
                ].blend_empty)
                context.view_layer.update()
                bone_obj.parent = parent_obj
                bone_obj.matrix_parent_inverse = (
                    parent_obj.matrix_world.inverted())
            # 2. Parent cubes keep transform
            for cube in bone.cubes:
                cube_obj = cast(Object, cube.blend_cube)
                context.view_layer.update()
                cube_obj.parent = bone_obj
                cube_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted())
            # 3. Parent poly_mesh keep transform
            if bone.poly_mesh is not None:
                poly_mesh_obj = cast(Object, bone.poly_mesh.blend_object)
                context.view_layer.update()
                poly_mesh_obj.parent = bone_obj
                poly_mesh_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted())

            # 4. Parent locators keep transform
            for locator in bone.locators:
                locator_obj = cast(Object, locator.blend_empty)
                context.view_layer.update()
                locator_obj.parent = bone_obj
                locator_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted())

        # Rotate objects
        for bone in self.bones.values():
            bone_obj = cast(Object, bone.blend_empty)
            context.view_layer.update()
            _mc_rotate(bone_obj, bone.rotation)
            for cube in bone.cubes:
                cube_obj = cast(Object, cube.blend_cube)
                _mc_rotate(cube_obj, cube.rotation)
        return armature

    def build_with_armature(self, context: bpy.types.Context):
        '''
        Builds the geometry in Blender. Uses armature and bones to represent
        the Minecraft bones.

        :param context: The context of running the operator.
        :returns: the armature which represents imported model. Root parent
            of created objects
        '''
        # Build everything using empties
        armature = self.build_with_empties(context)
        # This assert should never raise an Exception
        assert isinstance(armature.data, Armature), "Object is not Armature"
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(  # pyright: ignore[reportUnknownMemberType]
            mode='EDIT')
        edit_bones = armature.data.edit_bones
        
        # Create bones
        for bone in self.bones.values():
            add_bone(edit_bones, 0.3, bone)

        # Parent bones
        for bone in self.bones.values():
            # 1. Parent bone keep transform
            if (
                    bone.parent is not None and
                    bone.parent in self.bones):
                parent_obj = self.bones[bone.parent]
                # context.view_layer.update()
                edit_bones[bone.name].parent = edit_bones[parent_obj.name]
        bpy.ops.object.mode_set(mode='OBJECT')  # pyright: ignore[reportUnknownMemberType]

        # Add bindings to pose bones
        pose_bones = armature.pose.bones
        for bone in self.bones.values():
            if bone.binding is not None:  # pyright: ignore[reportUnnecessaryComparison]
                get_mcblend(pose_bones[bone.name]).binding = bone.binding

        def parent_bone_keep_transform(
                obj: Object, bone: ImportBone):
            '''
            Used for replacing empty parent with new bone parent
            '''
            context.view_layer.update()

            # Copy matrix_parent_inverse from previous parent
            # It can be copied because old parent (locator) has the same
            # transformation as the new one (bone)
            parent_inverse = obj.matrix_parent_inverse.copy()

            obj.parent = armature
            obj.parent_bone = bone.name  # type: ignore
            obj.parent_type = 'BONE'  # type: ignore

            obj.matrix_parent_inverse = parent_inverse

            # Correct parenting to tail of the bone instead of head
            context.view_layer.update()
            blend_bone = armature.pose.bones[bone.name]
            # pylint: disable=no-member
            correction = mathutils.Matrix.Translation(
                blend_bone.head - blend_bone.tail)
            obj.matrix_world = correction @ obj.matrix_world

        # Replace empties with bones
        for bone in self.bones.values():
            bone_obj = bone.blend_empty

            # 2. Parent cubes keep transform
            for cube in bone.cubes:
                assert cube.blend_cube is not None
                parent_bone_keep_transform(cube.blend_cube, bone)

            # 3. Parent poly_mesh keep transform
            if bone.poly_mesh is not None:
                assert bone.poly_mesh.blend_object is not None
                parent_bone_keep_transform(bone.poly_mesh.blend_object, bone)

            # 4. Parent locators keep transform
            for locator in bone.locators:
                assert locator.blend_empty is not None
                parent_bone_keep_transform(locator.blend_empty, bone)

            # remove the locators
            assert bone_obj is not None
            bpy.data.objects.remove(bone_obj)

        return armature

def _mc_translate(
        obj: Object, mctranslation: Vector3d,
        mcsize: Vector3d,
        mcpivot: Vector3d
    ):
    '''
    Translates a Blender object using a translation vector written in Minecraft
    coordinates system.

    :param obj: Blender object to transform..
    :param mctranslation: Minecraft translation.
    :param mcsize: Minecraft size.
    :param mcpivot: Minecraft pivot.
    '''
    # This assert should never raise an Exception
    assert isinstance(obj.data, Mesh), "The object is not a Mesh"
    pivot_offset = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    size_offset = mathutils.Vector(
        (np.array(mcsize)[[0, 2, 1]] / 2) / MINECRAFT_SCALE_FACTOR
    )
    translation = mathutils.Vector(
        np.array(mctranslation)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    for vertex in obj.data.vertices:
        vertex.co += (translation - pivot_offset + size_offset)  # type: ignore

def _mc_set_size(
        obj: Object, mcsize: Vector3d,
        inflate: Optional[float]=None):
    '''
    Scales a Blender object using scale vector written in Minecraft coordinates
    system.

    :param obj: Blender object
    :param mcsize: Minecraft object size.
    '''
    # This assert should never raise an Exception
    assert isinstance(obj.data, Mesh), "The object is not a Mesh"
    # cube_obj.dimensions = (
    #     np.array(cube_obj.dimensions) +
    #     (2*-cube.inflate/MINECRAFT_SCALE_FACTOR)
    # )
    effective_inflate: float = 0.0
    if inflate is not None:
        effective_inflate = inflate/MINECRAFT_SCALE_FACTOR

    pos_delta = (
        (np.array(mcsize)[[0, 2, 1]] / 2) / MINECRAFT_SCALE_FACTOR
    )
    pos_delta += effective_inflate
    vertices = obj.data.vertices
    # 0. ---; 1. --+; 2. -+-; 3. -++; 4. +--; 5. +-+; 6. ++- 7. +++
    vertices[0].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([-1, -1, -1])))
    vertices[1].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([-1, -1, 1])))
    vertices[2].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([-1, 1, -1])))
    vertices[3].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([-1, 1, 1])))
    vertices[4].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([1, -1, -1])))
    vertices[5].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([1, -1, 1])))
    vertices[6].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([1, 1, -1])))
    vertices[7].co = cast(
        list[float], mathutils.Vector(pos_delta * np.array([1, 1, 1])))

def _mc_pivot(obj: Object, mcpivot: Vector3d) -> None:
    '''
    Moves a pivot of an Blender object using pivot value in Minecraft
    coordinates system.

    :param obj: Blender object
    :param mcpivot: Minecraft object pivot point.
    '''
    translation = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    obj.location += translation  # type: ignore

def _mc_rotate(
        obj: Object, mcrotation: Vector3d
    ) -> None:
    '''
    Rotates a Blender object using rotation written in Minecraft coordinates
    system.

    :param obj: Blender object
    :param mcrotation: Minecraft object rotation.
    '''

    rotation = mathutils.Euler(  # pylint: disable=too-many-function-args
        (np.array(mcrotation)[[0, 2, 1]] * np.array([1, 1, -1])) * math.pi/180,
        'XZY'
    )
    obj.rotation_euler.rotate(rotation)

def _set_uv(
        uv_converter: CoordinatesConverter, cube_polygons: CubePolygons,
        uv: Dict[str, Any], uv_layer: MeshUVLoopLayer):
    '''
    Sets the UV of a face of a Blender cube mesh based on some Minecraft
    properties.

    :param uv_converter: converter used for converting from Minecraft UV
        coordinates (dependent on the scale of the texture) to Blender UV
        coordinates (values from 0 to 1).
    :param cube_polygons: CubePolygons object created from the mesh.
    :param uv: UV mapping for each face.
    :param uv_layer: UV layer of the mesh.
    '''
    uv_data = uv_layer.data
    def set_uv(
            cube_polygon: CubePolygon, size: Vector2d,
            uv: Vector2d):
        cp_loop_indices = cube_polygon.side.loop_indices
        cp_order = cube_polygon.order

        left_down = cp_loop_indices[cp_order[0]]
        right_down = cp_loop_indices[cp_order[1]]
        right_up = cp_loop_indices[cp_order[2]]
        left_up = cp_loop_indices[cp_order[3]]

        uv_data[left_down].uv = cast(
            list[float], uv_converter.convert((uv[0], uv[1] + size[1])))
        uv_data[right_down].uv = cast(
            list[float], uv_converter.convert((uv[0] + size[0], uv[1] + size[1])))
        uv_data[right_up].uv = cast(
            list[float], uv_converter.convert((uv[0] + size[0], uv[1])))
        uv_data[left_up].uv = cast(
            list[float], uv_converter.convert((uv[0], uv[1])))

    # right/left
    set_uv(cube_polygons.east, uv["east"]["uv_size"], uv["east"]["uv"])
    # front
    set_uv(cube_polygons.north, uv["north"]["uv_size"], uv["north"]["uv"])
    # left/right
    set_uv(cube_polygons.west, uv["west"]["uv_size"], uv["west"]["uv"])
    # back
    set_uv(cube_polygons.south, uv["south"]["uv_size"], uv["south"]["uv"])
    # top
    set_uv(cube_polygons.up, uv["up"]["uv_size"], uv["up"]["uv"])
    # bottom
    set_uv(cube_polygons.down, uv["down"]["uv_size"], uv["down"]["uv"])

def add_bone(
        edit_bones: ArmatureEditBones,
        length: float, import_bone: ImportBone):
    '''
    :param edit_bones: edit bones of the armature (from
        armature.data.edit_bones).
    :param length: length of the bone.
    :param import_bone: import bone with all of the Minecraft data
        and the reference to empty object that currently represents the bone.
    '''
    import_bone_blend_empty = import_bone.blend_empty
    if import_bone_blend_empty is None:
        raise ValueError("Failed to add bone.")
    matrix_world = import_bone_blend_empty.matrix_world
    bone = edit_bones.new(import_bone.name)
    bone.head = cast(List[float], (0.0, 0.0, 0.0))
    bone.tail = cast(List[float], (0.0, length, 0.0))
    bone.matrix = matrix_world
