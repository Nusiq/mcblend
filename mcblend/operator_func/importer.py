'''
Functions and objects related to importing Minecraft models to Blender.
'''
from __future__ import annotations

import math
from typing import cast, Dict, List, Optional, Any, Tuple

import numpy as np

import bpy_types
import mathutils
import bpy

from .common import MINECRAFT_SCALE_FACTOR
from .exception import InvalidDictPathException
from .json_tools import get_path

def _assert(expr: bool, msg: str = ''):
    '''
    Same functionality as normal assert statement but works even
    if __debug__ is False.

    # Arguments:
    `expr: bool` - boolean expression
    `msg: str` - error message for assertion error if expression is false.
    '''
    if not expr:
        raise AssertionError(msg)


def _assert_is_vector(
        vect: Any, length: int, types: Tuple, msg: str = ''
    ) -> None:
    '''
    Asserts that the "vect" is "length" long vector and all of the items
    in the vector are instances of types from types list.

    # Arguments:
    - `vect: Any` - input iterable
    - `length: int` - expected length of the iterable
    - `types: Tuple` - expected types of the items of iterable
    - `msg: str` - error message for AssertionError if assertion fails.
    '''
    _assert(isinstance(vect, list), msg)
    _assert(len(vect) == length, msg)
    _assert(all([isinstance(i, types) for i in vect]), msg)


