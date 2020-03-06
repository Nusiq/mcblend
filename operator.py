import bpy
import math
import json
import numpy as np


from .operator_func import *

# Additional imports for mypy
import bpy_types
import typing as tp


class OBJECT_OT_NusiqBmodelExportOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft models from blender'''
    bl_idname = "object.nusiq_bmodel_export_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports selected objects from scene to bedrock model."

    def execute(self, context):
        output = context.scene.nusiq_bmodel.path
        result = export_model(context)

        with open(output, 'w') as f:
            json.dump(result, f) #, indent=4)

        return {'FINISHED'}


class OBJECT_OT_NusiqBmodelExportAnimationOperator(bpy.types.Operator):
    '''Operator used for exporting minecraft animations from blender'''
    bl_idname = "object.nusiq_bmodel_export_animation_operator"
    bl_label = "Export animation for bedrock model."
    bl_description = (
        "Exports animation of selected objects to bedrock entity animation "
        "format."
    )

    def execute(self, context):
        output = context.scene.nusiq_bmodel.path_animation
        animation_dict = export_animation(context)

        # Save file and finish
        with open(output, 'w') as f:
            json.dump(animation_dict, f) #, indent=4)
        return {'FINISHED'}


class OBJECT_OT_NusiqBmodelMapUvOperator(bpy.types.Operator):
    '''Operator used for creating UV-mapping for minecraft model.'''
    bl_idname = "object.nusiq_bmodel_map_uv_operator"
    bl_label = "Map uv for bedrock model."
    bl_description = (
        "Set UV-mapping for minecraft objects."
    )

    def execute(self, context):
        print("TEST")
        return {'FINISHED'}

# Aditional operators
class OBJECT_OT_NusiqBmodelParentOperator(bpy.types.Operator):
    """Add parent child relation for bedrock model exporter."""
    bl_idname = "object.nusiq_bmodel_parent_operator"
    bl_label = "Parent bedrock bone"
    bl_description = "Parent object for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy_types.Context):
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

        return {'FINISHED'}


def menu_bedrock_parent(self, context: bpy_types.Context):
    '''Used for registration of OBJECT_OT_NusiqBmodelParentOperator class'''
    self.layout.operator(
        OBJECT_OT_NusiqBmodelParentOperator.bl_idname,
        text=OBJECT_OT_NusiqBmodelParentOperator.bl_label, icon="PLUGIN"
    )


class OBJECT_OT_NusiqBmodelParentClearOperator(bpy.types.Operator):
    """Clear parent child relation for bedrock model exporter."""
    bl_idname = "object.nusiq_bmodel_parent_clear_operator"
    bl_label = "Clear parent from bedrock bone"
    bl_description = "Clear parent for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.selected_objects) >= 1:
            return True
        return False

    def execute(self, context: bpy_types.Context):
        for obj in context.selected_objects:
            if 'mc_parent' in obj:
                del obj['mc_parent']
        return {'FINISHED'}


def menu_bedrock_parent_clear(self, context: bpy_types.Context):
    '''Used for registration of OBJECT_OT_NusiqBmodelParentClearOperator class'''
    self.layout.operator(
        OBJECT_OT_NusiqBmodelParentClearOperator.bl_idname,
        text=OBJECT_OT_NusiqBmodelParentClearOperator.bl_label, icon="PLUGIN"
    )
