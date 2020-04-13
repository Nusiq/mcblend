'''
Object representation of Minecraft model JSON files and data validation
'''
import typing as tp
from .json_tools import get_path
from .common import MINECRAFT_SCALE_FACTOR
import bpy_types
import mathutils
import bpy
import numpy as np
import math


def _assert(expr: bool, msg: str='') -> None:
    '''
    Same functionality as normal assert statement but works even
    if __debug__ is False.
    '''
    if not expr:
        raise AssertionError(msg)


def assert_is_vector(vect: tp. Any, length: int, types: tp.Tuple) -> None:
    '''
    Asserts that the "vect" is "length" long vector and all of the items
    in the vector are instances of types from types list.
    '''
    _assert(type(vect) is list)
    _assert(len(vect) == length)
    _assert(all([isinstance(i, types) for i in vect]))


def assert_is_model(a: tp.Any) -> None:
    '''
    Asserts that the input dictionary is a valid model file.
    '''
    _assert(type(a) is dict)
    _assert(set(a.keys()) == {'format_version', 'minecraft:geometry'})

    _assert(a['format_version'] == "1.12.0")

    geometries = a['minecraft:geometry']
    _assert(type(geometries) is list)
    _assert(len(geometries) > 0)
    
    # minecraft:geometry
    for geometry in geometries:
        _assert(type(geometry) is dict)
        _assert(set(geometry.keys()) == {'description', 'bones'})
        desc = geometry['description']
        bones = geometry['bones']

        # minecraft:geometry -> description
        _assert(type(desc) is dict)
        _assert(set(desc.keys()) == {'identifier', 'texture_width',
            'texture_height', 'visible_bounds_width', 'visible_bounds_height',
            'visible_bounds_offset'
        
        })
        _assert(type(desc['identifier']) is str)
        _assert(type(desc['texture_width']) is int)
        _assert(type(desc['texture_height']) is int)
        _assert(isinstance(desc['visible_bounds_width'], (float, int)))
        _assert(isinstance(desc['visible_bounds_height'], (float, int)))
        assert_is_vector(desc['visible_bounds_offset'], 3, (int, float))

        # minecraft:geometry -> bones
        _assert(type(bones) is list)
        for bone in bones:
            _assert(type(bone) is dict)

            _assert(set(bone.keys()) <= {  # acceptable keys
                'name', 'cubes', 'pivot', 'rotation', 'parent', 'locators'
            })
            _assert(set(bone.keys()) >= {  # obligatory keys
                'name', 'cubes', 'pivot', 'rotation'
            })
            _assert(type(bone['name']) is str)

            assert_is_vector(bone['pivot'], 3, (int, float))
            assert_is_vector(bone['rotation'], 3, (int, float))
            if 'parent' in bone:
                _assert(type(bone['parent']) is str)
            # minecraft:geometry -> bones -> locators
            if 'locators' in bone:
                _assert(type(bone['locators']) is dict)
                for locator_name, locator in bone['locators'].items():
                    _assert(type(locator_name) is str)
                    assert_is_vector(locator, 3, (int, float))
            # minecraft:geometry -> bones -> cubes
            _assert(type(bone['cubes']) is list)
            for cube in bone['cubes']:
                _assert(type(cube) is dict)
                _assert(set(cube.keys()) <= {  # acceptable keys
                    'uv', 'size', 'origin', 'pivot', 'rotation',
                    'mirror'
                })
                _assert(set(cube.keys()) >= {  # obligatory keys
                    'uv', 'size', 'origin', 'pivot', 'rotation'
                })
                assert_is_vector(cube['uv'], 2, (int, float))
                assert_is_vector(cube['size'], 3, (int, float))
                assert_is_vector(cube['origin'], 3, (int, float))
                assert_is_vector(cube['pivot'], 3, (int, float))
                assert_is_vector(cube['rotation'], 3, (int, float))
                if 'mirror' in cube:
                    _assert(type(cube['mirror']) is bool)


class ImportLocator(object):
    def __init__(self, name: str, position: tp.Tuple[float, float, float]):
        self.name = name
        self.position = position

        self.blend_empty: tp.Optional[bpy_types.Object] = None


