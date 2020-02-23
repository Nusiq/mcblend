import bpy
import math
import mathutils
import json
import numpy as np

from bpy.props import StringProperty
from bpy_extras import object_utils

MINECRAFT_SCALE_FACTOR = 16

# Names for temporary types of objects for the exporter
CUBE, BONE, BOTH = 'CUBE', 'BONE', "BOTH"


# TODO - apply translation
def cube_size(obj, translation):
    # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return (np.array(obj.bound_box[6]) - np.array(obj.bound_box[0]))[[0, 2, 1]]


# TODO - apply translation
def cube_position(obj, translation):
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(obj.bound_box[0])[[0, 2, 1]]


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


def rotation(child_matrix, parent_matrix=None):
    def local_rotation(child_matrix, parent_matrix):
        parent_rot = parent_matrix.to_quaternion()
        child_rot = child_matrix.to_quaternion()

        return parent_rot.rotation_difference(child_rot).to_euler('XZY')

    if parent_matrix is not None:
        result = local_rotation(
            child_matrix, parent_matrix
        )
    else:
        result = child_matrix.to_euler('XZY')
    result = np.array(result)[[0, 2, 1]]
    result = result * np.array([1, -1, 1])
    result = result * 180/math.pi  # math.degrees() for array
    return result


def to_mc_bone(
    bone, cubes=None
):
    # mcbone - parent, pivot, rotation
    # mccube - origin, size, inflate, pivot, rotation, uv

    # For the first version I want to use only:
    # origin, size, rotation
    # for mccube

    # Helper functions
    # TODO - apply translation
    print(f"Working on bone: {bone.name} with cubes {[i.name for i in cubes]}")
    def _scale(obj):
        '''Scale of a bone'''
        _, _, scale = obj.matrix_world.decompose()
        return np.array(scale.xzy)

    def json_vect(arr):
        return [i for i in arr]
    mcbone = {'name': bone.name, 'cubes': []}

    # Code
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name
        b_rot = rotation(bone.matrix_world, bone['mc_parent'].matrix_world)  # NO TRANSLATION
    else:
        b_rot = rotation(bone.matrix_world)  # NO TRANSLATION

    b_pivot = pivot(bone) * MINECRAFT_SCALE_FACTOR  # NO TRANSLATION
    
    for cube in cubes:
        translation = get_local_matrix(
            bone.matrix_world, cube.matrix_world
        )

        _b_scale = _scale(cube)  # @ NO TRANSLATION

        c_size = cube_size(cube, translation) * _b_scale * MINECRAFT_SCALE_FACTOR # @ TRANSLATION
        c_pivot = pivot(cube) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            cube_position(cube, translation) * _b_scale * MINECRAFT_SCALE_FACTOR  # @ TRANSLATION
        )
        c_rot = rotation(cube.matrix_world, bone.matrix_world)

        mcbone['cubes'].append({
            'uv': [0, 0],
            'size': json_vect(c_size),
            'origin': json_vect(c_origin),
            'pivot': json_vect(c_pivot),
            'rotation': json_vect(c_rot)
        })

    mcbone['pivot'] = json_vect(b_pivot)
    mcbone['rotation'] = json_vect(b_rot)
    return mcbone


def get_model_template(model_name, mc_bones):
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


def set_mc_obj_types():
    '''
    Loops through bpy.context.selected_objects and assigns custom poperty
    "mc_obj_type_tmp" with value "CUBE" or "BONE" or "BOTH".

    Also adds "mc_children_tmp" properties for easy access to reverse relation
    of "mc_parent".
    '''
    for obj in bpy.context.selected_objects:
        if "mc_parent" in obj:
            if "mc_children_tmp" in obj["mc_parent"]:
                obj["mc_parent"]["mc_children_tmp"].append(obj)
            else:
                obj["mc_parent"]["mc_children_tmp"] = [obj]

    for obj in bpy.context.selected_objects:
        if obj.type == 'EMPTY':
            obj['mc_obj_type_tmp'] = BONE
        elif obj.type == 'MESH':
            if "mc_children_tmp" in obj:
                obj['mc_obj_type_tmp'] = BOTH
            elif "mc_is_bone" in obj and obj["mc_is_bone"] is True:
                obj["mc_obj_type_tmp"] = BOTH
            elif "mc_parent" in obj:
                obj["mc_obj_type_tmp"] = CUBE
            else:  # Not connected to anything
                obj["mc_obj_type_tmp"] = BOTH
    # Objects other than EMPTY and MESH are ignored.


