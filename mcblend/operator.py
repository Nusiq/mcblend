'''
This module contains all of the operators.
'''
# don't import future annotations Blender needs that
import json
from typing import Optional, Dict

import bpy_types
import bpy
from bpy.props import (
    StringProperty, FloatProperty, EnumProperty, BoolProperty, IntProperty)
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
from .operator_func.texture_generator import list_mask_types_as_blender_enum

# TODO - move this somewhere else
from .panel import get_unused_uv_group_name


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
        len_anims = len(context.scene.nusiq_mcblend_animations)
        curr_anim_id = context.scene.nusiq_mcblend_active_animation
        if 0 < curr_anim_id or curr_anim_id >= len_anims:
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
        text="Mcblend: Export animation"
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
    Operator used for setting custom property called uv_group for selected
    objects.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_uv_group_operator"
    bl_label = "Set uv_group for bedrock model."
    bl_options = {'UNDO'}
    bl_description = (
        "Set uv_group for bedrock model. Objects that have the same width, "
        "depth and height and are in the same uv_group are mapped to the "
        "same spot on the texutre"
    )

    def list_uv_groups(self, context):
        items = [
            (x.name, x.name, x.name)
            for x in bpy.context.scene.nusiq_mcblend_uv_groups]
        return items
    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=list_uv_groups, name="UV Groups")

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 0:
            return False
        if len(bpy.context.scene.nusiq_mcblend_uv_groups) == 0:
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        context.object.nusiq_mcblend_object_properties.uv_group = (
            self.uv_groups_enum)
        return {'FINISHED'}


