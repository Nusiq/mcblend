import bpy
import math
import json
import numpy as np

from bpy.props import StringProperty, FloatProperty

from .operator_func import *

# Additional imports for mypy
import bpy_types
import typing as tp


class OBJECT_OT_NusiqMcblendExportOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft models from blender'''
    bl_idname = "object.nusiq_mcblend_export_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports selected objects from scene to bedrock model."

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        output = context.scene.nusiq_mcblend.path
        result = export_model(context)

        with open(output, 'w') as f:
            json.dump(result, f, indent='\t')

        self.report(
                {'INFO'} ,
                f'Model saved in {output}.'
        )
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendExportAnimationOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft animations from blender'''
    bl_idname = "object.nusiq_mcblend_export_animation_operator"
    bl_label = "Export animation for bedrock model."
    bl_description = (
        "Exports animation of selected objects to bedrock entity animation "
        "format."
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        output = context.scene.nusiq_mcblend.path_animation
        animation_dict = export_animation(context)

        # Save file and finish
        with open(output, 'w') as f:
            json.dump(animation_dict, f, indent='\t')
        self.report(
                {'INFO'} ,
                f'Animation saved in {output}.'
        )
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendMapUvOperator(bpy.types.Operator):
    '''Operator used for creating UV-mapping for minecraft model.'''
    bl_idname = "object.nusiq_mcblend_map_uv_operator"
    bl_label = "Map uv for bedrock model."
    bl_description = (
        "Set UV-mapping for minecraft objects."
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        if set_uvs(context):
            width = context.scene.nusiq_mcblend.texture_width
            height = context.scene.nusiq_mcblend.texture_height
            self.report(
                {'INFO'} ,
                f'UV map created successfuly for {width}x{height} texture.'
            )
        else:
            self.report({'ERROR'}, "Unable to create UV-mapping.")
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendUvGroupOperator(bpy.types.Operator):
    '''
    Operator used for setting custom property called mc_uv_group for selected
    objects.
    '''
    bl_idname = "object.nusiq_mcblend_uv_group_operator"
    bl_label = "Set mc_uv_group for bedrock model."
    bl_description = (
        "Set mc_uv_group for bedrock model. Objects that have the same width, "
        "depth and height and are in the same mc_uv_group are mapped to the "
        "same spot on the texutre"
    )

    group_name: StringProperty(default="", name="Name")  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        if self.group_name == "":
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    # Empty string clears the UV group
                    if 'mc_uv_group' in obj:
                        del obj['mc_uv_group']
            self.report({'INFO'} , f'Cleared mc_uv_groups.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    obj['mc_uv_group'] = self.group_name
            self.report({'INFO'} , f'Set mc_uv_group to {self.group_name}.')
        self.group_name = ""
        
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendToggleMcMirrorOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called mc_mirror for selected
    objects
    '''
    bl_idname = "object.nusiq_mcblend_toggle_mc_mirror_operator"
    bl_label = "Toggle mc_mirror for selected objects."
    bl_description = (
        "Toggle mc_mirror for selected objects. Adds or removes mirror "
        "property from a cube in minecraft model"
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        is_clearing = False
        for obj in context.selected_objects:
            if obj.type == "MESH":
                if 'mc_mirror' in obj:
                    obj['mc_mirror'] == 1
                    is_clearing = True
                    break
        if is_clearing:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    if 'mc_mirror' in obj:
                        del obj['mc_mirror']
            self.report({'INFO'} , f'Cleared mc_mirror.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    obj['mc_mirror'] = 1
            self.report({'INFO'} , f'Set mc_mirror to property 1.')

        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called mc_is_bone for selected
    objects.
    '''
    bl_idname = "object.nusiq_mcblend_toggle_mc_is_bone_operator"
    bl_label = "Toggle mc_is_bone for selected objects."
    bl_description = (
        "Toggles mc_is_bone for selected objects. Setting mc_is_bone property "
        "to 1 ensures that the object will be converted to a bone in minecraft"
        " model"
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        for obj in context.selected_objects:
            if obj.type == "MESH":
                return True
        return False

    def execute(self, context):
        is_clearing = False
        for obj in context.selected_objects:
            if obj.type == "MESH":
                if 'mc_is_bone' in obj:
                    is_clearing = True
                    break
        if is_clearing:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    if 'mc_is_bone' in obj:
                        del obj['mc_is_bone']
            self.report({'INFO'} , f'Cleared mc_is_bone.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    obj['mc_is_bone'] = {}
            self.report({'INFO'} , f'Marked slected objects as mcbones.')

        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendSetInflateOperator(bpy.types.Operator):
    '''
    Operator used for setting the inflate value of selected objects. It changes
    the dimensions of selected object and adds custom property called
    mc_inflate.
    '''
    bl_idname = "object.nusiq_mcblend_set_inflate_operator"
    bl_label = "Set the mc_inflate vale for selected objects and resise them."
    bl_description = (
        "Set the mc_inflate vale for selected objects and change their "
        "dimensions to fit the inflate values."
    )

    inflate_value: FloatProperty(default=0)  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        n_objects = set_inflate(context, self.inflate_value)
        self.inflate_value = 0
        self.report(
            {'INFO'} , f'Changed the inflate value of {n_objects} objects.'
        )
        return {'FINISHED'}


# Aditional operators
class OBJECT_OT_NusiqMcblendParentOperator(bpy.types.Operator):
    """Add parent child relation for bedrock model exporter."""
    bl_idname = "object.nusiq_mcblend_parent_operator"
    bl_label = "Parent bedrock bone"
    bl_description = "Parent object for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 2:
            return False
        elif not context.object.select_get():
            return False
        return True

    def execute(self, context: bpy_types.Context):
        def _is_parent_loop(this, start):
            if 'mc_parent' in this:
                if this['mc_parent'] is start:
                    return True
                return _is_parent_loop(this['mc_parent'], start)
            return False

        # Check looped parents
        for obj in context.selected_objects:
            if obj is not context.object:
                if _is_parent_loop(context.object, obj):
                    self.report({'ERROR'}, "Loop in parents")
                    return {'CANCELLED'}
        # No loops detected
        for obj in context.selected_objects:
            if obj is not context.object:
                obj['mc_parent'] = context.object

        self.report({'INFO'} , f'Set mc_parent to {context.object.name}')
        return {'FINISHED'}


def menu_bedrock_parent(self, context: bpy_types.Context):
    '''Used for registration of OBJECT_OT_NusiqMcblendParentOperator class'''
    self.layout.operator(
        OBJECT_OT_NusiqMcblendParentOperator.bl_idname,
        text=OBJECT_OT_NusiqMcblendParentOperator.bl_label, icon="PLUGIN"
    )


class OBJECT_OT_NusiqMcblendParentClearOperator(bpy.types.Operator):
    """Clear parent child relation for bedrock model exporter."""
    bl_idname = "object.nusiq_mcblend_parent_clear_operator"
    bl_label = "Clear parent from bedrock bone"
    bl_description = "Clear parent for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context: bpy_types.Context):
        for obj in context.selected_objects:
            if 'mc_parent' in obj:
                del obj['mc_parent']
        self.report(
            {'INFO'} , f'Cleared mc_parent property from slected objects'
        )
        return {'FINISHED'}


def menu_bedrock_parent_clear(self, context: bpy_types.Context):
    '''Used for registration of OBJECT_OT_NusiqMcblendParentClearOperator class'''
    self.layout.operator(
        OBJECT_OT_NusiqMcblendParentClearOperator.bl_idname,
        text=OBJECT_OT_NusiqMcblendParentClearOperator.bl_label, icon="PLUGIN"
    )