class ImportCube(object):
    def __init__(
        self,
        uv: tp.Tuple[int, int],
        mirror: bool,
        origin: tp.Tuple[float, float, float],
        pivot: tp.Tuple[float, float, float],
        size: tp.Tuple[float, float, float],
        rotation: tp.Tuple[float, float, float]
    ):
        self.uv = uv
        self.mirror = mirror
        self.origin = origin
        self.size = size

        self.pivot = pivot
        self.rotation = rotation

        self.blend_cube: tp.Optional[bpy_types.Object] = None


class ImportBone(object):
    def __init__(
        self, name: str, parent: tp.Optional[str],
        pivot: tp.Tuple[float, float, float],
        rotation: tp.Tuple[float, float, float], cubes: tp.List[ImportCube],
        locators: tp.List[ImportLocator]
    ):
        self.name = name
        self.parent = parent
        self.cubes = cubes
        self.locators = locators

        self.pivot = pivot
        self.rotation = rotation

        self.blend_empty: tp.Optional[bpy_types.Object] = None


class ImportGeometry(object):
    def __init__(
        self, identifier: str, texture_width: int, texture_height: int,
        bones: tp.Dict[str, ImportBone]
    ):
        self.identifier = identifier
        self.texture_width = texture_width
        self.texture_height = texture_height
        self.bones = bones


def _load_cube(data: tp.Dict) -> ImportCube:
    '''
    Returns ImportCube object created from a dictinary (part of the JSON)
    file in the model.
    '''
    if type(data) is not dict:
        raise ValueError('invalid cube structure')
    # uv
    if 'uv' not in data:
        uv: tp.Tuple[int, int] = (0, 0)
    elif (
        type(data['uv']) is not list or
        len(data['uv']) != 2 or
        not all([isinstance(i, (int, float)) for i in data['uv']])
    ):
        raise ValueError('uv must be a list of two numbers')
    else:
        uv = data['uv']
    # mirror
    if 'mirror' not in data:
        mirror: bool = False
    elif type(data['mirror']) is not bool:
        raise ValueError('mirror property must be boolean')
    else:
        mirror = data['mirror']

    # size
    if 'size' not in data:
        size: tp.Tuple[float, float, float] = (0, 0, 0)
    elif (
        type(data['size']) is not list or
        len(data['size']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['size']])
    ):
        raise ValueError('size must be a list of 3 floats')
    else:
        size = tuple(data['size'])  # type: ignore

    # origin
    if 'origin' not in data:
        origin: tp.Tuple[float, float, float] = (0, 0, 0)
    elif (
        type(data['origin']) is not list or
        len(data['origin']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['origin']])
    ):
        raise ValueError('origin must be a list of 3 floats')
    else:
        origin = tuple(data['origin'])  # type: ignore

    # rotation
    if 'rotation' not in data:
        rotation: tp.Tuple[float, float, float] = (0, 0, 0)
    elif (
        type(data['rotation']) is not list or
        len(data['rotation']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['rotation']])
    ):
        raise ValueError('rotation must be a list of 3 floats')
    else:
        rotation = tuple(data['rotation'])  # type: ignore

    # pivot
    if 'pivot' not in data:
        pivot: tp.Tuple[float, float, float] = (0, 0, 0)
    elif (
        type(data['pivot']) is not list or
        len(data['pivot']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['pivot']])
    ):
        raise ValueError('pivot must be a list of 3 floats')
    else:
        pivot = tuple(data['pivot'])  # type: ignore
    return ImportCube(uv, mirror, origin, pivot, size, rotation)


