import bpy
import mathutils
import math
import numpy as np
from enum import Enum

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp

from .uv import get_uv_mc_cubes, UvMcCube, plan_uv, set_cube_uv
from .animation import (
    get_mcanimation_json, get_mctranslations, get_next_keyframe,
    get_transformations
)
from .model import get_mcbone_json, get_mcmodel_json
from .common import (
    MCObjType, get_object_mcproperties, get_vect_json, pick_closest_rotation,
    ObjectId, ObjectMcProperties, get_name_conflicts, MINECRAFT_SCALE_FACTOR
)
from .importer import load_model, build_geometry, assert_is_model


def export_model(context: bpy_types.Context) -> tp.Tuple[tp.Dict, str]:
    '''
    Uses context.selected_objects to create and return dictionary with
    minecraft model.

    Additionally returns a string with error message or an empty string when
    there are no errors.
    '''
    object_properties = get_object_mcproperties(context)
    name_conflict = get_name_conflicts(object_properties)
    if name_conflict != '':
        return (
            {}, f'Name conflict "{name_conflict}". Please rename theobject."'
        )

    # Save starting frame
    start_frame = context.scene.frame_current
    # Stop animation if running & jump to the frame 0
    bpy.ops.screen.animation_cancel()
    context.scene.frame_set(0)

    texture_width = context.scene.nusiq_mcblend.texture_width
    texture_height = context.scene.nusiq_mcblend.texture_height
    model_name = context.scene.nusiq_mcblend.model_name
    mc_bones: tp.List[tp.Dict] = []

    for objid, objprop in object_properties.items():
        if (objprop.mctype in [MCObjType.BONE, MCObjType.BOTH]):
            # Create cubes and locators list
            cubes: tp.List[ObjectMcProperties] = []
            if objprop.mctype == MCObjType.BOTH:  # Else MCObjType == BOTH
                cubes = [objprop]
            locators: tp.List[ObjectMcProperties] = []
            # Add children cubes if they are MCObjType.CUBE type
            for child_id in objprop.mcchildren:
                if child_id in object_properties:
                    if object_properties[child_id].mctype == MCObjType.CUBE:
                        cubes.append(object_properties[child_id])
                    elif (
                        object_properties[child_id].mctype == MCObjType.LOCATOR
                    ):
                        locators.append(object_properties[child_id])

            mcbone = get_mcbone_json(
                objprop, cubes, locators, object_properties
            )
            mc_bones.append(mcbone)

    # Return to first frame and create the result
    context.scene.frame_set(start_frame)
    result = get_mcmodel_json(
        model_name, mc_bones, texture_width, texture_height
    )
    return result, ''


def export_animation(
    context: bpy_types.Context, old_dict: tp.Optional[tp.Dict]
) -> tp.Tuple[tp.Dict, str]:
    '''
    Uses context.selected_objects to create and return dictionary with
    minecraft animation.
    old_dict is an optional value with dictionary that contains the content of
    animation file. This function validates the dictionary and tries to use it
    while exporting the animation.
    '''
    # Check and create object properties
    object_properties = get_object_mcproperties(context)
    name_conflict = get_name_conflicts(object_properties)
    if name_conflict != '':
        return (
            {}, f'Name conflict "{name_conflict}". Please rename theobject."'
        )

    # Save starting frame
    start_frame = context.scene.frame_current
    # Stop animation if running & jump to the frame 0
    bpy.ops.screen.animation_cancel()
    context.scene.frame_set(0)

    # Dictionary that stores bone data
    bone_data: tp.Dict[ObjectId, tp.Dict[str, tp.List[tp.Dict]]] = (
        defaultdict(lambda: {
            'scale': [], 'rotation': [], 'position': []
        })
    )

    # Read data from frames
    default_translation = get_transformations(object_properties)
    prev_rotation = {
        name:np.zeros(3) for name in default_translation.keys()
    }
    next_keyframe = get_next_keyframe(context)
    while next_keyframe is not None:
        context.scene.frame_set(math.ceil(next_keyframe))
        current_translations = get_transformations(object_properties)
        for d_key, d_val in default_translation.items():
            # Get the difference from original
            loc, rot, scale = get_mctranslations(
                d_val.rotation, current_translations[d_key].rotation,
                d_val.scale, current_translations[d_key].scale,
                d_val.location, current_translations[d_key].location
            )
            time = str(round(
                (context.scene.frame_current-1) / context.scene.render.fps,
                4
            ))
            
            bone_data[d_key]['position'].append({
                'time': time,
                'value': get_vect_json(loc)
            })
            rot = pick_closest_rotation(
                rot, prev_rotation[d_key], d_val.rotation
            )
            bone_data[d_key]['rotation'].append({
                'time': time,
                'value': get_vect_json(rot)
            })
            bone_data[d_key]['scale'].append({
                'time': time,
                'value': get_vect_json(scale)
            })

            prev_rotation[d_key] = rot  # Save previous rotation

        next_keyframe = get_next_keyframe(context)

    # Return to first frame and create the result
    context.scene.frame_set(start_frame)
    animation_dict = get_mcanimation_json(
        name=context.scene.nusiq_mcblend.animation_name,
        length=(context.scene.frame_end-1)/context.scene.render.fps,
        loop_animation=context.scene.nusiq_mcblend.loop_animation,
        anim_time_update=context.scene.nusiq_mcblend.anim_time_update,
        bone_data=bone_data, object_properties=object_properties,
        extend_json=old_dict
    )

    return animation_dict, ''


