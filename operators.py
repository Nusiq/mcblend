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
    _timer = None
    _start_frame = None
    _animation_dict = None
    _animation_name = None

    def add_keyframe(
        self, bone: str, frame: int, type_: str, value: np.ndarray
    ):
        '''
        Adds new value to the self._animation_dict dictionary.

        :param str bone: name of the bone.
        :param int frame: the number of frame to edit of the animation.
        :param str type_: string with 'rotation', 'position' or 'scale' value.
        Indicates which value in animation should be changed.
        :param np.ndarray value: Vector with values to insert to the animation.
        '''
        bones = self._animation_dict['animations'][
            f"animation.{self._animation_name}"
        ]["bones"]
        if bone not in bones:
            bones[bone] = {}
        if type_ not in ['rotation', 'position', 'scale']:
            print(
                f'WARNING! Unknown translation type - {type_}. Use rotation, '
                'position or scale instead.'
            )
        if type_ not in bones[bone]:
            bones[bone][type_] = {}
        bones[bone][type_][
            f'{round((frame-1)/bpy.context.scene.render.fps, 4)}'
        ] = json_vect(value)

    def execute(self, context):
        wm = context.window_manager

        object_properties = get_object_properties()
        #self._timer = wm.event_timer_add(1.0, window=context.window)

        self._start_frame = bpy.context.scene.frame_current
        self._animation_name = context.scene.bedrock_exporter.animation_name
        loop_animation = context.scene.bedrock_exporter.loop_animation
        anim_time_update = context.scene.bedrock_exporter.anim_time_update
        self._animation_dict = get_animation_template(
            self._animation_name,
            bpy.context.scene.frame_end,
            loop_animation,
            anim_time_update
        )

        # Stop animation if running & jump to the first frame
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_set(0)

        next_keyframe = get_next_keyframe()
        while next_keyframe is not None:
            if bpy.context.scene.frame_current == 0:
                self.default_translation = get_transformations(object_properties)
                self.prev_rotation = {
                    name:np.zeros(3)
                    for name in self.default_translation.keys()
                }
            else:
                current_translations = get_transformations(object_properties)
                for d_key, d_val in self.default_translation.items():
                    # Get the difference from original
                    loc, rot, scale = to_mc_translation_vectors(
                        d_val['rotation'], current_translations[d_key]['rotation'],
                        d_val['scale'], current_translations[d_key]['scale'],
                        d_val['location'], current_translations[d_key]['location']
                    )


                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='position', value=loc
                    )
                    
                    rot = pick_closest_rotation(
                        rot, self.prev_rotation[d_key]
                    )
                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='rotation', value=rot
                    )

                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='scale', value=scale
                    )

                    self.prev_rotation[d_key] = rot  # Save previous rotation

            next_keyframe = get_next_keyframe()
            if next_keyframe is not None:
                bpy.context.scene.frame_set(math.ceil(next_keyframe))
            else:
                bpy.context.scene.frame_set(self._start_frame)
                output = context.scene.bedrock_exporter.path_animation
                with open(output, 'w') as f:
                    json.dump(self._animation_dict, f) #, indent=4)
                return {'FINISHED'}
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