# Toogle mirror
class OBJECT_OT_NusiqMcblendToggleMirrorOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called mirror for selected
    objects
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_toggle_mirror_operator"
    bl_label = "Toggle mirror for selected objects."
    bl_options = {'UNDO'}
    bl_description = (
        "Toggle mirror for selected objects. Adds or removes mirror "
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
                if obj.nusiq_mcblend_object_properties.mirror:
                    is_clearing = True
                    break
        if is_clearing:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    (obj.nusiq_mcblend_object_properties
                        ).mirror = False
            self.report({'INFO'}, 'Disabled the mirror for generating UV for '
                'selected objects.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH":
                    (obj.nusiq_mcblend_object_properties
                        ).mirror = True
            self.report({'INFO'}, 'Enabled the mirror for generating UV for '
                'selected objects.')
        return {'FINISHED'}


# Toggle is_bone
class OBJECT_OT_NusiqMcblendToggleIsBoneOperator(bpy.types.Operator):
    '''
    Operator used for toggling custom property called is_bone for selected
    objects.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_toggle_is_bone_operator"
    bl_label = "Toggle is_bone for selected objects."
    bl_options = {'UNDO'}
    bl_description = (
        "Toggles is_bone for selected objects. Setting is_bone property "
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
                if obj.nusiq_mcblend_object_properties.is_bone:
                    is_clearing = True
                    break
        if is_clearing:
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    obj.nusiq_mcblend_object_properties.is_bone = False
            self.report(
                {'INFO'}, 'Objects are not market to export as bones anymore.')
        else:
            for obj in context.selected_objects:
                if obj.type == "MESH" or obj.type == "EMPTY":
                    obj.nusiq_mcblend_object_properties.is_bone = True
            self.report({'INFO'}, 'Marked slected objects to export as bones')

        return {'FINISHED'}


# Inflate
class OBJECT_OT_NusiqMcblendSetInflateOperator(bpy.types.Operator):
    '''
    Operator used for setting the inflate value of selected objects. It changes
    the dimensions of selected object and adds custom property called inflate.
    '''
    # pylint: disable=C0116, W0613, no-member
    bl_idname = "object.nusiq_mcblend_set_inflate_operator"
    bl_label = "Set inflate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Set the inflate vale for selected objects and change their "
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
    bl_options = {'UNDO'}
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
        maxlen=500,
        name='Geometry name'
    )

    replace_bones_with_empties: BoolProperty(  # type: ignore
        default=False,
        description='Creates empties instead of armature and bones',
        name='Replace bones with empties'
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

# Animation GUI
def save_animation_frame_properties(animation, context):
    '''Helper function for saving animation when its changed in GUI'''
    animation.frame_start = context.scene.frame_start
    animation.frame_end = context.scene.frame_end
    animation.frame_current = context.scene.frame_current

def load_animation_frame_properties(animation, context):
    '''Helper function for loading animation when its changed in GUI'''
    context.scene.frame_start = animation.frame_start
    context.scene.frame_end = animation.frame_end
    context.scene.frame_current = animation.frame_current

class OBJECT_OT_NusiqMcblendListAnimations(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_list_animations"
    bl_label = "List animations and save them to Enum to display them in GUI"

    def list_animations(self, context):
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(bpy.context.scene.nusiq_mcblend_animations)]
        return items

    animations_enum: bpy.props.EnumProperty(  # type: ignore
        items=list_animations, name="Animations")

    # @classmethod
    # def poll(cls, context):
    #     return context.mode == 'OBJECT'
    
    def execute(self, context):
        '''
        Runs when user picks an item from the dropdown menu in animations
        panel. Sets the active animation.
        '''
        # If OK than save old animation state
        len_anims = len(context.scene.nusiq_mcblend_animations)
        curr_anim_id = context.scene.nusiq_mcblend_active_animation
        if curr_anim_id >= 0 and curr_anim_id < len_anims:
            save_animation_frame_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)

        # Set new animation and load its state
        new_anim_id=int(self.animations_enum)
        context.scene.nusiq_mcblend_active_animation=new_anim_id
        load_animation_frame_properties(
                context.scene.nusiq_mcblend_animations[new_anim_id], context)
        return {'FINISHED'}


class OBJECT_OT_NusiqMcblendAddAnimation(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_add_animation"
    bl_label = '''Adds new animation to the list.'''
    bl_options = {'UNDO'}

    def execute(self, context):
        # If OK save old animation
        len_anims = len(context.scene.nusiq_mcblend_animations)
        curr_anim_id = context.scene.nusiq_mcblend_active_animation
        if 0 <= curr_anim_id and curr_anim_id < len_anims:
            save_animation_frame_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)

        # Add new animation and set its properties
        animation_new = context.scene.nusiq_mcblend_animations.add()
        len_anims = len(context.scene.nusiq_mcblend_animations)
        context.scene.nusiq_mcblend_active_animation=len_anims-1
        animation_new.name = f'animation{len_anims}'

        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendRemoveAnimation(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_remove_animation"
    bl_label = "Remove current animation from the list."
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.nusiq_mcblend_animations) > 0

    def execute(self, context):
        # Remove animation
        context.scene.nusiq_mcblend_animations.remove(
            context.scene.nusiq_mcblend_active_animation)

        # Set new active animation
        last_active=context.scene.nusiq_mcblend_active_animation
        len_anims=len(context.scene.nusiq_mcblend_animations)
        if last_active > 0:
            context.scene.nusiq_mcblend_active_animation=last_active-1

        # Load data from new active animation
        curr_anim_id=context.scene.nusiq_mcblend_active_animation
        if 0 >= curr_anim_id and curr_anim_id < len_anims:
            load_animation_frame_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)
        return {'FINISHED'}

# UV group GUI
class OBJECT_OT_NusiqMcblendListUvGroups(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_list_uv_groups"
    bl_label = "List UV groups and save them to Enum to display them in GUI"

    def list_uv_groups(self, context):
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(bpy.context.scene.nusiq_mcblend_uv_groups)]
        return items

    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=list_uv_groups, name="UV Groups")

    def execute(self, context):
        '''
        Runs when user picks an item from the dropdown menu in uv_groups
        panel. Sets the active animation.
        '''
        # If OK than save old animation state
        len_uv_groups = len(context.scene.nusiq_mcblend_uv_groups)
        curr_uv_group_id = context.scene.nusiq_mcblend_active_uv_group

        # Set new uv_group and load its state
        new_uv_group_id=int(self.uv_groups_enum)
        context.scene.nusiq_mcblend_active_uv_group=new_uv_group_id

        # TODO - Load uv group properties
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendAddUvGroup(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_add_uv_group"
    bl_label = '''Adds new uv_group to the list.'''
    bl_options = {'UNDO'}

    def execute(self, context):
        # If OK save old uv_group
        len_groups = len(context.scene.nusiq_mcblend_uv_groups)

        # Add new uv_group and set its properties
        uv_group_new = context.scene.nusiq_mcblend_uv_groups.add()
        len_groups = len(context.scene.nusiq_mcblend_uv_groups)
        context.scene.nusiq_mcblend_active_uv_group=len_groups-1

        uv_group_new.name = get_unused_uv_group_name('uv_group')
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendRemoveUvGroup(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_remove_uv_group"
    bl_label = "Remove current uv_group from the list."
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.nusiq_mcblend_uv_groups) > 0

    def execute(self, context):
        group_id = context.scene.nusiq_mcblend_active_uv_group
        group_name = context.scene.nusiq_mcblend_uv_groups[group_id].name
        # Remove uv_group
        context.scene.nusiq_mcblend_uv_groups.remove(group_id)
        

        # Update the names of all of the meshes
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                obj_props = obj.nusiq_mcblend_object_properties
                if obj_props.uv_group == group_name:
                    obj_props.uv_group = ''

        # Set new active uv_group
        len_uv_groups=len(context.scene.nusiq_mcblend_uv_groups)
        if group_id > 0:
            context.scene.nusiq_mcblend_active_uv_group=group_id-1

        # Load data from new active uv_group
        curr_uv_group_id=context.scene.nusiq_mcblend_active_uv_group
        return {'FINISHED'}

# class OBJECT_OT_NusiqMcblendRenameUvGroup(bpy.types.Operator):
#     bl_idname = "object.nusiq_mcblend_rename_uv_group"
#     bl_label = "Rename current uv_group from the list."
#     bl_options = {'UNDO'}

#     new_name: bpy.props.StringProperty(  # type: ignore
#         name='Name', description='New name of the UV group', maxlen=1024
#     )

#     @classmethod
#     def poll(cls, context):
#         return len(context.scene.nusiq_mcblend_uv_groups) > 0

#     def invoke(self, context, event):
#         return context.window_manager.invoke_props_dialog(self)

#     def update_uv_group_name(self, uv_group, new_name: str):
#         # Update the names of all of the meshes
#         for obj in bpy.data.objects:
#             if obj.type == "MESH":
#                 obj_props = obj.nusiq_mcblend_object_properties
#                 if obj_props.uv_group == uv_group.name:
#                     obj_props.uv_group = new_name
#         # Update the name of the UV group
#         uv_group.name = new_name

#     def execute(self, context):
#         groups = context.scene.nusiq_mcblend_uv_groups
#         this_group_index = context.scene.nusiq_mcblend_active_uv_group
#         this_group = groups[this_group_index]

        
#         # Empty name is no allowed
#         if self.new_name == '':
#             self.report({'WARNING'}, "Invalid name (empty string).")
#             return {'CANCELLED'}

#         # If name already in use rename the other uv group
#         for other_group in groups:
#             if (  # Change the of the duplicate if there is one
#                     other_group.path_from_id() != this_group.path_from_id() and
#                     other_group.name == self.new_name):
#                 # Get starting name index
#                 i = 1
#                 base_name = self.new_name
#                 split_name = self.new_name.split('.')
#                 try:
#                     prev_i = int(split_name[-1])
#                     i = i if prev_i <= 0 else prev_i
#                     base_name = '.'.join(split_name[:-1])
#                 except ValueError:
#                     pass
#                 other_new_name = get_unused_uv_group_name(base_name, i)
#                 self.update_uv_group_name(other_group, other_new_name)
#                 break
#         self.update_uv_group_name(this_group, self.new_name)
#         return {'FINISHED'}

# UV Group -> UV Mask (GUI)

def get_active_masks(context):
    '''
    Helper function for getting access to active UV Group -> Masks
    '''
    curr_group_id = context.scene.nusiq_mcblend_active_uv_group
    curr_group = context.scene.nusiq_mcblend_uv_groups[curr_group_id]
    sides = [
        curr_group.side1, curr_group.side2,
        curr_group.side3, curr_group.side4,
        curr_group.side5, curr_group.side6
    ]
    masks = sides[int(context.scene.nusiq_mcblend_active_uv_groups_side)]
    return masks

class OBJECT_OT_NusiqMcblendAddUvMask(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_add_uv_mask"
    bl_label = '''Adds new mask to active uv group at active face.'''
    bl_options = {'UNDO'}

    mask_type: EnumProperty(  # type: ignore
        items=list_mask_types_as_blender_enum, name='Mask type'
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        new_mask = masks.add()
        new_mask.mask_type = self.mask_type
        new_mask.colors.add()
        new_mask.stripes.add()
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendRemoveUvMask(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_remove_uv_mask"
    bl_label = '''Removes mask from active face of active uv group.'''
    bl_options = {'UNDO'}

    target: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        masks.remove(self.target)
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendMoveUvMask(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_move_uv_mask"
    bl_label = (
        'Moves mask in active face of active uv group to different place on '
        'the list.')
    bl_options = {'UNDO'}

    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        masks.move(self.move_from, self.move_to)
        return {'FINISHED'}

# UV Group -> UV Mask -> side -> colors (GUI)
class OBJECT_OT_NusiqMcblendAddUvMaskColor(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_add_uv_mask_color"
    bl_label = '''Adds new color to a mask.'''
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.colors.add()
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendRemoveUvMaskColor(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_remove_uv_mask_color"
    bl_label = 'Removes color from colors of active face of active uv group.'
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore
    color_index: IntProperty()  # type: ignore


    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.colors.remove(self.color_index)
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendMoveUvMaskColor(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_move_uv_mask_color"
    bl_label = (
        'Moves color in active mask of active face  of active uv group to'
        'different place on the list.')
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore
    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.colors.move(self.move_from, self.move_to)
        return {'FINISHED'}

# UV Group -> UV Mask -> side -> stripes (GUI)
class OBJECT_OT_NusiqMcblendAddUvMaskStripe(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_add_uv_mask_stripe"
    bl_label = '''Adds new color to a mask.'''
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.stripes.add()
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendRemoveUvMaskStripe(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_remove_uv_mask_stripe"
    bl_label = 'Removes color from colors of active face of active uv group.'
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore
    stripe_index: IntProperty()  # type: ignore


    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.stripes.remove(self.stripe_index)
        return {'FINISHED'}

class OBJECT_OT_NusiqMcblendMoveUvMaskStripe(bpy.types.Operator):
    bl_idname = "object.nusiq_mcblend_move_uv_mask_stripe"
    bl_label = (
        'Moves color in active mask of active face  of active uv group to'
        'different place on the list.')
    bl_options = {'UNDO'}

    mask_index: IntProperty()  # type: ignore
    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if len(context.scene.nusiq_mcblend_uv_groups) < 1:
            return False
        return True

    def execute(self, context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]
        mask.stripes.move(self.move_from, self.move_to)
        return {'FINISHED'}
