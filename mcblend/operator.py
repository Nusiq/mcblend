'''
This module contains all of the operators.
'''
# don't import future annotations Blender needs that
import json
from typing import Optional, Dict

import bpy_types
import bpy
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .operator_func import (
    export_model, export_animation, set_uvs, set_inflate,
    round_dimensions, import_model
)
from .operator_func.json_tools import CompactEncoder
from .operator_func.exception import (
    NameConflictException, NotEnoughTextureSpace,
)
from .operator_func.jsonc_decoder import JSONCDecoder



class OBJECT_OT_NusiqMcblendExportModelOperator(bpy.types.Operator, ExportHelper):
    '''Operator used for exporting minecraft models from blender'''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_export_operator"
    bl_label = "Export model"
    bl_options = {'REGISTER'}
    bl_description = "Exports selected objects from scene to bedrock model."

    filename_ext = '.geo.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        try:
            result = export_model(context)
        except NameConflictException as e:
            self.report({'WARNING'}, str(e))
            return {'FINISHED'}

        with open(self.filepath, 'w') as f:
            json.dump(result, f, cls=CompactEncoder)

        self.report({'INFO'}, f'Model saved in {self.filepath}.')
        return {'FINISHED'}


def menu_func_nusiq_mcblend_export_model(self, context):
    # pylint: disable=W0613
    '''Function that adds export model operator to the menu.'''
    self.layout.operator(
        OBJECT_OT_NusiqMcblendExportModelOperator.bl_idname,
        text="Mcblend: Export model"
    )


# Export animation
class OBJECT_OT_NusiqMcblendExportAnimationOperator(
        bpy.types.Operator, ExportHelper):
    '''Operator used for exporting minecraft animations from blender'''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_export_animation_operator"
    bl_label = "Export animation"
    bl_options = {'REGISTER'}
    bl_description = (
        "Exports animation of selected objects to bedrock entity animation "
        "format."
    )


    filename_ext = '.animation.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        # Read and validate old animation file
        old_dict: Optional[Dict] = None
        try:
            with open(self.filepath, 'r') as f:
                old_dict = json.load(f, cls=JSONCDecoder)
        except (json.JSONDecodeError, OSError):
            pass

        try:
            animation_dict = export_animation(context, old_dict)
        except NameConflictException as e:
            self.report({'WARNING'}, str(e))
            return {'FINISHED'}

        # Save file and finish
        with open(self.filepath, 'w') as f:
            json.dump(animation_dict, f, cls=CompactEncoder)
        self.report({'INFO'}, f'Animation saved in {self.filepath}.')
        return {'FINISHED'}


def menu_func_nusiq_mcblend_export_animation(self, context):
    # pylint: disable=W0613
    '''Function that adds export animation operator to the menu.'''
    self.layout.operator(
        OBJECT_OT_NusiqMcblendExportAnimationOperator.bl_idname,
        text="Mcblend: Export anmiation"
    )


# Uv map
class OBJECT_OT_NusiqMcblendMapUvOperator(bpy.types.Operator):
    '''Operator used for creating UV-mapping for minecraft model.'''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_map_uv_operator"
    bl_label = "Map uv for bedrock model."
    bl_options = {'REGISTER', 'UNDO'}
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
        try:
            set_uvs(context)
        except NotEnoughTextureSpace:
            self.report({'ERROR'}, "Unable to create UV-mapping.")
            return {'FINISHED'}
        except NameConflictException as e:
            self.report({'WARNING'}, str(e))
            return {'FINISHED'}
        width = context.scene.nusiq_mcblend.texture_width
        height = context.scene.nusiq_mcblend.texture_height
        self.report(
            {'INFO'},
            f'UV map created successfuly for {width}x{height} texture.'
        )

        return {'FINISHED'}


