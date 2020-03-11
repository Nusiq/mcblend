import bpy
import mathutils
import math
import numpy as np
from enum import Enum

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp

from .uv import (
    get_uv_mc_cubes, UvMcCube, plan_uv, set_cube_uv
)
from .animation import (
    get_mcanimation_json, 
    get_mctranslations,
    get_next_keyframe,
    get_transformations
)
from .model import (
    get_mcbone_json,
    get_mcmodel_json
)
from .common import (
    MCObjType,
    get_object_mcproperties,
    get_vect_json,
    pick_closest_rotation
)

def export_model(context: bpy_types.Context) -> tp.Dict:
    '''
    Uses context.selected_objects to create and return dictionary with
    minecraft model.
    '''
    object_properties = get_object_mcproperties(context)
    texture_width = context.scene.nusiq_bmodel.texture_width
    texture_height = context.scene.nusiq_bmodel.texture_height

    mc_bones: tp.List[tp.Dict] = []

    for obj in context.selected_objects:
        if (
            obj.name in object_properties and
            object_properties[obj.name].mctype in
            [MCObjType.BONE, MCObjType.BOTH]
        ):
            # Create cubes list
            if object_properties[obj.name].mctype == MCObjType.BOTH:
                cubes = [obj]
            elif object_properties[obj.name].mctype == MCObjType.BONE:
                cubes = []
            # Add children cubes if they are MCObjType.CUBE type
            for child_name in (
                object_properties[obj.name].mcchildren
            ):
                if (
                    child_name in object_properties and
                    object_properties[child_name].mctype ==
                    MCObjType.CUBE
                ):
                    cubes.append(bpy.data.objects[child_name])

            mcbone = get_mcbone_json(obj, cubes)
            mc_bones.append(mcbone)

    result = get_mcmodel_json(
        context.scene.nusiq_bmodel.model_name,
        mc_bones, texture_width,
        texture_height
    )
    return result

def export_animation(context: bpy_types.Context) -> tp.Dict:
    '''
    Uses context.selected_objects to create and return dictionary with
    minecraft animation.
    '''
    object_properties = get_object_mcproperties(context)

    start_frame = context.scene.frame_current
    
    bone_data: tp.Dict[str, tp.Dict[str, tp.List[tp.Dict]]] = (  # TODO - Create object for that for safer/cleaner code - https://www.python.org/dev/peps/pep-0589/
        defaultdict(lambda: {
            'scale': [], 'rotation': [], 'position': []
        })
    )

    # Stop animation if running & jump to the first frame
    bpy.ops.screen.animation_cancel()
    context.scene.frame_set(0)
    default_translation = get_transformations(context, object_properties)
    prev_rotation = {
        name:np.zeros(3) for name in default_translation.keys()
    }

    next_keyframe = get_next_keyframe(context)

    while next_keyframe is not None:
        context.scene.frame_set(math.ceil(next_keyframe))
        current_translations = get_transformations(context, object_properties)
        for d_key, d_val in default_translation.items():
            # Get the difference from original
            loc, rot, scale = get_mctranslations(
                d_val.rotation, current_translations[d_key].rotation,
                d_val.scale, current_translations[d_key].scale,
                d_val.location, current_translations[d_key].location
            )
            time = str(round(
                (context.scene.frame_current-1) /
                context.scene.render.fps, 4
            ))
            
            bone_data[d_key]['position'].append({
                'time': time,
                'value': get_vect_json(loc)
            })
            rot = pick_closest_rotation(
                rot, prev_rotation[d_key]
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

    context.scene.frame_set(start_frame)
    animation_dict = get_mcanimation_json(
        context,
        name=context.scene.nusiq_bmodel.animation_name,
        length=context.scene.frame_end,
        loop_animation=context.scene.nusiq_bmodel.loop_animation,
        anim_time_update=context.scene.nusiq_bmodel.anim_time_update,
        bone_data=bone_data
    )

    return animation_dict

def set_uvs(context: bpy_types.Context) -> bool:
    width = context.scene.nusiq_bmodel.texture_width
    height = context.scene.nusiq_bmodel.texture_height
    move_blender_uvs = context.scene.nusiq_bmodel.move_blender_uvs
    move_existing_mappings = context.scene.nusiq_bmodel.move_existing_mappings
    remove_old_mappings = context.scene.nusiq_bmodel.remove_old_mappings
    resolution = context.scene.nusiq_bmodel.texture_template_resolution

    objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

    uv_dict: tp.Dict[str, UvMcCube] = get_uv_mc_cubes(
        objs, read_existing_uvs=not move_existing_mappings
    )
    uv_mc_cubes = [i for i in uv_dict.values()]
    if height <= 0:
        height = None

    map_result = plan_uv(uv_mc_cubes, width, height)
    if map_result is False:
        return False

    if remove_old_mappings:
        for obj in objs:
            while len(obj.data.uv_layers) > 0:
                obj.data.uv_layers.remove(obj.data.uv_layers[0])



    for obj in objs:
        if obj.name in uv_dict:
            curr_uv = uv_dict[obj.name]
            obj['mc_uv_u'] = curr_uv.uv[0]
            obj['mc_uv_v'] = curr_uv.uv[1]

    if height is None:
        new_height = max([i.uv[1] + i.size[1] for i in uv_dict.values()])
    else:
        new_height = height
    context.scene.nusiq_bmodel.texture_height=new_height

    # TODO - Create texture template
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
        for obj in objs:
            if obj.name in uv_dict:
                curr_uv = uv_dict[obj.name]
                obj.data.uv_layers.new()
                set_cube_uv(
                    obj, (curr_uv.uv[0], curr_uv.uv[1]),
                    curr_uv.width, curr_uv.depth, curr_uv.height,
                    width, new_height
                )
    return True

