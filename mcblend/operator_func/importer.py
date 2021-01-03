'''
Functions and objects related to importing Minecraft models to Blender.
'''
from __future__ import annotations

import math
from typing import Dict, List, Optional, Any, Tuple, Set

import numpy as np

import bpy_types
import mathutils
import bpy

from .common import (
    MINECRAFT_SCALE_FACTOR, CubePolygons, CubePolygon)
from .uv import CoordinatesConverter
from .exception import FileIsNotAModelException, ImportingNotImplementedError

def _assert(expr: bool, msg: str = ''):
    '''Used in this module to raise exceptions based on condition.'''
    if not expr:
        raise FileIsNotAModelException(msg)

def _assert_is_vector(
        name: str, obj: Any, length: int, types: Tuple, json_path: List
    ) -> None:
    '''
    Asserts that object is an array of specific length with specific type of
    items.
    '''
    _assert(isinstance(obj, list), f'{json_path}::{name} is not a list')
    _assert(
        len(obj) == length,
        f'{json_path}::{name} has invalid length {len(obj)} != {length}')
    _assert(
        all([isinstance(i, types) for i in obj]),
        f'{json_path}::{name} is not instance of List[{types}]')

def _assert_has_required_keys(
        what: str, has_keys: Set, required_keys: Set, json_path: List):
    '''Asserts that object has required keys.'''
    missing_keys = required_keys - has_keys
    if len(missing_keys) != 0:
        raise FileIsNotAModelException(
            f'{json_path}::{what} is missing properties: {missing_keys}')

def _assert_has_accepted_keys_only(
        what: str, has_keys: Set, accepted_keys: Set, json_path: List):
    '''Asserts that object has only keys from accepted set.'''
    additional_keys = has_keys - accepted_keys
    if len(additional_keys) != 0:
        raise FileIsNotAModelException(
            f'{json_path}::{what} has unexpected properties: {additional_keys}')

