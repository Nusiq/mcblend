import bpy
import math
import mathutils
import json
import numpy as np


MINECRAFT_SCALE_FACTOR = 16


def cube_size(obj):
    # 1. ---; 2. --+; 3. -++; 4. -+-; 5. +--; 6. +-+; 7. +++; 8. ++-
    return np.array(obj.bound_box[7]) - np.array(obj.bound_box[1])

def cube_position(obj):
    return np.array(obj.bound_box[1])

def get_local_matrix(parent_world_matrix, child_world_matrix):
    '''
    Returns translation matrix of child in relation to parent.
    In space defined by parent translation matrix.
    '''
    return (
        parent_world_matrix.inverted() @ child_world_matrix
    )


def pivot(obj):
    def local_crds(parent_matrix, child_matrix):
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _pivot(obj):
        if 'mc_parent' in obj:
            result = local_crds(
                obj['mc_parent'].matrix_world,
                obj.matrix_world
            )
            result += _pivot(obj['mc_parent'])
        else:
            result = obj.matrix_world.to_translation()
        return result

    return np.array(_pivot(obj).xzy)


# Pseudocode
def rotation(obj):
    def local_rotation(parent_matrix, child_matrix):
        parent_rot = parent_matrix.to_quaternion()
        child_rot = child_matrix.to_quaternion()

        return child_rot.rotation_difference(parent_rot).to_euler('XZY')

    if 'mc_parent' in obj:
        result = local_rotation(
            obj.matrix_world, obj['mc_parent'].matrix_world
        )
    else:
        result = obj.matrix_world.to_euler('XZY')
    result = np.array(result)[[0, 2, 1]]
    result = result * np.array([1, -1, 1])
    result = result * 180/math.pi  # math.degrees() for array
    return result


# Wziac poprzednika, z poprzednika obliczyć PIVOT
def to_mc_bone(
    bone, cubes_matrixes=None
):
    # TODO - make use of cubes_matrix
    # mcbone - parent, pivot, rotation
    # mccube - origin, size, inflate, pivot, rotation, uv

    # For the first version I want to use only:
    # origin, size, rotation
    # for mccube
    def json_vect(arr):
        return [i for i in arr]
    mcbone = {'name': bone.name, 'cubes': []}

    matrix = bone.matrix_world
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name

    _, _, _b_scale = matrix.decompose()
    b_pivot = pivot(bone)
    b_rot = rotation(bone)

    c_size = np.array(_b_scale.xzy) * cube_size(bone) * MINECRAFT_SCALE_FACTOR
    b_pivot = np.array(b_pivot) * MINECRAFT_SCALE_FACTOR
    c_origin = (b_pivot - c_size/2)

    mcbone['pivot'] = json_vect(b_pivot)
    mcbone['rotation'] = json_vect(b_rot)
    mcbone['cubes'].append({
        'uv': [0, 0],
        'size': json_vect(c_size),
        'origin': json_vect(c_origin),
        'pivot': json_vect(b_pivot)
    })
    return mcbone


class NUSIQ_OT_MainOperator(bpy.types.Operator):
    bl_idname = "nusiq.main_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports visible objects from scene to bedrock model."

    def __init__(self):
        super().__init__()
        self.output = (
            "C:/Users/artur/AppData/Local/Packages/"
            "Microsoft.MinecraftUWP_8wekyb3d8bbwe/LocalState/games/"
            "com.mojang/minecraftWorlds/Models-Tests/resource_packs/"
            "physics_rp/models/entity/b_model.geo.json"
        )

    def execute(self, context):
        mc_bones = []

        # prev_obj = None
        # for obj in bpy.data.objects:
        #     if obj.visible_get():
        #         if prev_obj is not None:
        #             obj['mc_parent'] = prev_obj
        #         prev_obj = obj

        for obj in bpy.data.objects:
            if obj.visible_get():
                mcbone = to_mc_bone(obj)
                mc_bones.append(mcbone)
        result = {
            "format_version": "1.12.0",
            "minecraft:geometry": [
                {
                    "description": {
                        "identifier": "geometry.b_model",
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
        # print(result)
        with open(self.output, 'w') as f:
            json.dump(result, f, indent=4)

        return {'FINISHED'}