# Uv group
class OBJECT_OT_NusiqMcblendUvGroupOperator(bpy.types.Operator):
    '''
    Operator used for setting custom property called mc_uv_group for selected
    objects.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_uv_group_operator"
    bl_label = "Set mc_uv_group for bedrock model."
    bl_options = {'REGISTER', 'UNDO'}
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
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.group_name == "":
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    # Empty string clears the UV group
                    if 'mc_uv_group' in obj:
                        del obj['mc_uv_group']
            self.report({'INFO'}, 'Cleared mc_uv_groups.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    obj['mc_uv_group'] = self.group_name
            self.report({'INFO'}, f'Set mc_uv_group to {self.group_name}.')
        self.group_name = ""

        return {'FINISHED'}


# Toogle mc_mirror
class OBJECT_OT_NusiqMcblendToggleMcMirrorOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called mc_mirror for selected
    objects
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_toggle_mc_mirror_operator"
    bl_label = "Toggle mc_mirror for selected objects."
    bl_options = {'REGISTER', 'UNDO'}
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
                    is_clearing = True
                    break
        if is_clearing:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    if 'mc_mirror' in obj:
                        del obj['mc_mirror']
            self.report({'INFO'}, 'Cleared mc_mirror.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    obj['mc_mirror'] = {}
            self.report({'INFO'}, 'Set mc_mirror to property 1.')

        return {'FINISHED'}


# Toggle mc_is_bone
class OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called mc_is_bone for selected
    objects.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_toggle_mc_is_bone_operator"
    bl_label = "Toggle mc_is_bone for selected objects."
    bl_options = {'REGISTER', 'UNDO'}
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
            if obj.type == "MESH" or obj.type == "EMPTY":
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
                if obj.type == "MESH" or obj.type == "EMPTY":
                    if 'mc_is_bone' in obj:
                        del obj['mc_is_bone']
            self.report({'INFO'}, 'Cleared mc_is_bone.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    obj['mc_is_bone'] = {}
            self.report({'INFO'}, 'Marked slected objects as mcbones.')

        return {'FINISHED'}


# Inflate
class OBJECT_OT_NusiqMcblendSetInflateOperator(bpy.types.Operator):
    '''
    Operator used for setting the inflate value of selected objects. It changes
    the dimensions of selected object and adds custom property called
    mc_inflate.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_set_inflate_operator"
    bl_label = "Set mc_inflate"
    bl_options = {'REGISTER', 'UNDO', 'BLOCKING', 'GRAB_CURSOR'}
    bl_description = (
        "Set the mc_inflate vale for selected objects and change their "
        "dimensions to fit the inflate values."
    )


    inflate_value: FloatProperty(default=0)  # type: ignore
    mode: EnumProperty(  # type: ignore
        items=(
            ('RELATIVE', 'Relative', 'Add or remove to current inflate value'),
            ('ABSOLUTE', 'Absolute', 'Set the inflate value'),
        ),
        name='Mode'
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def invoke(self, context, event):
        self.inflate_value = 0
        self.mode = 'RELATIVE'
        return {'FINISHED'}

    def execute(self, context):
        set_inflate(  # Returns number of inflated objects
            context, self.inflate_value, self.mode
        )
        return {'FINISHED'}


# Round dimensions
class OBJECT_OT_NusiqMcblendRoundDimensionsOperator(bpy.types.Operator):
    '''
    Operator used for rounding the values of dimensions.
    '''
    # pylint: disable=C0116, W0613, R0201, no-member
    bl_idname = "object.nusiq_mcblend_round_dimensions_operator"
    bl_label = "Round dimensions"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Round the dimensions of selected object to integers."
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        round_dimensions(  # Returns number of edited objects
            context
        )
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendImport(bpy.types.Operator, ImportHelper):
    '''Operator used for importiong minecraft models to blender'''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_import_operator"
    bl_label = "Import model"
    bl_options = {'REGISTER'}
    bl_description = "Import model from json file."
    # ImportHelper mixin class uses this
    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore
        default="*.json",
        options={'HIDDEN'},
        maxlen=1000,
    )

    geometry_name: StringProperty(  # type: ignore
        default='',
        maxlen=500
    )

    replace_bones_with_empties: BoolProperty(  # type: ignore
        default=False,
        description='Creates empties instead of armature and bones'
    )

    def execute(self, context):
        # Save file and finish
        with open(self.filepath, 'r') as f:
            data = json.load(f, cls=JSONCDecoder)
        try:
            import_model(
                data, self.geometry_name, self.replace_bones_with_empties,
                context)
        except AssertionError as e:
            self.report(
                {'ERROR'}, f'Invalid model: {e}'
            )
        except ValueError as e:
            self.report(
                {'ERROR'}, f'{e}'
            )
        return {'FINISHED'}

# Helper function - add operator to the import men
def menu_func_nusiq_mcblend_import(self, context):
    # pylint: disable=W0613
    '''Function that adds import model operator to the menu.'''
    self.layout.operator(
        OBJECT_OT_NusiqMcblendImport.bl_idname, text="Mcblend: Import model"
    )
