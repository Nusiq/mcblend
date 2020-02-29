import bpy
import math
import json
import numpy as np


from .operator_funcs import *

class OBJECT_OT_ExportOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft models from blender'''
    bl_idname = "object.export_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports selected objects from scene to bedrock model."

    def execute(self, context):
        object_properties = get_object_properties()

        mc_bones = []
        output = context.scene.bedrock_exporter.path
        model_name = context.scene.bedrock_exporter.model_name

        for obj in bpy.context.selected_objects:
            if (
                obj.name in object_properties and
                object_properties[obj.name]['mc_obj_type'] in [BONE, BOTH]
            ):
                # Create cubes list
                if object_properties[obj.name]['mc_obj_type'] == BOTH:
                    cubes = [obj]
                elif object_properties[obj.name]['mc_obj_type'] == BONE:
                    cubes = []
                # Add children cubes if they are CUBE type
                for child in (
                    object_properties[obj.name]['mc_children']
                ):
                    if (
                        child.name in object_properties and
                        object_properties[child.name]['mc_obj_type'] == CUBE
                    ):
                        cubes.append(child)

                mcbone = to_mc_bone(obj, cubes)
                mc_bones.append(mcbone)

        result = get_model_template(model_name, mc_bones)

        with open(output, 'w') as f:
            json.dump(result, f) #, indent=4)

        return {'FINISHED'}


class OBJECT_OT_ExportAnimationOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft animations from blender'''
    bl_idname = "object.export_animation_operator"
    bl_label = "Export animation for bedrock model."
    bl_description = (
        "Exports animation of selected objects to bedrock entity animation "
        "format."
    )

    _animation_dict = None
    _animation_name = None

    def execute(self, context):
        wm = context.window_manager

        object_properties = get_object_properties()

        start_frame = bpy.context.scene.frame_current
        bone_data: tp.Dict[str, tp.Dict[str, tp.List[int]]] = (
            defaultdict(lambda: {
                'scale': [], 'rotation': [], 'position': []
            })
        )

        # Stop animation if running & jump to the first frame
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(0)
        default_translation = get_transformations(object_properties)
        prev_rotation = {
            name:np.zeros(3) for name in default_translation.keys()
        }

        next_keyframe = get_next_keyframe()
        
        while next_keyframe is not None:
            bpy.context.scene.frame_set(math.ceil(next_keyframe))
            print(f'setting frame {next_keyframe}')
            current_translations = get_transformations(object_properties)
            for d_key, d_val in default_translation.items():
                # Get the difference from original
                loc, rot, scale = to_mc_translation_vectors(
                    d_val['rotation'], current_translations[d_key]['rotation'],
                    d_val['scale'], current_translations[d_key]['scale'],
                    d_val['location'], current_translations[d_key]['location']
                )
                time = str(round(
                    (bpy.context.scene.frame_current-1) /
                    bpy.context.scene.render.fps, 4
                ))
                
                bone_data[d_key]['position'].append({
                    'time': time,
                    'value': json_vect(loc)
                })
                print(f'The frame is {bpy.context.scene.frame_current} Time is {time}')
                rot = pick_closest_rotation(
                    rot, prev_rotation[d_key]
                )
                bone_data[d_key]['rotation'].append({
                    'time': time,
                    'value': json_vect(rot)
                })
                bone_data[d_key]['scale'].append({
                    'time': time,
                    'value': json_vect(scale)
                })

                prev_rotation[d_key] = rot  # Save previous rotation

            next_keyframe = get_next_keyframe()


        animation_dict = get_animation_template(
            name=context.scene.bedrock_exporter.animation_name,
            length=bpy.context.scene.frame_end,
            loop_animation=context.scene.bedrock_exporter.loop_animation,
            anim_time_update=context.scene.bedrock_exporter.anim_time_update,
            bone_data=bone_data
        )

        # Save file and finish
        bpy.context.scene.frame_set(start_frame)
        output = context.scene.bedrock_exporter.path_animation
        with open(output, 'w') as f:
            json.dump(animation_dict, f) #, indent=4)
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