def _assert_is_type(
        name: str, obj: Any, types: Tuple, json_path: List):
    '''Asserts that object is instance of specific type'''
    if not isinstance(obj, types):
        raise FileIsNotAModelException(
            f'{json_path}::{name} is not an instance of {types}')

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
            raise FileIsNotAModelException(
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
        raise FileIsNotAModelException(
            f'Unsupported format version: {version}')
    return '.'.join([str(i) for i in best_choice])


class ModelLoader:
    '''
    Interface loads model from a JSON dict with Minecraft model.
    Fills missing, optional data with default values.

    :param data: The JSON dict with models file.
    :param geometry_name: Optional - the name of the geometry to load.
    '''
    def __init__(self, data: Dict, geometry_name: str = ""):
        self.data = data
        self.format_version = self._load_format_version(data)
        geometry, geometry_path = self._load_geometry(
            geometry_name, self.data)

        self.description: Dict = self._load_description(
            geometry, geometry_path)
        self.bones: List = self._load_bones(
            geometry['bones'], geometry_path + ['bones'])

    def _load_format_version(self, data: Dict) -> str:
        '''
        Returns the version of the model from JSON file loaded into data.

        :param data: JSON dict with model file.
        '''
        # pylint: disable=no-self-use
        _assert_has_required_keys(
            'model file', set(data.keys()), {'format_version'}, [])
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), data['format_version'])
        if parser_version == '1.12.0':
            _assert_has_required_keys(
                'model file', set(data.keys()),

                {'minecraft:geometry', 'format_version'},
                [])
            _assert_has_accepted_keys_only(
                'model file', set(data.keys()),
                {'minecraft:geometry', 'format_version', 'cape'}, [])
            if 'cape' in data.keys():
                raise ImportingNotImplementedError('cape', [])
            return data['format_version']

        if parser_version == '1.8.0':
            # All geometries must start with geometry.
            for k in data.keys():  # key must be string because its from json
                _assert(
                    (
                        k.startswith('geometry.') or
                        k in ['debug', 'format_version']
                    ),
                    f'{[]}::{k} is invalid geometry name (it should start '
                    'with "geometry."'
                )
            if 'debug' in data.keys():
                raise ImportingNotImplementedError('debug', [])
            return data['format_version']
        raise FileIsNotAModelException('Unsupported format version')

    def _load_geometry(
            self, geometry_name: str, data: Any) -> Tuple[Dict, List]:
        '''
        Finds and returns geometry with specific name from list of geometries
        from JSON dict with models. Returns the geometry dict with
        all of the missing default values added and the JSON path to the
        geometry.

        :param geometry_name: The name of geometry
        :param data: Root object of the JSON.
        '''
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version == '1.12.0':
            geometries = data['minecraft:geometry']
            path: List = ['minecraft:geometry']
            _assert_is_type('geometries', geometries, (list,), path)
            for i, geometry in enumerate(geometries):
                path = ['minecraft:geometry', i]
                _assert_is_type('geometry', geometry, (dict,), path)
                _assert_has_required_keys(
                    'geometry', set(geometry.keys()), {'description', 'bones'},
                    path)
                _assert_has_accepted_keys_only(
                    'geometry', set(geometry.keys()), {'description', 'bones'},
                    path)
                desc = geometry['description']
                if 'identifier' not in desc:
                    raise FileIsNotAModelException(
                        f'{path}::description is missing identifier')
                identifier = desc['identifier']
                if geometry_name in (identifier, ''):
                    return geometry, path
            raise ValueError(f'Unable to find geometry called geometry.{geometry_name}')

        if parser_version == '1.8.0':
            geometries = data
            path = []
            _assert_is_type('geometries', geometries, (dict,), path)
            for k, geometry in geometries.items():
                if k in ['format_version', 'debug']:
                    continue
                path = [k]
                _assert_is_type('geometry', geometry, (dict,), path)
                _assert_has_accepted_keys_only(
                    'geometry', set(geometry.keys()),
                    {
                        "debug", "visible_bounds_width",
                        "visible_bounds_height", "visible_bounds_offset",
                        "texturewidth", "textureheight", "cape", "bones"
                    }, path)
                identifier = k
                if geometry_name in (identifier, ''):
                    return geometry, path
            raise ValueError(f'Unable to find geometry called geometry.{geometry_name}')
        raise FileIsNotAModelException(f'Unsupported format version: {self.format_version}')

    def _load_description(self, geometry: Any, geometry_path: List) -> Dict:
        '''
        Returns the description of the geometry.

        :param geometry: The geometry with description.
        :param geometry_path: The JSON path to the geometry (used for error
            messages)
        '''
        result = {
            "texture_width" : 64,
            "texture_height" : 64,
            "visible_bounds_offset" : [0, 0, 0],
            "visible_bounds_width" : 1,
            "visible_bounds_height": 1
        }
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version == '1.12.0':
            desc = geometry['description']
            path = geometry_path + ['description']

            _assert_has_required_keys(
                'description', set(desc.keys()), {'identifier'}, path)
            acceptable_keys = {
                'identifier', 'texture_width', 'texture_height',
                'visible_bounds_offset', 'visible_bounds_width',
                'visible_bounds_height'}
            _assert_has_accepted_keys_only(
                'description', set(desc.keys()), acceptable_keys, path)

            _assert_is_type(
                'identifier', desc['identifier'], (str,),
                geometry_path + ['identifier'])
            result['identifier'] = desc['identifier']
            if 'texture_width' in desc:
                _assert_is_type(
                    'texture_width', desc['texture_width'], (int, float),
                    geometry_path + ['texture_width'])
                result['texture_width'] = int(desc['texture_width'])
            if 'texture_height' in desc:
                _assert_is_type(
                    'texture_height', desc['texture_height'], (int, float),
                    geometry_path + ['texture_height'])
                result['texture_height'] = int(desc['texture_height'])
            if 'visible_bounds_offset' in desc:
                _assert_is_vector(
                    'visible_bounds_offset', desc['visible_bounds_offset'], 3,
                    (int, float), geometry_path + ['visible_bounds_offset'])
                result['visible_bounds_offset'] = desc['visible_bounds_offset']
            if 'visible_bounds_width' in desc:
                _assert_is_type(
                    'visible_bounds_width', desc['visible_bounds_width'],
                    (int, float), geometry_path + ['visible_bounds_width'])
                result['visible_bounds_width'] = desc['visible_bounds_width']
            if 'visible_bounds_height' in desc:
                _assert_is_type(
                    'visible_bounds_height', desc['visible_bounds_height'],
                    (int, float), geometry_path + ['visible_bounds_height'])
                result['visible_bounds_height'] = desc['visible_bounds_height']
            return result
        if parser_version == '1.8.0':
            desc = geometry
            path = geometry_path

            acceptable_keys = {
                "debug", "visible_bounds_width",
                "visible_bounds_height", "visible_bounds_offset",
                "texturewidth", "textureheight", "cape", "bones"}
            _assert_has_accepted_keys_only(
                'geometry', set(desc.keys()), acceptable_keys, path)

            _assert_is_type(
                'identifier', path[-1], (str,),
                geometry_path + ['identifier'])
            result['identifier'] = path[-1]
            if 'debug' in desc:
                _assert_is_type(
                    'debug', desc['debug'], (bool,),
                    geometry_path + ['debug'])
                raise ImportingNotImplementedError('debug', path + ['debug'])
            if 'texturewidth' in desc:
                _assert_is_type(
                    'texturewidth', desc['texturewidth'], (int, float),
                    geometry_path + ['texturewidth'])
                # texture_width not texturewidth (not a bug!!!)
                result['texture_width'] = int(desc['texturewidth'])
            if 'textureheight' in desc:
                _assert_is_type(
                    'textureheight', desc['textureheight'], (int, float),
                    geometry_path + ['textureheight'])
                # texture_height not textureheight (not a bug!!!)
                result['texture_height'] = int(desc['textureheight'])
            if 'visible_bounds_offset' in desc:
                _assert_is_vector(
                    'visible_bounds_offset', desc['visible_bounds_offset'], 3,
                    (int, float), geometry_path + ['visible_bounds_offset'])
                result['visible_bounds_offset'] = desc['visible_bounds_offset']
            if 'visible_bounds_width' in desc:
                _assert_is_type(
                    'visible_bounds_width', desc['visible_bounds_width'],
                    (int, float), geometry_path + ['visible_bounds_width'])
                result['visible_bounds_width'] = desc['visible_bounds_width']
            if 'visible_bounds_height' in desc:
                _assert_is_type(
                    'visible_bounds_height', desc['visible_bounds_height'],
                    (int, float), geometry_path + ['visible_bounds_height'])
                result['visible_bounds_height'] = desc['visible_bounds_height']
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _load_bones(
            self, bones: Any, bones_path: List) -> List[Dict[str, Any]]:
        '''
        Returns the bones from a list of bones, adds missing default values.

        :param bones: List of bones.
        :param bones_path: Path to the bones list (used for error messages).
        '''
        result: List = []
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version in ('1.12.0', '1.8.0'):
            _assert_is_type('bones property', bones, (list,), bones_path)
            for i, bone in enumerate(bones):
                bone_path = bones_path + [i]
                result.append(self._load_bone(bone, bone_path))
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _load_bone(self, bone: Any, bone_path: List) -> Dict[str, Any]:
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
            "render_group_id": 0,  # int >= 0
            "cubes" : [],  # List[Dict]
            "locators": {},  # Dict[...]
            "poly_mesh": None,  # Dict
            "texture_meshes": []  # List[Dict]
        }
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version == '1.12.0':
            _assert_is_type('bone', bone, (dict,), bone_path)


            _assert_has_required_keys(
                'bone', set(bone.keys()), {'name'}, bone_path)
            acceptable_keys = {
                'name', 'parent', 'pivot', 'rotation', 'mirror', 'inflate',
                'debug', 'render_group_id', 'cubes', 'locators', 'poly_mesh',
                'texture_meshes'}
            _assert_has_accepted_keys_only(
                'bone', set(bone.keys()), acceptable_keys, bone_path)

            if 'name' in bone:
                _assert_is_type(
                    'name', bone['name'], (str,), bone_path + ['name'])
                result['name'] = bone['name']
            if 'parent' in bone:
                _assert_is_type(
                    'parent', bone['parent'], (str,), bone_path + ['parent'])
                result['parent'] = bone['parent']
            if 'pivot' in bone:
                _assert_is_vector(
                    'pivot', bone['pivot'], 3, (int, float),
                    bone_path + ['pivot'])
                result['pivot'] = bone['pivot']
            if 'rotation' in bone:
                _assert_is_vector(
                    'rotation', bone['rotation'], 3, (int, float),
                    bone_path + ['rotation'])
                result['rotation'] = bone['rotation']
            if 'mirror' in bone:
                _assert_is_type(
                    'mirror', bone['mirror'], (bool,), bone_path + ['mirror'])
                result['mirror'] = bone['mirror']
            if 'inflate' in bone:
                _assert_is_type(
                    'inflate', bone['inflate'], (float, int),
                    bone_path + ['inflate'])
                result['inflate'] = bone['inflate']
            if 'debug' in bone:
                _assert_is_type(
                    'debug', bone['debug'], (bool,), bone_path + ['debug'])
                raise ImportingNotImplementedError(
                    'debug', bone_path + ['debug'])
            if 'render_group_id' in bone:
                _assert_is_type(
                    'render_group_id', bone['render_group_id'], (int, float),
                    bone_path + ['render_group_id'])
                # int >= 0
                raise ImportingNotImplementedError(
                    'render_group_id', bone_path + ['render_group_id'])
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
            if 'texture_meshes' in bone:
                # type: list
                raise ImportingNotImplementedError(
                    'texture_meshes', bone_path + ['texture_meshes'])
            return result
        if parser_version == '1.8.0':
            _assert_is_type('bone', bone, (dict,), bone_path)

            _assert_has_required_keys(
                'bone', set(bone.keys()), {'name'}, bone_path)
            acceptable_keys = {
                'name', 'reset', 'neverRender', 'parent', 'pivot', 'rotation',
                'bind_pose_rotation', 'mirror', 'inflate', 'debug',
                'render_group_id', 'cubes', 'locators', 'poly_mesh',
                'texture_meshes'}
            _assert_has_accepted_keys_only(
                'bone', set(bone.keys()), acceptable_keys, bone_path)

            if 'name' in bone:
                _assert_is_type(
                    'name', bone['name'], (str,), bone_path + ['name'])
                result['name'] = bone['name']
            if 'reset' in bone:
                _assert_is_type(
                    'reset', bone['reset'], (bool,), bone_path + ['reset'])
                raise ImportingNotImplementedError(
                    'reset', bone_path + ['reset'])
            if 'neverRender' in bone:
                _assert_is_type(
                    'neverRender', bone['neverRender'], (bool,),
                    bone_path + ['neverRender'])
                raise ImportingNotImplementedError(
                    'neverRender', bone_path + ['neverRender'])
            if 'parent' in bone:
                _assert_is_type(
                    'parent', bone['parent'], (str,), bone_path + ['parent'])
                result['parent'] = bone['parent']
            if 'pivot' in bone:
                _assert_is_vector(
                    'pivot', bone['pivot'], 3, (int, float),
                    bone_path + ['pivot'])
                result['pivot'] = bone['pivot']
            if 'rotation' in bone:
                _assert_is_vector(
                    'rotation', bone['rotation'], 3, (int, float),
                    bone_path + ['rotation'])
                result['rotation'] = bone['rotation']
            if 'bind_pose_rotation' in bone:
                _assert_is_vector(
                    'bind_pose_rotation', bone['bind_pose_rotation'], 3,
                    (int, float), bone_path + ['bind_pose_rotation'])
                raise ImportingNotImplementedError(
                    'bind_pose_rotation', bone_path + ['bind_pose_rotation'])
            if 'mirror' in bone:
                _assert_is_type(
                    'mirror', bone['mirror'], (bool,), bone_path + ['mirror'])
                result['mirror'] = bone['mirror']
            if 'inflate' in bone:
                _assert_is_type(
                    'inflate', bone['inflate'], (float, int),
                    bone_path + ['inflate'])
                result['inflate'] = bone['inflate']
            if 'debug' in bone:
                _assert_is_type(
                    'debug', bone['debug'], (bool,), bone_path + ['debug'])
                raise ImportingNotImplementedError(
                    'debug', bone_path + ['debug'])
            if 'render_group_id' in bone:
                _assert_is_type(
                    'render_group_id', bone['render_group_id'], (int, float),
                    bone_path + ['render_group_id'])
                # int >= 0
                raise ImportingNotImplementedError(
                    'render_group_id', bone_path + ['render_group_id'])
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
            if 'texture_meshes' in bone:
                # type: list
                raise ImportingNotImplementedError(
                    'texture_meshes', bone_path + ['texture_meshes'])
            return result
        raise FileIsNotAModelException('Unsupported format version')

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
        result = []
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version in ('1.12.0', '1.8.0'):
            _assert_is_type('cubes property', cubes, (list,), cubes_path)
            for i, cube in enumerate(cubes):
                cube_path = cubes_path + [i]
                result.append(
                    self._load_cube(
                        cube, cube_path, default_mirror,
                        default_inflate))
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _create_default_uv(
            self, size: Tuple[float, float, float], mirror: bool,
            uv: Tuple[float, float] = (0.0, 0.0)) -> Dict:
        '''
        Creates default UV dictionary (in per-face UV-mapping format) based on
        some other properties of a cube.

        :param size: The size of the cube.
        :param mirror: The mirror property of the cube.
        :param uv: Optional - the UV property of the cube (if the cube uses the
            standard Minecraft UV-mapping format).
        '''
        # pylint: disable=no-self-use
        width, height, depth = (int(i) for i in size)

        def _face(size: Tuple[float, float], uv: Tuple[float, float]):
            return {"uv_size": size, "uv": uv, "material_instance": ""}

        face1 = _face((depth, height), (uv[0], uv[1] + depth))
        face2 = _face((width, height), (uv[0]+depth, uv[1] + depth))
        face3 = _face((depth, height), (uv[0]+depth + width, uv[1] + depth))
        face4 = _face((width, height), (uv[0]+2*depth + width, uv[1] + depth))
        face5 = _face((width, depth), (uv[0]+depth, uv[1]))
        face6 = _face((width, depth), (uv[0]+depth + width, uv[1]))
        if mirror:
            face_west, face_east = face1, face3
        else:
            face_east, face_west = face1, face3
        # No mirror: | # Mirror:
        #   5 6      | #   5 6
        # 1 2 3 4    | # 3 2 1 4
        result: Dict = {
            "north": face2, "south": face4, "east": face_east,
            "west": face_west, "up": face5, "down": face6}
        return result

    def _load_cube(
            self, cube: Any, cube_path: List, default_mirror: bool,
            default_inflate: float) -> Dict[str, Any]:
        '''
        Returns a cube with added all of the missing default values of the
        properties.

        :param cube: Part of the JSON dict that has the inforation about the
            cube.
        :param cube_path: JSON path to the cube (used for error messages).
        :param default_mirror: Mirror value of a bone that owns this cube.
        '''
        result = {
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
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version == '1.12.0':
            _assert_is_type('cube', cube, (dict,), cube_path)
            # There is no required keys {} is a valid cube
            acceptable_keys = {
                "mirror", "inflate", "pivot", "rotation", "origin",
                "size", "uv"}
            _assert_has_accepted_keys_only(
                'cube', set(cube.keys()), acceptable_keys, cube_path)
            if 'origin' in cube:
                _assert_is_vector(
                    'origin', cube['origin'], 3, (int, float),
                    cube_path + ['origin'])
                result['origin'] = cube['origin']
            if 'size' in cube:
                _assert_is_vector(
                    'size', cube['size'], 3, (int, float),
                    cube_path + ['size'])
                result['size'] = cube['size']
            if 'rotation' in cube:
                _assert_is_vector(
                    'rotation', cube['rotation'], 3, (int, float),
                    cube_path + ['rotation'])
                result['rotation'] = cube['rotation']
            if 'pivot' in cube:
                _assert_is_vector(
                    'pivot', cube['pivot'], 3, (int, float),
                    cube_path + ['pivot'])
                result['pivot'] = cube['pivot']
            if 'inflate' in cube:
                _assert_is_type(
                    'inflate', cube['inflate'], (int, float), cube_path + ['inflate'])
                result['inflate'] = cube['inflate']
            if 'mirror' in cube:
                _assert_is_type(
                    'mirror', cube['mirror'], (bool,), cube_path + ['mirror'])
                result['mirror'] = cube['mirror']
            if 'uv' in cube:
                _assert_is_type(
                    'uv', cube['uv'], (list, dict), cube_path + ['uv'])
                if isinstance(cube['uv'], dict):
                    result['uv'] = self._load_uv(
                        cube['uv'], cube_path + ['uv'],
                        tuple(result['size'])  # type: ignore
                    )
                elif isinstance(cube['uv'], list):
                    _assert_is_vector(
                        'uv', cube['uv'], 2, (int, float), cube_path + ['uv'])
                    result['uv'] = self._create_default_uv(
                        tuple(result['size']),  # type: ignore
                        result['mirror'],  # type: ignore
                        tuple(cube['uv']))  # type: ignore
                else:
                    raise FileIsNotAModelException(
                        f'{cube_path + ["uv"]}::{"uv"} is not an '
                        f'instance of {(list, dict)}')
            # Create default UV based on size and mirror
            if result['uv'] is None:
                result['uv'] = result['uv'] = self._create_default_uv(
                    tuple(result['size']),  # type: ignore
                    result['mirror'])  # type: ignore
            return result
        if parser_version == '1.8.0':
            _assert_is_type('cube', cube, (dict,), cube_path)
            # There is no required keys {} is a valid cube
            acceptable_keys = {"origin", "size", "uv", "inflate", "mirror"}
            _assert_has_accepted_keys_only(
                'cube', set(cube.keys()), acceptable_keys, cube_path)
            if 'origin' in cube:
                _assert_is_vector(
                    'origin', cube['origin'], 3, (int, float),
                    cube_path + ['origin'])
                result['origin'] = cube['origin']
            if 'size' in cube:
                _assert_is_vector(
                    'size', cube['size'], 3, (int, float),
                    cube_path + ['size'])
                result['size'] = cube['size']
            if 'inflate' in cube:
                _assert_is_type(
                    'inflate', cube['inflate'], (int, float), cube_path + ['inflate'])
                result['inflate'] = cube['inflate']
            if 'mirror' in cube:
                _assert_is_type(
                    'mirror', cube['mirror'], (bool,), cube_path + ['mirror'])
                result['mirror'] = cube['mirror']
            if 'uv' in cube:
                _assert_is_type(
                    'uv', cube['uv'], (list,), cube_path + ['uv'])
                _assert_is_vector(
                    'uv', cube['uv'], 2, (int, float), cube_path + ['uv'])
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
        raise FileIsNotAModelException('Unsupported format version')

    def _load_poly_mesh(
            self, poly_mesh: Any, poly_mesh_path: List) -> Dict[str, Any]:
        '''
        Returns a cube with added all of the missing default values of the
        properties.

        :param cube: Part of the JSON dict that has the inforation about the
            cube.
        :param cube_path: JSON path to the cube (used for error messages).
        :param default_mirror: Mirror value of a bone that owns this cube.
        '''
        result = {
            'normalized_uvs': False,
            'positions': [],
            'normals': [],
            'uvs': [],
            'polys': [],  # 'tri_list' or 'quad_list" or list with data
        }
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version in ['1.12.0', '1.8.0']:
            _assert_is_type('poly_mesh', poly_mesh, (dict,), poly_mesh_path)
            # There is no required keys {} is a valid poly_mesh
            _assert_has_required_keys(
                'poly_mesh', set(poly_mesh.keys()), {'polys'}, poly_mesh_path)
            acceptable_keys = {
                "normalized_uvs", "positions", "normals", "uvs", "polys"}
            _assert_has_accepted_keys_only(
                'poly_mesh', set(poly_mesh.keys()), acceptable_keys,
                poly_mesh_path)
            # Acceptable keys
            if 'normalized_uvs' in poly_mesh:
                _assert_is_type(
                    'normalized_uvs', poly_mesh['normalized_uvs'], (bool,),
                    poly_mesh_path + ['normalized_uvs'])
                result['normalized_uvs'] = poly_mesh['normalized_uvs']
            if 'positions' in poly_mesh:
                positions = poly_mesh['positions']
                positions_path = poly_mesh_path + ['position']
                _assert_is_type('positions', positions, (list,), positions_path)
                for position_id, position in enumerate(positions):
                    _assert_is_vector(
                        'position', position, 3, (float, int,),
                        positions_path + [position_id])
                    result['positions'].append(tuple(position))  # type: ignore
            if 'normals' in poly_mesh:
                normals = poly_mesh['normals']
                normals_path = poly_mesh_path + ['normal']
                _assert_is_type('normals', normals, (list,), normals_path)
                for normal_id, normal in enumerate(normals):
                    _assert_is_vector(
                        'normal', normal, 3, (float, int,),
                        normals_path + [normal_id])
                    result['normals'].append(tuple(normal))  # type: ignore
            if 'uvs' in poly_mesh:
                uvs = poly_mesh['uvs']
                uvs_path = poly_mesh_path + ['uv']
                _assert_is_type('uvs', uvs, (list,), uvs_path)
                for uv_id, uv in enumerate(uvs):
                    _assert_is_vector(
                        'uv', uv, 2, (float, int,),
                        uvs_path + [uv_id])
                    result['uvs'].append(tuple(uv))  # type: ignore
            # Required keys
            _assert_is_type(
                'polys', poly_mesh['polys'], (str, list),
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
                    curr_result_poly: List[Tuple[int, int, int]] = []
                    result['polys'].append(curr_result_poly)  # type: ignore
                    poly_path = polys_path + [poly_id]
                    _assert_is_type(
                        'poly', poly, (list,), poly_path)
                    for poly_vertex_id, poly_vertex in enumerate(poly):
                        _assert_is_vector(
                            'vertex', poly_vertex, 3, (int,),
                            poly_path + [poly_vertex_id])
                        curr_result_poly.append(
                            tuple(poly_vertex))  # type: ignore
            else:
                raise FileIsNotAModelException(
                    f'{poly_mesh_path + ["polys"]}::{"polys"} is not an '
                    f'instance of {(str, list)}')
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _create_default_polys(
            self, grouping_mode: str, positions: List[List[float]],
            normals: List[List[float]], uvs: List[List[float]],
            poly_mesh_path: List[str]
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
            raise FileIsNotAModelException(
                f'{poly_mesh_path + ["polys"]}::{"polys"} is not an a list of polys or a '
                'literal string "quad_list" or "tri_list"')
        # Check if positions, normals and uvs are the same lengts
        pos_length = len(positions)
        if not (pos_length == len(normals) == len(uvs)):
            raise FileIsNotAModelException(
                f'{poly_mesh_path}::"positions", "normals" and "uvs" are not '
                'the same lengths. They must be the same lengths in "tri_list"'
                ' and "quad_list" polys grouping mode.')
        # Check if list length is divisible by the group_size
        if not (pos_length % group_size == 0):
            raise FileIsNotAModelException(
                f'{poly_mesh_path}::"positions" list length must be '
                f'divisible by {group_size} in {grouping_mode}.')
        # Build default polys property in list format
        result = np.repeat(
            range(pos_length), 3
        ).reshape(
            -1, group_size, 3
        ).to_list()
        return result

    def _load_uv(
            self, uv: Any, uv_path: List,
            cube_size: Tuple[float, float, float]) -> Dict[str, Any]:
        '''
        Returns UV and adds all of the missing default values of its
        properties.

        :param uv: Part of the JSON dict that has the inforation about the uv.
        :param uv_path: Path to the UV (used for error messages).
        :param cube_size: Size of the cube which is being mapped (used for
            getting default UV values).
        '''
        width, height, depth = cube_size
        def _face(size: Tuple[float, float], uv: Tuple[float, float]):
            return {"uv_size": size, "uv": uv, "material_instance": ""}
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

        parser_version = pick_version_parser(
            ('1.12.0',), self.format_version)
        if parser_version == '1.12.0':
            _assert_is_type('uv', uv, (dict,), uv_path)
            # There is no required keys {} is a valid UV
            acceptable_keys = {"north", "south", "east", "west", "up", "down"}
            _assert_has_accepted_keys_only(
                'uv', set(uv.keys()), acceptable_keys, uv_path)
            if "north" in uv:
                _assert_is_type(
                    'north', uv['north'], (dict,), uv_path + ['north'])
                result["north"] = self._load_uv_face(
                    uv["north"], uv_path + ["north"], (depth, height))
            if "south" in uv:
                _assert_is_type(
                    'south', uv['south'], (dict,), uv_path + ['south'])
                result["south"] = self._load_uv_face(
                    uv["south"], uv_path + ["south"], (width, height))
            if "east" in uv:
                _assert_is_type(
                    'east', uv['east'], (dict,), uv_path + ['east'])
                result["east"] = self._load_uv_face(
                    uv["east"], uv_path + ["east"], (depth, height))
            if "west" in uv:
                _assert_is_type(
                    'west', uv['west'], (dict,), uv_path + ['west'])
                result["west"] = self._load_uv_face(
                    uv["west"], uv_path + ["west"], (width, height))
            if "up" in uv:
                _assert_is_type(
                    'up', uv['up'], (dict,), uv_path + ['up'])
                result["up"] = self._load_uv_face(
                    uv["up"], uv_path + ["up"], (width, depth))
            if "down" in uv:
                _assert_is_type(
                    'down', uv['down'], (dict,), uv_path + ['down'])
                result["down"] = self._load_uv_face(
                    uv["down"], uv_path + ["down"], (width, depth))
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _load_uv_face(
            self, uv_face: Any, uv_face_path: List,
            default_size: Tuple[float, float]) -> Dict[str, Any]:
        '''
        Returns UV and adds all of the missing default values of its
        properties.

        :param uv_face: Part of the JSON dict that has the inforation about the
          uv face.
        :param uv_face_path: Path to the uv face (used for error messages).
        :param default_size: Default size of the UV face.
        '''
        result = {
            "uv_size": default_size, "uv": [0, 0], "material_instance": ""
        }
        parser_version = pick_version_parser(
            ('1.12.0',), self.format_version)
        if parser_version == '1.12.0':
            _assert_is_type('uv_face', uv_face, (dict,), uv_face_path)
            _assert_has_required_keys(
                'uv', set(uv_face.keys()), {'uv'}, uv_face_path)
            _assert_has_accepted_keys_only(
                'uv_face', set(uv_face.keys()),
                {"uv", "uv_size", "material_instance"}, uv_face_path)


            _assert_is_vector(
                'uv', uv_face['uv'], 2, (int, float),
                uv_face_path + ['uv'])
            result["uv"] = uv_face["uv"]
            if "uv_size" in uv_face:
                _assert_is_vector(
                    'uv_size', uv_face['uv_size'], 2, (int, float),
                    uv_face_path + ['uv_size'])
                result["uv_size"] = uv_face["uv_size"]
            if "material_instance" in uv_face:
                _assert_is_type(
                    'material_instance', uv_face['material_instance'], (str,),
                    uv_face_path + ['material_instance'])
                raise ImportingNotImplementedError(
                    'material_instance', uv_face_path + ['material_instance'])
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _load_locators(
            self, locators: Any, locators_path: List) -> Dict[str, Any]:
        '''
        Returns the locators from the list of locators with added missing
        default values.

        :param locators: List of the locators.
        :param locators_path: Path to the locators list (used for error
            messages)
        '''
        result = {}
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version in ['1.12.0', '1.8.0']:
            _assert_is_type(
                'locators property', locators, (dict,), locators_path)
            for i, locator in locators.items():
                locator_path = locators_path + [i]
                result[i] = self._load_locator(locator, locator_path)
            return result
        raise FileIsNotAModelException('Unsupported format version')

    def _load_locator(self, locator: Any, locator_path: List) -> Any:
        '''
        Returns the locator with added missing default values.

        :param locator: The locator
        :param locator_path: Path to the locator
        '''
        parser_version = pick_version_parser(
            ('1.12.0', '1.8.0'), self.format_version)
        if parser_version == '1.12.0':
            if isinstance(locator, list):
                _assert_is_vector('locator', locator, 3, (int, float), locator_path)
                return locator

            if isinstance(locator, dict):
                raise ImportingNotImplementedError('locator', locator_path)
            raise FileIsNotAModelException(
                f'{locator_path + ["locator"]}::{"locator"} is not an '
                f'instance of {(list, dict)}')
        if parser_version == '1.8.0':
            _assert_is_type('locator', locator, (list,), locator_path)
            _assert_is_vector('locator', locator, 3, (int, float), locator_path)
            return locator
        raise FileIsNotAModelException('Unsupported format version')


class ImportLocator:
    '''
    Represents Minecraft locator during import operation.

    :param name: Name of the locator.
    :param position: The position of the locator.
    '''
    def __init__(self, name: str, position: Tuple[float, float, float]):
        self.name = name
        self.position = position

        self.blend_empty: Optional[bpy.types.Object] = None


class ImportCube:
    '''
    Represents minecraft cube during import operation.

    :param data: The part of the Minecraft model JSON dict that represents this
        cube.
    '''
    def __init__(
            self, data: Dict):
        '''
        Creates ImportCube object created from a dictionary (part of the JSON)
        file in the model.

        # Arguments:
        - `data: Dict` - the part of the Minecraft model JSON file that represents
        the cube.
        '''
        self.blend_cube: Optional[bpy.types.Object] = None

        self.uv: Dict = data['uv']
        self.mirror: bool = data['mirror']
        self.inflate: bool = data['inflate']
        self.origin: Tuple[float, float, float] = tuple(  # type: ignore
            data['origin'])
        self.pivot: Tuple[float, float, float] = tuple(  # type: ignore
            data['pivot'])
        self.size: Tuple[float, float, float] = tuple(  # type: ignore
            data['size'])
        self.rotation: Tuple[float, float, float] = tuple(  # type: ignore
            data['rotation'])


class ImportPolyMesh:
    '''
    Represents Minecraft poly_mesh during import operation.

    :param data: The part of the Minecraft model JSON dict that represents this
        poly_mesh.
    '''
    def __init__(
            self, data: Dict):
        '''
        Creates ImportPolyMesh object created from a dictionary (part of the
        JSON) file in the model.

        :param data: The part of the Minecraft model JSON file that represents
        the poly_mesh.
        '''
        self.blend_object: Optional[bpy.types.Object] = None

        self.normalized_uvs: bool = data['normalized_uvs']
        self.positions: List[Tuple[float, float, float]] = data['positions']
        self.normals: List[Tuple[float, float, float]] = data['normals']
        self.uvs: List[Tuple[float, float]] = data['uvs']
        self.polys: List[List[Tuple[int, int, int]]] = data['polys']

    def unpack_data(self):
        '''
        Unpacks the data about polymesh to a format more useful in blender.
        The data is not converted to minecraft format.
        '''
        # positions -> vertices
        # polys -> [loops]
        #   vertex ID
        #   loop normal ID
        #   loop uv ID
        # normals -> normals (coordinates)
        # uvs -> uvs (coordinates)

        # vertex IDs to create polygons
        blender_polygons: List[List[int]] = []
        # List of vectors with normals
        blender_normals: List[Tuple[float, float, float]] = []
        # List of vectors with UVs
        blender_uvs: List[Tuple[float, float]] = []

        # TODO - this function or earlier data processing should make sure
        # the indices doesn't go out of bounds
        for poly in self.polys:
            curr_polygon: List[int] = []
            for vertex_id, normal_id, uv_id in poly:
                curr_polygon.append(vertex_id)
                blender_normals.append(self.normals[normal_id])
                blender_uvs.append(self.uvs[uv_id])
            blender_polygons.append(curr_polygon)
        return blender_polygons, self.positions, blender_normals, blender_uvs


class ImportBone:
    '''
    Represents Minecraft bone during import operation.

    :param data: The part of the Minecraft model JSON dict that represents the
        bone.
    '''
    def __init__(self, data: Dict):
        self.blend_empty: Optional[bpy.types.Object] = None

        # Locators
        locators: List[ImportLocator] = []
        for k, v in data['locators'].items():
            locators.append(ImportLocator(k, tuple(v)))  # type: ignore
        # Cubes
        import_cubes: List[ImportCube] = []
        for cube in data['cubes']:
            import_cubes.append(ImportCube(cube))

        self.name: str = data['name']
        self.parent: str = data['parent']
        self.cubes = import_cubes
        self.poly_mesh: Optional[ImportPolyMesh] = None
        if data['poly_mesh'] is not None:
            self.poly_mesh = ImportPolyMesh(data['poly_mesh'])
        self.locators = locators
        self.pivot: Tuple[float, float, float] = tuple(  # type: ignore
            data['pivot'])
        self.rotation: Tuple[float, float, float] = tuple(  # type: ignore
            data['rotation'])
        self.mirror = data['mirror']


class ImportGeometry:
    '''
    Represents whole Minecraft geometry during import operation.

    :param loader: Loader object with all of the required model properties.
    '''
    def __init__(self, loader: ModelLoader):
        # Set the values
        self.identifier = loader.description['identifier']
        self.texture_width = int(loader.description['texture_width'])
        self.texture_height = int(loader.description['texture_height'])
        self.visible_bounds_offset = loader.description['visible_bounds_offset']
        self.visible_bounds_width = loader.description['visible_bounds_width']
        self.visible_bounds_height = loader.description['visible_bounds_height']
        self.bones: Dict[str, ImportBone] = {}
        self.uv_converter = CoordinatesConverter(
            np.array([[0, self.texture_width], [0, self.texture_height]]),
            np.array([[0, 1], [1, 0]])
        )

        # Read bones
        for bone in loader.bones:
            import_bone = ImportBone(bone)
            self.bones[import_bone.name] = import_bone

    def build_with_empties(self, context: bpy_types.Context):
        '''
        Builds the geometry in Blender. Uses empties to represent Minecraft
        bones.

        :param context: The context of running the operator.
        '''
        # Create objects - and set their pivots
        for bone in self.bones.values():
            # 1. Spawn bone (empty)
            bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0), radius=0.2)
            bone_obj: bpy.types.Object
            bone_obj = bone.blend_empty = context.object
            _mc_pivot(bone_obj, bone.pivot)  # 2. Apply translation
            bone_obj.name = bone.name  # 3. Apply custom properties
            bone_obj.nusiq_mcblend_object_properties.is_bone = True
            for cube in bone.cubes:
                cube_obj: bpy.types.Object
                # 1. Spawn cube
                bpy.ops.mesh.primitive_cube_add(
                    size=1, enter_editmode=False, location=(0, 0, 0)
                )
                cube_obj = cube.blend_cube = context.object

                # 2. Set uv
                # warning! Moving this code below cube transformation would
                # break it because bound_box is not getting updated properly
                # before the end of running of the opperator.
                cube_obj.nusiq_mcblend_object_properties.mirror = cube.mirror
                _set_uv(
                    self.uv_converter,
                    CubePolygons.build(cube_obj, cube.mirror),
                    cube.uv, cube_obj.data.uv_layers.active)

                # 3. Set size & inflate
                cube.blend_cube.nusiq_mcblend_object_properties.inflate = (
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
                blender_uvs: List[Tuple[float, float]] = []
                blender_vertices: List[Tuple[float, float, float]] = []

                for vertex in bone.poly_mesh.positions:
                    blender_vertices.append((
                            vertex[0] / MINECRAFT_SCALE_FACTOR,
                            vertex[2] / MINECRAFT_SCALE_FACTOR,
                            vertex[1] / MINECRAFT_SCALE_FACTOR))
                for poly in bone.poly_mesh.polys:
                    curr_polygon: List[int] = []
                    for vertex_id, normal_id, uv_id in poly:
                        if vertex_id in curr_polygon:
                            # vertex can apear only onece per polygon. The
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
                mesh.from_pydata(blender_vertices, [], blender_polygons)

                if not mesh.validate():  # Valid geometry
                    # 3. Create an object and connect mesh to it
                    poly_mesh_obj = bpy.data.objects.new('poly_mesh', mesh)
                    context.collection.objects.link(poly_mesh_obj)
                    bone.poly_mesh.blend_object = poly_mesh_obj
                    # 4. Set mesh normals and UVs
                    mesh.create_normals_split()
                    mesh.use_auto_smooth = True
                    mesh.normals_split_custom_set(blender_normals)
                    if mesh.uv_layers.active is None:
                        mesh.uv_layers.new()
                    uv_layer = mesh.uv_layers.active.data  # type: ignore
                    for i, uv in enumerate(blender_uvs):
                        uv_layer[i].uv = uv
                else:
                    del mesh
                    raise FileIsNotAModelException('Invalid poly_mesh geometry!')

            for locator in bone.locators:
                # 1. Spawn locator (empty)
                locator_obj: bpy.types.Object
                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0), radius=0.1)
                locator_obj = locator.blend_empty = context.object
                _mc_pivot(locator_obj, locator.position)  # 2. Apply translation
                # 3. Apply custom properties
                locator_obj.name = locator.name

        # Parent objects (keep offset)
        for bone in self.bones.values():
            bone_obj = bone.blend_empty
            # 1. Parent bone keep transform
            if bone.parent is not None and bone.parent in self.bones:
                parent_obj: bpy.types.Object = self.bones[
                    bone.parent
                ].blend_empty
                context.view_layer.update()
                bone_obj.parent = parent_obj
                bone_obj.matrix_parent_inverse = (
                    parent_obj.matrix_world.inverted()
                )
            # 2. Parent cubes keep transform
            for cube in bone.cubes:
                cube_obj = cube.blend_cube
                context.view_layer.update()
                cube_obj.parent = bone_obj
                cube_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted()
                )
            # 3. Parent poly_mesh keep transform
            if bone.poly_mesh is not None:
                poly_mesh_obj = bone.poly_mesh.blend_object
                context.view_layer.update()
                poly_mesh_obj.parent = bone_obj
                poly_mesh_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted()
                )

            # 4. Parent locators keep transform
            for locator in bone.locators:
                locator_obj = locator.blend_empty
                context.view_layer.update()
                locator_obj.parent = bone_obj
                locator_obj.matrix_parent_inverse = (
                    bone_obj.matrix_world.inverted()
                )

        # Rotate objects
        for bone in self.bones.values():
            bone_obj = bone.blend_empty
            context.view_layer.update()
            _mc_rotate(bone_obj, bone.rotation)
            for cube in bone.cubes:
                cube_obj = cube.blend_cube
                _mc_rotate(cube_obj, cube.rotation)

    def build_with_armature(self, context: bpy_types.Context):
        '''
        Builds the geometry in Blender. Uses armature and bones to represent
        the Minecraft bones.

        :param context: The context of running the operator.
        '''
        # Build everything using empties
        self.build_with_empties(context)

        # Build armature
        # Create empty armature and enter edit mode:
        bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.armature.delete()
        # Save the armature
        armature = context.object
        edit_bones = armature.data.edit_bones
        # Create bones
        for bone in self.bones.values():
            add_bone(edit_bones, 0.3, bone)

        # Parent bones
        for bone in self.bones.values():
            # 1. Parent bone keep transform
            if bone.parent is not None and bone.parent in self.bones:
                parent_obj: bpy.types.Object = self.bones[
                    bone.parent
                ]
                # context.view_layer.update()
                edit_bones[bone.name].parent = edit_bones[parent_obj.name]
        bpy.ops.object.mode_set(mode='OBJECT')

        def parent_bone_keep_transform(
                obj: bpy.types.Object, bone: ImportBone):
            '''
            Used for replacing empty parent with new bone parent
            '''
            context.view_layer.update()

            # Copy matrix_parent_inverse from previous parent
            # It can be copied because old parent (locator) has the same
            # transformation as the new one (bone)
            parent_inverse = (
                obj.matrix_parent_inverse.copy()  # type:ignore
            )

            obj.parent = armature  # type: ignore
            obj.parent_bone = bone.name  # type: ignore
            obj.parent_type = 'BONE'  # type: ignore

            obj.matrix_parent_inverse = parent_inverse  # type: ignore

            # Correct parenting to tail of the bone instead of head
            context.view_layer.update()
            blend_bone = armature.pose.bones[bone.name]
            # pylint: disable=no-member
            correction = mathutils.Matrix.Translation(
                blend_bone.head-blend_bone.tail
            )
            obj.matrix_world = (  # type: ignore
                correction @
                obj.matrix_world  # type: ignore
            )

        # Replace empties with bones
        for bone in self.bones.values():
            bone_obj = bone.blend_empty

            # 2. Parent cubes keep transform
            for cube in bone.cubes:
                parent_bone_keep_transform(cube.blend_cube, bone)

            # 3. Parent poly_mesh keep transform
            if bone.poly_mesh is not None:
                parent_bone_keep_transform(bone.poly_mesh.blend_object, bone)

            # 4. Parent locators keep transform
            for locator in bone.locators:
                parent_bone_keep_transform(locator.blend_empty, bone)

            # remove the locators
            bpy.data.objects.remove(bone_obj)


