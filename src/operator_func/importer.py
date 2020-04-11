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


class ImportLocator(object):
    def __init__(self, name: str, position: tp.Tuple[float, float, float]):
        self.name = name
        self.position = position

        self.blend_empty: tp.Optional[bpy_types.Empty] = None


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

        self.blend_empty: tp.Optional[bpy_types.Empty] = None


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

    # Create objects
    for bone in geometry.bones.values():
        # 1. Spawn bone (empty)
        bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
        obj = bone.blend_empty = context.object
        # 2. Apply translation
        _mc_pivot(obj, bone.pivot)
        # 3. Apply rotation
        _mc_rotate(obj, bone.rotation)
        context.view_layer.update()
    #     # 4. Apply custom properties
    #     obj.name = bone.name
    #     # 5. Spawn cubes
    #     for cube in bone.cubes:
    #         # 1. Spawn cube
    #         bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, location=(0, 0, 0))
    #         obj = cube.blend_cube = context.object

    #         # 2. Apply translation
    #         _mc_translate(obj, cube.origin, cube.pivot)
    #         # 3. Apply scale
    #         _mc_scale(obj, cube.size)
    #         # 4. Move pivot
    #         _mc_pivot(obj, cube.pivot)
    #         # 5. Rotate around the pivot
    #         _mc_rotate(obj, cube.rotation)
    #         context.view_layer.update()
    #         # 6. Apply custom properties
    #         obj['mc_uv'] = list(cube.uv)
    #         if cube.mirror:
    #             obj['mc_mirror'] = {}

    #     for locator in bone.locators:
    #         # 1. Spawn locator (empty)
    #         bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
    #         obj = locator.blend_empty = context.object
    #         # 2. Apply translation
    #         _mc_pivot(obj, locator.position)

    # # Add parenting (and apply parent transformations)
    # for bone in geometry.bones.values():
    #     # If there is parent set it (don't keep transform)
    #     if bone.parent is not None and bone.parent in geometry.bones:
    #         bone.blend_empty.parent = geometry.bones[  # type: ignore
    #             bone.parent
    #         ].blend_empty
    #     for cube in bone.cubes:
    #         # Set bone as parent (keep transform)
    #         cube.blend_cube.parent = bone.blend_empty  # type: ignore
    #     for locator in bone.locators:
    #         # Set the bone as parent
    #         locator.blend_empty.parent = bone.blend_empty  # type: ignore


def _mc_translate(
    obj: bpy_types.Object, mctranslation: tp.Tuple[float, float, float],
    mcpivot: tp.Tuple[float, float, float]
):
    '''
    Translates a blender object using a translation vector written in minecraft
    coordinates system.
    '''
    # translation = mathutils.Vector(
        
    #     (
    #         np.array(mctranslation)[[0, 2, 1]] * np.array([1, 1, 1])
    #     ) /
    #     MINECRAFT_SCALE_FACTOR
    # )
    # for vertex in obj.data.vertices:
    #     vertex.co -= translation


def _mc_scale(
    obj: bpy_types.Object, mcscale: tp.Tuple[float, float, float]
):
    '''
    Scales a blender object using scale vector written in minecraft coordinates
    system.
    '''
    obj.scale = mathutils.Vector(
        (
            (np.array(mcscale)[[0, 2, 1]] * np.array([1, -1, 1])) *
            np.array(obj.scale) / MINECRAFT_SCALE_FACTOR
        )
    )


def _mc_pivot(
    obj: bpy_types.Object, mcpivot: tp.Tuple[float, float, float]
):
    '''
    Moves a pivot of an blender object using coordinates written in minecraft
    coordinates system.
    '''
    translation = mathutils.Vector(
        np.array(mcpivot)[[0, 2, 1]] * np.array([1, 1, 1]) /
        MINECRAFT_SCALE_FACTOR
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
        (np.array(mcrotation)[[0, 2, 1]] * np.array([1, -1, 1])) * math.pi/180,
        'XYZ'
    )
    obj.rotation_euler.rotate(rotation)