def _assert_is_model_file(model: Any) -> None:
    '''
    Asserts that the input dictionary is a valid model file.

    # Arguments:
    - `model: Any` - a dictionary
    '''
    _assert(isinstance(model, dict), 'Model file must be an object')
    _assert(
        set(model.keys()) == {'format_version', 'minecraft:geometry'},
        'Model file must have format_version and minecraft:geometry properties'
    )

    _assert(model['format_version'] == "1.12.0", 'Unsuported format version')

    geometries = model['minecraft:geometry']
    _assert(
        isinstance(geometries, list),
        'minecraft:geometry property must be a list'
    )
    _assert(
        len(geometries) > 0, 'minecraft:geometry must have at least one item'
    )

    # minecraft:geometry
    for geometry in geometries:
        _assert(
            isinstance(geometry, dict),
            'Every item from minecraft:geometry list must be an object'
        )
        _assert(
            set(geometry.keys()) == {'description', 'bones'},
            'Every item from minecraft:geometry list must have description '
            'and bones properties'
        )
        desc = geometry['description']
        bones = geometry['bones']

        # minecraft:geometry -> description
        _assert(isinstance(desc, dict), 'Geometry description must be an object')
        _assert(
            set(desc.keys()) == {
                'identifier', 'texture_width',
                'texture_height', 'visible_bounds_width',
                'visible_bounds_height', 'visible_bounds_offset'
            },
            'Geometry description must have following properties: '
            'identifier, texture_width, texture_height, visible_bounds_width, '
            'visible_bounds_height, visible_bounds_offset'
        )
        _assert(
            isinstance(desc['identifier'], str),
            'Geometry identifier must be a string'
        )
        _assert(
            isinstance(desc['texture_width'], int),
            'texture_width must be an integer'
        )
        _assert(
            isinstance(desc['texture_height'], int),
            'texture_height must be an integer'
        )
        _assert(
            desc['texture_width'] >= 0,
            'texture_width must be greater than 0'
        )
        _assert(
            desc['texture_height'] >= 0,
            'texture_height must be greater than 0'
        )

        _assert(
            isinstance(desc['visible_bounds_width'], (float, int)),
            'visible_bounds_width must be a number'
        )
        _assert(
            isinstance(desc['visible_bounds_height'], (float, int)),
            'visible_bounds_height must be a number'
        )
        _assert_is_vector(
            desc['visible_bounds_offset'], 3, (int, float),
            'visible_bounds_offset must be a vector of 3 numbers'
        )

        # minecraft:geometry -> bones
        _assert(isinstance(bones, list))
        for bone in bones:
            _assert(isinstance(bone, dict), 'Every bone must be an object')

            _assert(
                set(bone.keys()) <= {  # acceptable keys
                    'name', 'cubes', 'pivot', 'rotation', 'parent', 'locators'
                },
                'Only properties from this list are allowed for bones: '
                'name, cubes, pivot, rotation, parent, locators'
            )
            _assert(  # obligatory keys
                set(bone.keys()) >= {'name', 'cubes', 'pivot', 'rotation'},
                'Every bone must have following properties: name, cubes, '
                'pivot, rotation'
            )
            _assert(isinstance(bone['name'], str), 'Bone name must be a string')

            _assert_is_vector(
                bone['pivot'], 3, (int, float),
                'pivot property of a bone must be a vector of 3 numbers'
            )
            _assert_is_vector(
                bone['rotation'], 3, (int, float),
                'rotation property of a bone must be a vector of 3 numbers'
            )
            if 'parent' in bone:
                _assert(
                    isinstance(bone['parent'], str),
                    'parent property of a bone must be a string'
                )
            # minecraft:geometry -> bones -> locators
            if 'locators' in bone:
                _assert(
                    isinstance(bone['locators'], dict),
                    'locators property of a bone must be an object'
                )
                for locator_name, locator in bone['locators'].items():
                    _assert(
                        isinstance(locator_name, str),
                        'Locator name property must be a string'
                    )
                    _assert_is_vector(
                        locator, 3, (int, float),
                        'Locator value must be a vector of 3 numbers'
                    )
            # minecraft:geometry -> bones -> cubes
            _assert(
                isinstance(bone['cubes'], list),
                'cubes property of a bone must be a list'
            )
            for cube in bone['cubes']:
                _assert(isinstance(cube, dict), 'Every cube must be an object')
                _assert(
                    set(cube.keys()) <= {  # acceptable keys
                        'uv', 'size', 'origin', 'pivot', 'rotation', 'mirror'
                    },
                    'Only properties from this list are allowed for cubes: '
                    'uv, size, origin, pivot, rotation, mirror'
                )
                _assert(
                    set(cube.keys()) >= {  # obligatory keys
                        'uv', 'size', 'origin', 'pivot', 'rotation'
                    },
                    'Every cube must have following properties: '
                    'uv, size, origin, pivot, rotation'
                )
                _assert_is_vector(
                    cube['uv'], 2, (int, float),
                    'size property of a cube must be a vector of 2 numbers'
                )
                _assert_is_vector(
                    cube['size'], 3, (int, float),
                    'size property of a cube must be a vector of 3 numbers'
                )
                _assert_is_vector(
                    cube['origin'], 3, (int, float),
                    'origin property of a cube must be a vector of 3 numbers'
                )
                _assert_is_vector(
                    cube['pivot'], 3, (int, float),
                    'pivot property of a cube must be a vector of 3 numbers'
                )
                _assert_is_vector(
                    cube['rotation'], 3, (int, float),
                    'rotation property of a cube must be a vector of 3 numbers'
                )
                if 'mirror' in cube:
                    _assert(isinstance(cube['mirror'], bool))


class ImportLocator:
    '''Represents Minecraft locator during import operation.'''
    def __init__(self, name: str, position: Tuple[float, float, float]):
        self.name = name
        self.position = position

        self.blend_empty: Optional[bpy_types.Object] = None


class ImportCube:
    '''Represents minecraft cube during import operation.'''
    def __init__(
            self, data: Dict):
        '''
        Creates ImportCube object created from a dictinary (part of the JSON)
        file in the model.

        # Arguments:
        - `data: Dict` - the part of the Minecraft model JSON file that represents
        the cube.
        '''
        self.blend_cube: Optional[bpy_types.Object] = None

        self.uv: Tuple[int, int] = data['uv']
        self.mirror: bool = False if 'mirror' not in data else data['mirror']
        self.origin: Tuple[float, float, float] = tuple(  # type: ignore
            data['origin'])
        self.pivot: Tuple[float, float, float] = tuple(  # type: ignore
            data['pivot'])
        self.size: Tuple[float, float, float] = tuple(  # type: ignore
            data['size'])
        self.rotation: Tuple[float, float, float] = tuple(  # type: ignore
            data['rotation'])