def _mc_translate(
        obj: bpy.types.Object, mctranslation: Tuple[float, float, float],
        mcsize: Tuple[float, float, float],
        mcpivot: Tuple[float, float, float]
    ):
    '''
    Translates a Blender object using a translation vector written in Minecraft
    coordinates system.

    :param obj: Blender object to transform..
    :param mctranslation: Minecraft translation.
    :param mcsize: Minecraft size.
    :param mcpivot: Minecraft pivot.
    '''
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
        vertex.co += (translation - pivot_offset + size_offset)

def _mc_set_size(
        obj: bpy.types.Object, mcsize: Tuple[float, float, float],
        inflate: Optional[float]=None):
    '''
    Scales a Blender object using scale vector written in Minecraft coordinates
    system.

    :param obj: Blender object
    :param mcsize: Minecraft object size.
    '''
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
    data = obj.data
    # 0. ---; 1. --+; 2. -+-; 3. -++; 4. +--; 5. +-+; 6. ++- 7. +++
    data.vertices[0].co = mathutils.Vector(pos_delta * np.array([-1, -1, -1]))
    data.vertices[1].co = mathutils.Vector(pos_delta * np.array([-1, -1, 1]))
    data.vertices[2].co = mathutils.Vector(pos_delta * np.array([-1, 1, -1]))
    data.vertices[3].co = mathutils.Vector(pos_delta * np.array([-1, 1, 1]))
    data.vertices[4].co = mathutils.Vector(pos_delta * np.array([1, -1, -1]))
    data.vertices[5].co = mathutils.Vector(pos_delta * np.array([1, -1, 1]))
    data.vertices[6].co = mathutils.Vector(pos_delta * np.array([1, 1, -1]))
    data.vertices[7].co = mathutils.Vector(pos_delta * np.array([1, 1, 1]))

