import bpy
import numpy as np

# Additional imports for mypy
import bpy_types
import typing as tp

from .common import (
    MINECRAFT_SCALE_FACTOR, get_mcrotation, get_mcpivot, get_local_matrix,
    get_mcube_size, get_vect_json, get_mccube_position,
    get_object_mcproperties, MCObjType, ObjectId, ObjectMcProperties
)


def get_mcmodel_json(
    model_name: str, mc_bones: tp.List[tp.Dict],
    texture_width: int, texture_height: int
) -> tp.Dict:
    '''
    Returns the dictionary that represents JSON file for exporting the model
    '''
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.{model_name}",
                    "texture_width": texture_width,
                    "texture_height": texture_height,
                    "visible_bounds_width": 10,
                    "visible_bounds_height": 10,
                    "visible_bounds_offset": [0, 2, 0]
                },
                "bones": mc_bones
            }
        ]
    }


def get_mcbone_json(
    boneprop: ObjectMcProperties, cubeprops: tp.List[ObjectMcProperties],
    locatorprops: tp.List[ObjectMcProperties],
    object_properties: tp.Dict[ObjectId, ObjectMcProperties]
) -> tp.Dict:
    '''
    - boneprop - the main object that represents the bone.
    - cubeprops - the list of objects that represent the cubes that belong to
      the bone. If the "boneprop" is one of the cubes it should be included on
      the list.
    - locatorprops - the list of objects that represent the locators that
      belong to the bone.
    - object_properties - the properties of all of the mccubes and mcbones in
      minecraft model.

    Returns the dictionary that represents a single mcbone in json file
    of model.
    '''
    def _scale(objprop: ObjectMcProperties) -> np.ndarray:
        '''Scale of a bone'''
        _, _, scale = objprop.matrix_world().decompose()
        return np.array(scale.xzy)

    # Set basic bone properties
    mcbone: tp.Dict = {'name': boneprop.name(), 'cubes': []}
    if boneprop.mcparent is not None:
        mcbone['parent'] = object_properties[boneprop.mcparent].name()
        b_rot = get_mcrotation(
            boneprop.matrix_world(),
            object_properties[boneprop.mcparent].matrix_world()
        )
    else:
        b_rot = get_mcrotation(boneprop.matrix_world())
    b_pivot = get_mcpivot(boneprop, object_properties) * MINECRAFT_SCALE_FACTOR
    mcbone['pivot'] = get_vect_json(b_pivot)
    mcbone['rotation'] = get_vect_json(b_rot)

    # Set locators
    if len(locatorprops) > 0:
        mcbone['locators'] = {}
    for locatorprop in locatorprops:
        translation = get_local_matrix(
            boneprop.matrix_world(), locatorprop.matrix_world()
        )
        _l_scale = _scale(locatorprop)
        l_pivot = get_mcpivot(
            locatorprop, object_properties
        ) * MINECRAFT_SCALE_FACTOR
        l_origin = l_pivot + (
            get_mccube_position(locatorprop, translation) *
            _l_scale * MINECRAFT_SCALE_FACTOR
        )
        mcbone['locators'][locatorprop.name()] = get_vect_json(l_origin)

    # Set cubes
    for cubeprop in cubeprops:
        translation = get_local_matrix(
            boneprop.matrix_world(), cubeprop.matrix_world()
        )
        _c_scale = _scale(cubeprop)
        c_size = get_mcube_size(
            cubeprop
        ) * _c_scale * MINECRAFT_SCALE_FACTOR
        c_pivot = get_mcpivot(
            cubeprop, object_properties
        ) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            get_mccube_position(cubeprop, translation) * _c_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_rot = get_mcrotation(
            cubeprop.matrix_world(), boneprop.matrix_world()
        )

        if cubeprop.has_uv():
            uv = cubeprop.get_mc_uv()
        else:
            uv = (0, 0)

        if cubeprop.has_mc_inflate():
            c_size = c_size - cubeprop.get_mc_inflate()*2
            c_origin = c_origin + cubeprop.get_mc_inflate()

        cube_dict: tp.Dict = {
            'uv': uv,
            # TODO - add rounding option in the menu
            'size': [round(i) for i in get_vect_json(c_size)],
            'origin': get_vect_json(c_origin),
            'pivot': get_vect_json(c_pivot),
            'rotation': get_vect_json(c_rot)
        }

        if cubeprop.has_mc_inflate():
            cube_dict['inflate'] = cubeprop.get_mc_inflate()

        if cubeprop.has_mc_mirror():
            cube_dict['mirror'] = True

        mcbone['cubes'].append(cube_dict)

    return mcbone