def clear_mc_obj_tmp_properties():
    '''
    Removes temportary custom properties from selected objects
    assigned during export process.
    '''
    for obj in bpy.context.selected_objects:
        if "mc_obj_type_tmp" in obj:
            del obj["mc_obj_type_tmp"]
        if "mc_children_tmp" in obj:
            obj["mc_children_tmp"].clear()
            del obj["mc_children_tmp"]


class OBJECT_OT_ExportOperator(bpy.types.Operator):
    bl_idname = "object.export_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports selected objects from scene to bedrock model."

    def execute(self, context):
        set_mc_obj_types()

        mc_bones = []
        output = context.scene.bedrock_exporter.path
        model_name = context.scene.bedrock_exporter.model_name

        for obj in bpy.context.selected_objects:
            if (
                'mc_obj_type_tmp' in obj and
                obj['mc_obj_type_tmp'] in [BONE, BOTH]
            ):
                # Create cubes list
                if obj['mc_obj_type_tmp'] == BOTH:
                    cubes = [obj]
                elif obj['mc_obj_type_tmp'] == BONE:
                    cubes = []
                if 'mc_children_tmp' in obj:
                    for child in obj['mc_children_tmp']:
                        if (
                            'mc_obj_type_tmp' in child and
                            child['mc_obj_type_tmp'] == CUBE
                        ):
                            cubes.append(child)

                mcbone = to_mc_bone(obj, cubes)
                mc_bones.append(mcbone)

        result = get_model_template(model_name, mc_bones)

        clear_mc_obj_tmp_properties()

        with open(output, 'w') as f:
            json.dump(result, f, indent=4)

        return {'FINISHED'}

# Aditional operators

class OBJECT_OT_BedrockParentOperator(bpy.types.Operator):
    """Add parent child relation for bedrock model exporter."""
    bl_idname = "object.parent_operator"
    bl_label = "Parent bedrock bone"
    bl_description = "Parent object for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) < 2:
            return False
        elif not bpy.context.object.select_get():
            return False
        return True

    def execute(self, context):
        def _is_parent_loop(this, start):
            if 'mc_parent' in this:
                if this['mc_parent'] is start:
                    print(this['mc_parent'])
                    return True
                return _is_parent_loop(this['mc_parent'], start)
            return False

        # Check looped parents
        for obj in bpy.context.selected_objects:
            if obj is not bpy.context.object:
                if _is_parent_loop(bpy.context.object, obj):
                    self.report({'ERROR'}, "Loop in parents")
                    return {'CANCELLED'}
        # No loops detected
        for obj in bpy.context.selected_objects:
            if obj is not bpy.context.object:
                obj['mc_parent'] = bpy.context.object

        return {'FINISHED'}


def menu_bedrock_parent(self, context):
    '''Used for registration of OBJECT_OT_BedrockParentOperator class'''
    self.layout.operator(
        OBJECT_OT_BedrockParentOperator.bl_idname,
        text=OBJECT_OT_BedrockParentOperator.bl_label, icon="PLUGIN"
    )


class OBJECT_OT_BedrockParentClearOperator(bpy.types.Operator):
    """Clear parent child relation for bedrock model exporter."""
    bl_idname = "object.parent_clear_operator"
    bl_label = "Clear parent from bedrock bone"
    bl_description = "Clear parent for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) >= 1:
            return True
        return False

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if 'mc_parent' in obj:
                del obj['mc_parent']
        return {'FINISHED'}


def menu_bedrock_parent_clear(self, context):
    '''Used for registration of OBJECT_OT_BedrockParentClearOperator class'''
    self.layout.operator(
        OBJECT_OT_BedrockParentClearOperator.bl_idname,
        text=OBJECT_OT_BedrockParentClearOperator.bl_label, icon="PLUGIN"
    )