class ImportBone:
    '''Represents minecraft bone during import operation.'''
    def __init__(self, data: Dict):
        '''
        Creates ImportBone object created from a dictinary (part of the JSON)
        file in the model.

        # Arguments:
        - `data: Dict` - the part of the Minecraft model JSON file that represents
        the bone.
        '''
        self.blend_empty: Optional[bpy_types.Object] = None

        # Locators
        locators: List[ImportLocator] = []
        if 'locators' in data:
            for k, v in data['locators'].items():
                locators.append(ImportLocator(k, tuple(v)))  # type: ignore
        # Cubes
        import_cubes: List[ImportCube] = []
        for cube in data['cubes']:
            import_cubes.append(ImportCube(cube))

        self.name: str = data['name']
        self.parent = None if 'parent' not in data else data['parent']
        self.cubes = import_cubes
        self.locators = locators
        self.pivot: Tuple[float, float, float] = tuple(  # type: ignore
            data['pivot'])
        self.rotation: Tuple[float, float, float] = tuple(  # type: ignore
            data['rotation'])


class ImportGeometry:
    '''Represents whole minecraft geometry during import operation.'''
    def __init__(
            self, data: Dict, geometry_name: str = ""):
        '''
        The data dict is a dictionary representaiton of the JSON file with
        Minecraft model.

        geometry_name is a name of the geometry to load. This argument is
        optional if not specified or epmty string only the first model is
        imported.

        # Arguments:
        - `data: Dict` - a dictionary with a valid Minecraft model file (can
        have multiple geometries).
        - `geometry_name: str` - a name of the geometry to import.
        '''
        # Validate the input data
        _assert_is_model_file(data)

        # format_version: str = data['format_version']
        geometries: List = data['minecraft:geometry']
        geometry, geometry_name = self._load_geometry(
            geometries, geometry_name)
        texture_width, texture_height = self._load_dimensions(geometry)
        import_bones = self._load_bones(geometry)

        # Set the values
        self.identifier = geometry_name
        self.texture_width = texture_width
        self.texture_height = texture_height
        self.bones = import_bones

    def _load_geometry(
            self, geometries: List, geometry_name: str) -> Tuple[Dict, str]:
        # Find geometry
        geometry: Optional[Dict] = None
        for curr_geometry in geometries:
            try:
                identifier = get_path(curr_geometry, ['description', 'identifier'])
            except InvalidDictPathException:
                continue

            # Found THE geometry
            if geometry_name == "" or f'geometry.{geometry_name}' == identifier:
                identifier = cast(str, identifier)  # mypy cast
                geometry_name = identifier
                geometry = curr_geometry
                break

        # Geometry not found
        if geometry is None:
            if geometry_name == "":
                raise ValueError('Unable to find valid geometry')
            raise ValueError(
                f'Unable to find geometry called geometry.{geometry_name}'
            )
        return geometry, geometry_name

    def _load_dimensions(
            self, geometry: Dict) -> Tuple[int, int]:
        # Load texture_width
        try:
            texture_width: int = int(
                get_path(  # type: ignore
                    geometry, ['description', 'texture_width']
                )
            )
        except (InvalidDictPathException, ValueError):
            # TODO - give user some kind of warning if this happens
            # there is clearly something wrong about the model that doesn't
            # define the texture width
            texture_width = 100

        # Load texture_height
        try:
            texture_height: int = int(
                get_path(  # type: ignore
                    geometry, ['description', 'texture_height']
                )
            )
        except (InvalidDictPathException, ValueError):
            # TODO - give user some kind of warning if this happens
            # there is clearly something wrong about the model that doesn't
            # define the texture width
            texture_height = 100
        return texture_width, texture_height

    def _load_bones(self, geometry: Dict) -> Dict[str, ImportBone]:
        # Load bones from geometry
        bones: List = geometry['bones']

        # Read bones
        import_bones: Dict[str, ImportBone] = {}
        for bone in bones:
            import_bone = ImportBone(bone)
            import_bones[import_bone.name] = import_bone
        return import_bones

    def build(
            self, context: bpy_types.Context):
        '''
        Builds the geometry in Blender based on ImportGeometry object.

        # Arguments:
        `context: bpy_types.Context` - the context of running the operator.
        '''
        # context.view_layer.update()
        # Create objects - and set their pivots
        for bone in self.bones.values():
            # 1. Spawn bone (empty)
            bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
            bone_obj: bpy_types.Object
            bone_obj = bone.blend_empty = context.object
            _mc_pivot(bone_obj, bone.pivot)  # 2. Apply translation
            bone_obj.name = bone.name  # 3. Apply custom properties
            bone_obj['mc_is_bone'] = {}
            for cube in bone.cubes:
                cube_obj: bpy_types.Object
                # 1. Spawn cube
                bpy.ops.mesh.primitive_cube_add(
                    size=1, enter_editmode=False, location=(0, 0, 0)
                )
                cube_obj = cube.blend_cube = context.object

                _mc_set_size(cube_obj, cube.size)  # 3. Set size
                _mc_pivot(cube_obj, cube.pivot)  # 4. Move pivot
                # 2. Apply translation
                _mc_translate(cube_obj, cube.origin, cube.size, cube.pivot)
                # 5. Apply custom properties
                # cube_obj['mc_uv'] = list(cube.uv)  # TODO - map the UV
                if cube.mirror:
                    cube_obj['mc_mirror'] = {}
            for locator in bone.locators:
                # 1. Spawn locator (empty)
                locator_obj: bpy_types.Object
                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
                locator_obj = locator.blend_empty = context.object
                _mc_pivot(locator_obj, locator.position)  # 2. Apply translation
                # 3. Apply custom properties
                locator_obj.name = locator.name

        # Parent objects (keep offset)
        for bone in self.bones.values():
            bone_obj = bone.blend_empty
            # 1. Parent bone keep transform
            if bone.parent is not None and bone.parent in self.bones:
                parent_obj: bpy_types.Object = self.bones[
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
            # 3. Parent locators keep transform
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


def _mc_translate(
        obj: bpy_types.Object, mctranslation: Tuple[float, float, float],
        mcsize: Tuple[float, float, float],
        mcpivot: Tuple[float, float, float]
    ):
    '''
    Translates a blender object using a translation vector written in Minecraft
    coordinates system.

    # Arguments:
    - `obj: bpy_types.Object` - blender object to transform..
    - `mctranslation: Tuple[float, float, float]` - minecraft translation.
    - `mcsize: Tuple[float, float, float]` - minecraft size.
    - `mcpivot: Tuple[float, float, float]` - minecraft pivot.
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


def _mc_set_size(obj: bpy_types.Object, mcsize: Tuple[float, float, float]):
    '''
    Scales a blender object using scale vector written in minecraft coordinates
    system.

    # Arguments:
    - `obj: bpy_types.Object` - Blender object
    - `mcsize: Tuple[float, float, float]` - Minecraft object size.
    '''
    pos_delta = (
        (np.array(mcsize)[[0, 2, 1]] / 2) / MINECRAFT_SCALE_FACTOR
    )
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


def _mc_pivot(obj: bpy_types.Object, mcpivot: Tuple[float, float, float]):
    '''
    Moves a pivot of an blender object using coordinates written in minecraft
    coordinates system.

    # Arguments:
    - `obj: bpy_types.Object` - Blender object
    - `mcpivot: Tuple[float, float, float]` - Minecraft object pivot point.
    '''
    translation = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    obj.location += translation


def _mc_rotate(
        obj: bpy_types.Object, mcrotation: Tuple[float, float, float]
    ):
    '''
    Rotates a blender object using minecraft coordinates system for rotation
    vector.

    # Arguments:
    - `obj: bpy_types.Object` - Blender object
    - `mcrotation: Tuple[float, float, float]` - Minecraft object rotation.
    '''
    rotation = mathutils.Euler(
        (np.array(mcrotation)[[0, 2, 1]] * np.array([1, 1, -1])) * math.pi/180,
        'XZY'
    )
    obj.rotation_euler.rotate(rotation)
