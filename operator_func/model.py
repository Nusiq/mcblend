import bpy
import numpy as np

# Additional imports for mypy
import bpy_types
import typing as tp

from .common import (
    MINECRAFT_SCALE_FACTOR, get_mcrotation, get_mcpivot, get_local_matrix,
    get_mcube_size, get_vect_json, get_mccube_position
)


def get_mcmodel_json(model_name: str, mc_bones: tp.List[tp.Dict]) -> tp.Dict:
    '''
    Returns the dictionary that represents JSON file for exporting the model
    '''
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.{model_name}",
                    "texture_width": 1,
                    "texture_height": 1,
                    "visible_bounds_width": 10,
                    "visible_bounds_height": 10,
                    "visible_bounds_offset": [0, 2, 0]
                },
                "bones": mc_bones
            }
        ]
    }


def get_mcbone_json(
    bone: bpy_types.Object, cubes: tp.List[bpy_types.Object]
) -> tp.Dict:
    '''
    - bone - the main object that represents the bone.
    - cubes - the list of objects that represent the cubes that belong to
      the bone. If the "bone" is one of the cubes it should be included on the
      list.

    Returns the dictionary that represents a single mcbone in json file
    of exported model.
    '''
    def _scale(obj: bpy_types.Object) -> np.ndarray:
        '''Scale of a bone'''
        _, _, scale = obj.matrix_world.decompose()
        return np.array(scale.xzy)

    mcbone = {'name': bone.name, 'cubes': []}

    # Code
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name
        b_rot = get_mcrotation(bone.matrix_world, bone['mc_parent'].matrix_world)
    else:
        b_rot = get_mcrotation(bone.matrix_world)

    b_pivot = get_mcpivot(bone) * MINECRAFT_SCALE_FACTOR

    for cube in cubes:
        translation = get_local_matrix(
            bone.matrix_world, cube.matrix_world
        )

        _b_scale = _scale(cube)

        c_size = (
            get_mcube_size(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_pivot = get_mcpivot(cube) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            get_mccube_position(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_rot = get_mcrotation(cube.matrix_world, bone.matrix_world)

        mcbone['cubes'].append({
            'uv': [0, 0],
            'size': get_vect_json(c_size),
            'origin': get_vect_json(c_origin),
            'pivot': get_vect_json(c_pivot),
            'rotation': get_vect_json(c_rot)
        })

    mcbone['pivot'] = get_vect_json(b_pivot)
    mcbone['rotation'] = get_vect_json(b_rot)
    return mcbone