def _mc_pivot(obj: bpy.types.Object, mcpivot: Tuple[float, float, float]):
    '''
    Moves a pivot of an Blender object using pivot value in Minecraft
    coordinates system.

    :param obj: Blender object
    :param mcpivot: Minecraft object pivot point.
    '''
    translation = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    obj.location += translation

def _mc_rotate(
        obj: bpy.types.Object, mcrotation: Tuple[float, float, float]
    ):
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
        uv: Dict, uv_layer: bpy.types.MeshUVLoopLayer):
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
            cube_polygon: CubePolygon, size: Tuple[float, float],
            uv: Tuple[float, float]):
        cp_loop_indices = cube_polygon.side.loop_indices
        cp_order = cube_polygon.order

        left_down = cp_loop_indices[cp_order[0]]
        right_down = cp_loop_indices[cp_order[1]]
        right_up = cp_loop_indices[cp_order[2]]
        left_up = cp_loop_indices[cp_order[3]]

        uv_data[left_down].uv = uv_converter.convert((uv[0], uv[1] + size[1]))
        uv_data[right_down].uv = uv_converter.convert(
            (uv[0] + size[0], uv[1] + size[1]))
        uv_data[right_up].uv = uv_converter.convert((uv[0] + size[0], uv[1]))
        uv_data[left_up].uv = uv_converter.convert((uv[0], uv[1]))

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
        edit_bones: bpy.types.bpy_prop_collection,
        length: float, import_bone: ImportBone):
    '''
    :param edit_bones: edit bones of the armature (from
        armature.data.edit_bones).
    :param length: length of the bone.
    :param import_bone: import bone with all of the Minecraft data
        and the reference to empty object that currently represents the bone.
    '''
    matrix_world: mathutils.Matrix = (
        import_bone.blend_empty.matrix_world  # type: ignore
    )
    bone = edit_bones.new(import_bone.name)
    bone.head, bone.tail = (0.0, 0.0, 0.0), (0.0, length, 0.0)
    bone.matrix = matrix_world
