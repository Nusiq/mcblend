import bpy
import math
import mathutils
import json
import numpy as np


def get_local_matrix(parent_world_matrix, child_world_matrix):
    '''
    Returns translation matrix of child in relation to parent.
    In space defined by parent translation matrix.
    '''
    return (
        parent_world_matrix.inverted() @ child_world_matrix
    )

# Pseudocode
def pivot(obj):
    result = [0, 0, 0]
    def local_crds():
        pass
    if obj.parent is not None:
        parent_pivot = pivot(obj.parent)
        result += local_crds(obj.crds, obj.parent.crds) + parent_pivot
    else:
        result = obj.crds
    return result

# Pseudocode
def rotation(obj):
    def local_rotation():
        pass
    if obj.parent is not None:
        return local_rotation(obj.rot, obj.parent.rot)
    else:
        return obj.rot

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
        parent = bone['mc_parent']
        mcbone['parent'] = parent.name
        rot = parent.matrix_world.to_euler('XYZ')
        rot = (
            mathutils.Matrix.Rotation(-rot[0], 4, 'X') @
            mathutils.Matrix.Rotation(-rot[1], 4, 'Y') @
            mathutils.Matrix.Rotation(-rot[2], 4, 'Z')
        )

        matrix = rot @ matrix

    b_pivot, b_rot, c_size = matrix.decompose()

    b_rot = np.array(b_rot.to_euler('XYZ'))[[0, 2, 1]]
    b_rot = b_rot * np.array([1, -1, 1])
    b_rot = b_rot * 180/math.pi  # math.degrees() for array

    # TODO -handle other sizes of cube
    c_size = np.array(c_size.xzy) * 2  # Size of default cube is 2x2x2
    b_pivot = np.array(b_pivot.xzy)
    c_origin = b_pivot - c_size/2

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
