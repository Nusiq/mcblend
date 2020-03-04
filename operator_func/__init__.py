import bpy
import mathutils
import math
import numpy as np
from enum import Enum

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp

# from .uv import (
#     get_uv_face,
#     set_cube_uv,
#     set_uv
# )
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


# MAIN
def export_model(context: bpy_types.Context, model_name: str):
    object_properties = get_object_mcproperties(context)

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

    result = get_mcmodel_json(model_name, mc_bones)
    return result

def export_animation(context: bpy_types.Context):
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
        name=context.scene.bedrock_exporter.animation_name,
        length=context.scene.frame_end,
        loop_animation=context.scene.bedrock_exporter.loop_animation,
        anim_time_update=context.scene.bedrock_exporter.anim_time_update,
        bone_data=bone_data
    )

    return animation_dict