def set_uvs(context: bpy_types.Context) -> bool:
    width = context.scene.nusiq_mcblend.texture_width
    height = context.scene.nusiq_mcblend.texture_height
    move_blender_uvs = context.scene.nusiq_mcblend.move_blender_uvs
    move_existing_mappings = context.scene.nusiq_mcblend.move_existing_mappings
    remove_old_mappings = context.scene.nusiq_mcblend.remove_old_mappings
    resolution = context.scene.nusiq_mcblend.texture_template_resolution

    # Save starting frame
    start_frame = context.scene.frame_current
    # Stop animation if running & jump to the frame 0
    bpy.ops.screen.animation_cancel()
    context.scene.frame_set(0)

    object_properties = get_object_mcproperties(context)
    objprops = [
        o for o in object_properties.values()
        if o.type() == 'MESH'
    ]

    uv_dict: tp.Dict[str, UvMcCube] = get_uv_mc_cubes(
        objprops, read_existing_uvs=not move_existing_mappings
    )
    uv_mc_cubes = [i for i in uv_dict.values()]
    if height <= 0:
        height = None

    map_result = plan_uv(uv_mc_cubes, width, height)
    if map_result is False:
        return False

    if remove_old_mappings:
        for objprop in objprops:
            objprop.clear_uv_layers()

    for objprop in objprops:
        if objprop.name() in uv_dict:
            curr_uv = uv_dict[objprop.name()]
            objprop.set_mc_uv((curr_uv.uv[0], curr_uv.uv[1]))

    if height is None:
        new_height = max([i.uv[1] + i.size[1] for i in uv_dict.values()])
    else:
        new_height = height
    context.scene.nusiq_mcblend.texture_height=new_height

    if resolution >= 1:
        image = bpy.data.images.new(
            "template",
            width*resolution,
            new_height*resolution,
            alpha=True
        )
        def paint_texture(arr, uv_box, color, resolution):
            min1 = int(arr.shape[0]/resolution)-int(uv_box.uv[1]+uv_box.size[1])
            max1 = int(arr.shape[0]/resolution)-int(uv_box.uv[1])
            min2, max2 = int(uv_box.uv[0]), int(uv_box.uv[0]+uv_box.size[0])
            min1 = min1 * resolution
            min2 = min2 * resolution
            max1 = max1 * resolution
            max2 = max2 * resolution
            a = arr[min1:max1, min2:max2]
            a[...,0] = color[0]
            a[...,1] = color[1]
            a[...,2] = color[2]
            a[...,3] = color[3]

        # This array represents new texture
        # DIM0:up axis DIM1:right axis DIM2:rgba axis
        arr = np.zeros([image.size[1], image.size[0], 4])

        for uv_cube in uv_dict.values():
            paint_texture(arr, uv_cube.front, [0, 1, 0, 1], resolution)
            paint_texture(arr, uv_cube.back, [1, 0, 1, 1], resolution)
            paint_texture(arr, uv_cube.right, [1, 0, 0, 1], resolution)
            paint_texture(arr, uv_cube.left, [0, 1, 1, 1], resolution)
            paint_texture(arr, uv_cube.top, [0, 0, 1, 1], resolution)
            paint_texture(arr, uv_cube.bottom, [1, 1, 0, 1], resolution)
        image.pixels = arr.ravel()  # Apply texture pixels values

    if move_blender_uvs:
        for objprop in objprops:
            if objprop.name() in uv_dict:
                curr_uv = uv_dict[objprop.name()]
                objprop.data_uv_layers_new()
                set_cube_uv(
                    objprop, (curr_uv.uv[0], curr_uv.uv[1]),
                    curr_uv.width, curr_uv.depth, curr_uv.height,
                    width, new_height
                )

    # Return to first frame
    context.scene.frame_set(start_frame)

    return True


