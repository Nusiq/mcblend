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


def assert_is_vector(
    vect: tp. Any, length: int, types: tp.Tuple, msg: str=''
) -> None:
    '''
    Asserts that the "vect" is "length" long vector and all of the items
    in the vector are instances of types from types list.
    '''
    _assert(type(vect) is list, msg)
    _assert(len(vect) == length, msg)
    _assert(all([isinstance(i, types) for i in vect]), msg)


def assert_is_model(a: tp.Any) -> None:
    '''
    Asserts that the input dictionary is a valid model file.
    '''
    _assert(type(a) is dict, 'Model file must be an object')
    _assert(
        set(a.keys()) == {'format_version', 'minecraft:geometry'},
        'Model file must have format_version and minecraft:geometry properties'
    )

    _assert(a['format_version'] == "1.12.0", 'Unsuported format version')

    geometries = a['minecraft:geometry']
    _assert(
        type(geometries) is list,
        'minecraft:geometry property must be a list'
    )
    _assert(
        len(geometries) > 0, 'minecraft:geometry must have at least one item'
    )

    # minecraft:geometry
    for geometry in geometries:
        _assert(
            type(geometry) is dict,
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
        _assert(type(desc) is dict, 'Geometry description must be an object')
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
            type(desc['identifier']) is str,
            'Geometry identifier must be a string'
        )
        _assert(
            type(desc['texture_width']) is int,
            'texture_width must be an integer'
        )
        _assert(
            type(desc['texture_height']) is int,
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
        assert_is_vector(
            desc['visible_bounds_offset'], 3, (int, float),
            'visible_bounds_offset must be a vector of 3 numbers'
        )

        # minecraft:geometry -> bones
        _assert(type(bones) is list)
        for bone in bones:
            _assert(type(bone) is dict, 'Every bone must be an object')

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
            _assert(type(bone['name']) is str, 'Bone name must be a string')

            assert_is_vector(
                bone['pivot'], 3, (int, float),
                'pivot property of a bone must be a vector of 3 numbers'
            )
            assert_is_vector(
                bone['rotation'], 3, (int, float),
                'rotation property of a bone must be a vector of 3 numbers'
            )
            if 'parent' in bone:
                _assert(type(bone['parent']) is str,
                'parent property of a bone must be a string'
            )
            # minecraft:geometry -> bones -> locators
            if 'locators' in bone:
                _assert(
                    type(bone['locators']) is dict,
                    'locators property of a bone must be an object'
                )
                for locator_name, locator in bone['locators'].items():
                    _assert(
                        type(locator_name) is str,
                        'Locator name property must be a string'
                    )
                    assert_is_vector(
                        locator, 3, (int, float),
                        'Locator value must be a vector of 3 numbers'
                    )
            # minecraft:geometry -> bones -> cubes
            _assert(
                type(bone['cubes']) is list,
                'cubes property of a bone must be a list'
            )
            for cube in bone['cubes']:
                _assert(type(cube) is dict, 'Every cube must be an object')
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
                assert_is_vector(
                    cube['uv'], 2, (int, float),
                    'size property of a cube must be a vector of 2 numbers'
                )
                assert_is_vector(
                    cube['size'], 3, (int, float),
                    'size property of a cube must be a vector of 3 numbers'
                )
                assert_is_vector(
                    cube['origin'], 3, (int, float),
                    'origin property of a cube must be a vector of 3 numbers'
                )
                assert_is_vector(
                    cube['pivot'], 3, (int, float),
                    'pivot property of a cube must be a vector of 3 numbers'
                )
                assert_is_vector(
                    cube['rotation'], 3, (int, float),
                    'rotation property of a cube must be a vector of 3 numbers'
                )
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
    # uv
    uv: tp.Tuple[int, int] = data['uv']
    # mirror
    if 'mirror' not in data:
        mirror: bool = False
    else:
        mirror = data['mirror']

    # size
    size: tp.Tuple[float, float, float] = tuple(data['size'])  # type: ignore

    # origin
    origin: tp.Tuple[float, float, float] = tuple(  # type: ignore
        data['origin']
    )

    # rotation
    rotation: tp.Tuple[float, float, float] = tuple(  # type: ignore
        data['rotation']
    )

    # pivot
    pivot: tp.Tuple[float, float, float] = tuple(data['pivot'])  # type: ignore
    return ImportCube(uv, mirror, origin, pivot, size, rotation)


def _load_bone(data: tp.Dict) -> ImportBone:
    '''
    Returns ImportBone object created from a dictinary (part of the JSON)
    file in the model.
    '''

    name: str = data['name']
    # Pivot
    pivot: tp.Tuple[float, float, float] = tuple(data['pivot'])  # type: ignore

    # Roatation
    rotation: tp.Tuple[float, float, float] = tuple(  # type: ignore
        data['rotation']
    )
    # Parent
    if 'parent' not in data:
        parent = None
    else:
        parent = data['parent']


    # Locators
    locators: tp.List[ImportLocator] = []
    if 'locators' not in data:
        pass
    else:
        for k, v in data['locators'].items():
            locators.append(ImportLocator(
                k,
                tuple(v))  # type: ignore
            )
    # Cubes
    import_cubes: tp.List[ImportCube] = []
    for i, c in enumerate(data['cubes']):
        import_cubes.append(_load_cube(c))

    return ImportBone(
        name, parent, pivot, rotation, import_cubes, locators
    )


def load_model(data: tp.Dict, geometry_name: str="") -> ImportGeometry:
    '''
    Returns ImportGeometry object with all of the data loaded from data dict.
    The data dict is a dictionary representaiton of the JSON file with
    Minecraft model. Doesn't validates the input. Use assert_is_model for that.

    geometry_name is a name of the geometry to load. This argument is optional
    if not specified or epmty string only the first model is imported.
    '''
    format_version: str = data['format_version']
    geometries: tp.List = data['minecraft:geometry']

    # Find geometry
    geometry: tp.Optional[tp.Dict] = None
    for g in geometries:
        identifier, success = get_path(g, ['description', 'identifier'])
        if not success:
            continue
        # Found THE geometry
        if geometry_name == "" or f'geometry.{geometry_name}' == identifier:
            identifier = tp.cast(str, identifier)  # mypy cast
            geometry_name = identifier
            geometry = g
            break

    # Geometry not found
    if geometry is None:
        if geometry_name == "":
            raise ValueError('Unable to find valid geometry')
        else:
            raise ValueError(
                f'Unable to find geometry called geometry.{geometry_name}'
            )

    # Load texture_width
    texture_width, success = get_path(
        geometry, ['description', 'texture_width']
    )
    texture_width = tp.cast(int, texture_width)

    # Load texture_height
    texture_height, success = get_path(
        geometry, ['description', 'texture_height']
    )
    texture_height = tp.cast(int, texture_height)

    # Load bones from geometry
    bones: tp.List = geometry['bones']

    # Read bones
    import_bones: tp.Dict[str, ImportBone] = {}
    for i, b in enumerate(bones):
        import_bone = _load_bone(b)
        import_bones[import_bone.name] = import_bone

    return ImportGeometry(
        geometry_name,
        texture_width,
        texture_height,
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