def _load_bone(data: tp.Dict) -> ImportBone:
    '''
    Returns ImportBone object created from a dictinary (part of the JSON)
    file in the model.
    '''
    if type(data) is not dict:
        raise ValueError('Invalid bone structure')

    # Name
    if 'name' not in data:
        raise ValueError('Missing bone name')
    elif type(data['name']) is not str:
        raise ValueError('Bone name must be a string')
    else:
        name: str = data['name']
    # Pivot
    if 'pivot' not in data:
        pivot: tp.Tuple[float, float, float] = (0, 0, 0)
    elif type(data['pivot']) is not list:
        raise ValueError('Invalid pivot property structure')
    elif (
        len(data['pivot']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['pivot']])
    ):
        raise ValueError('pivot property must be a list of 3 numbers')
    else:
        pivot = tuple(data['pivot'])  # type: ignore

    # Roatation
    if 'rotation' not in data:
        rotation: tp.Tuple[float, float, float] = (0, 0, 0)
    elif type(data['rotation']) is not list:
        raise ValueError('Invalid rotation property structure')
    elif (
        len(data['rotation']) != 3 or
        not all([isinstance(i, (float, int)) for i in data['rotation']])
    ):
        raise ValueError('rotation property must be a list of 3 numbers')
    else:
        rotation = tuple(data['rotation'])  # type: ignore
    # Parent
    if 'parent' not in data:
        parent = None
    elif type(data['parent']) is not str:
        raise ValueError('parent value must be a string')
    else:
        parent = data['parent']


    # Locators
    locators: tp.List[ImportLocator] = []
    if 'locators' not in data:
        pass
    elif type(data['locators']) is not dict:
        raise ValueError('Invalid locators property structure')
    else:
        for k, v in data['locators'].items():
            if type(k) is not str:
                raise ValueError('Locator name must be a string')
            elif (
                type(v) is not list or
                len(v) != 3 or
                not all([isinstance(i, (float, int)) for i in v])
            ):
                raise ValueError(
                    'Locator coordinates must be a list of 3 numbers'
                )
            else:
                locators.append(ImportLocator(
                    k,
                    tuple(v))  # type: ignore
                )
    # Cubes
    import_cubes: tp.List[ImportCube] = []
    if 'cubes' not in data:
        pass
    elif type(data['cubes']) is not list:
        raise ValueError('Invalid cubes property structure')
    else:
        for i, c in enumerate(data['cubes']):
            if type(c) is not dict:
                raise ValueError(f'Cube "{i}" of is invalid')
            try:
                import_cubes.append(_load_cube(c))
            except ValueError as e:
                raise ValueError(
                    f'cube {i} - {e}'
                )

    return ImportBone(
        name, parent, pivot, rotation, import_cubes, locators
    )


def load_model(data: tp.Dict, geometry_name: str="") -> ImportGeometry:
    '''
    Returns ImportGeometry object with all of the data loaded from data dict.
    The data dict is a dictionary representaiton of the JSON file with
    Minecraft model. Raises ValueError if data is invalid.

    geometry_name is a name of the geometry to load. This argument is optional
    if not specified or epmty string only the first model is imported.
    '''
    # Format version
    if type(data) is not dict:
        raise ValueError(f'Invalid model structure')

    if 'format_version' not in data:
        raise ValueError(f'Missing format_version')
    elif data['format_version'] != "1.12.0":
        raise ValueError(f'Unsuported version {data["format_version"]}')
    else:
        format_version: str = data['format_version']

    # Geometry
    if 'minecraft:geometry' not in data:
        raise ValueError('Missing minecraft:geometry property')
    elif type(data['minecraft:geometry']) is not list:
        raise ValueError('Property minecraft:geometry must be a list')
    elif len(data['minecraft:geometry']) == 0:
        raise ValueError('minecraft:geometry is empty')
    else:
        geometries: tp.List = data['minecraft:geometry']

    # Find geometry
    geometry: tp.Optional[tp.Dict] = None
    for g in geometries:
        identifier, success = get_path(g, ['description', 'identifier'])
        if not success:
            continue
        # Found THE geometry
        if geometry_name == "" or geometry_name == identifier:
            identifier = tp.cast(str, identifier)  # mypy cast
            geometry_name = identifier
            geometry = g
            break

    # Geometry not found
    if geometry is None:
        if geometry_name == "":
            raise ValueError('Unable to find valid geometry')
        else:
            raise ValueError(f'Unable to find geometry called {geometry_name}')

    # Load texture_width
    texture_width, success = get_path(
        geometry, ['description', 'texture_width']
    )
    if not success:
        texture_width = 0
    elif type(texture_width) is not int or texture_width < 0:  # type: ignore
        raise ValueError('texture_width property must be an positive integer')
    # Load texture_height
    texture_height, success = get_path(
        geometry, ['description', 'texture_height']
    )
    if not success:
        texture_height = 0
    elif (
        type(texture_height) is not int or texture_height < 0  # type: ignore
    ):
        raise ValueError('texture_height property must be an positive integer')

    # Load bones from geometry
    if 'bones' not in geometry:
        bones: tp.List = []
    elif type(geometry['bones']) is not list:
        raise ValueError('The bones property of the geometry must be a list')
    else:
        bones: tp.List = geometry['bones']  # type: ignore

    # Read bones
    import_bones: tp.Dict[str, ImportBone] = {}
    for i, b in enumerate(bones):
        if type(b) is not dict:
            raise ValueError(
                f'Bone "{i}" of geometry "{identifier}" is invalid'
            )
        try:
            import_bone = _load_bone(b)
            import_bones[import_bone.name] = import_bone
        except ValueError as e:
            raise ValueError(
                f'Error in bone {i} of geometry {identifier}: {e}'
            )
    return ImportGeometry(
        geometry_name,
        texture_width,  # type: ignore
        texture_height,  # type: ignore
        import_bones
    )