def set_inflate(context: bpy_types.Context, inflate: float, mode: str) -> int:
    '''
    Adds mc_inflate property to objects and changes their dimensions. Returns
    the number of edited objects.
    Returns the number of edited objects.
    '''
    if mode == 'RELATIVE':
        relative = True
    elif mode == 'ABSOLUTE':
        relative = False
    else:
        raise ValueError(f'Unknown mode for set_inflate operator: {mode}')

    counter = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            if 'mc_inflate' in obj:
                if relative:
                    effective_inflate = obj['mc_inflate'] + inflate
                else:
                    effective_inflate = inflate
                delta_inflate = effective_inflate - obj['mc_inflate']
                obj['mc_inflate'] = effective_inflate
            else:
                delta_inflate = inflate
                obj['mc_inflate'] = inflate
            # Clear parent from children for a moment
            children = obj.children
            for c in children:
                old_matrix = c.matrix_world.copy()
                c.parent = None
                c.matrix_world = old_matrix

            dimensions = np.array(obj.dimensions)

            # Set new dimensions
            dimensions = (
                dimensions +
                (2*delta_inflate/MINECRAFT_SCALE_FACTOR)
            )

            obj.dimensions = dimensions
            context.view_layer.update()

            # Add children back and set their previous transformations
            for c in children:
                c.parent = obj
                c.matrix_parent_inverse = obj.matrix_world.inverted()

            # Remove the property if it's equal to 0
            if obj['mc_inflate'] == 0:
                del obj['mc_inflate']

            counter += 1
    return counter


def round_dimensions(context: bpy_types.Context) -> int:
    '''
    Rounds dimensions of selected objects. Returns the number of edited
    objects.
    '''

    counter = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            # Clear parent from children for a moment
            children = obj.children
            for c in children:
                old_matrix = c.matrix_world.copy()
                c.parent = None
                c.matrix_world = old_matrix

            # Set new dimensions
            dimensions = np.array(obj.dimensions)
            if 'mc_inflate' in obj:
                dimensions -= (
                    obj['mc_inflate'] * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            dimensions = np.array(
                dimensions * MINECRAFT_SCALE_FACTOR
            ).round() / MINECRAFT_SCALE_FACTOR
            if 'mc_inflate' in obj:
                dimensions += (
                    obj['mc_inflate'] * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            obj.dimensions = dimensions
            context.view_layer.update()

            # Add children back and set their previous transformations
            for c in children:
                c.parent = obj
                c.matrix_parent_inverse = obj.matrix_world.inverted()

            counter += 1
    return counter

def import_model(data: tp.Dict, context: bpy_types.Context) -> bool:
    '''
    Import and build model from JSON file. Returns success result value (bool).
    '''
    assert_is_model(data)
    geometry = load_model(data, geometry_name='')
    build_geometry(geometry, context)
    context.scene.nusiq_mcblend.texture_width = geometry.texture_width
    context.scene.nusiq_mcblend.texture_height = geometry.texture_height
    if geometry.identifier.startswith('geometry.'):
        context.scene.nusiq_mcblend.model_name = geometry.identifier[9:]
    else:
        context.scene.nusiq_mcblend.model_name = geometry.identifier
    return True