def build_geometry(geometry: ImportGeometry, context: bpy_types.Context):
    '''Builds the geometry in Blenders 3D space'''
    # context.view_layer.update()
    # Create objects - and set their pivots
    for bone in geometry.bones.values():
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
            cube_obj['mc_uv'] = list(cube.uv)
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
    for bone in geometry.bones.values():
        bone_obj = bone.blend_empty
        # 1. Parent bone keep transform
        if bone.parent is not None and bone.parent in geometry.bones:
            parent_obj: bpy_types.Object = geometry.bones[
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
    for bone in geometry.bones.values():
        bone_obj = bone.blend_empty
        context.view_layer.update()
        _mc_rotate(bone_obj, bone.rotation)
        for cube in bone.cubes:
            cube_obj = cube.blend_cube
            _mc_rotate(cube_obj, cube.rotation)


def _mc_translate(
    obj: bpy_types.Object, mctranslation: tp.Tuple[float, float, float],
    mcsize: tp.Tuple[float, float, float],
    mcpivot: tp.Tuple[float, float, float]
):
    '''
    Translates a blender object using a translation vector written in minecraft
    coordinates system.
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
    obj: bpy_types.Object, mcsize: tp.Tuple[float, float, float]
):
    '''
    Scales a blender object using scale vector written in minecraft coordinates
    system.
    '''
    pos_delta = (
        (np.array(mcsize)[[0, 2, 1]] / 2) / MINECRAFT_SCALE_FACTOR
    )
    data = obj.data
    # 0. ---; 1. --+; 2. -+-; 3. -++; 4. +--; 5. +-+; 6. ++- 7. +++
    data.vertices[0].co = mathutils.Vector(pos_delta * np.array([-1, -1,-1]))
    data.vertices[1].co = mathutils.Vector(pos_delta * np.array([-1, -1, 1]))
    data.vertices[2].co = mathutils.Vector(pos_delta * np.array([-1, 1, -1]))
    data.vertices[3].co = mathutils.Vector(pos_delta * np.array([-1, 1, 1]))
    data.vertices[4].co = mathutils.Vector(pos_delta * np.array([1, -1, -1]))
    data.vertices[5].co = mathutils.Vector(pos_delta * np.array([1, -1, 1]))
    data.vertices[6].co = mathutils.Vector(pos_delta * np.array([1, 1, -1]))
    data.vertices[7].co = mathutils.Vector(pos_delta * np.array([1, 1, 1]))



def _mc_pivot(
    obj: bpy_types.Object, mcpivot: tp.Tuple[float, float, float]
):
    '''
    Moves a pivot of an blender object using coordinates written in minecraft
    coordinates system.
    '''
    translation = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] / MINECRAFT_SCALE_FACTOR
    )
    obj.location += translation


def _mc_rotate(
    obj: bpy_types.Object, mcrotation: tp.Tuple[float, float, float]
):
    '''
    Rotates a blender object using minecraft coordinates system for rotation
    vector.
    '''
    rotation = mathutils.Euler(
        (np.array(mcrotation)[[0, 2, 1]] * np.array([1, 1, -1])) * math.pi/180,
        'XZY'
    )
    obj.rotation_euler.rotate(rotation)