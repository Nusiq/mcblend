'''
This module contains all of the operators.
'''
# don't import future annotations Blender needs that
import json
from json.decoder import JSONDecodeError
from typing import Any, List, Optional, Dict

import bpy_types
import bpy
from bpy.props import (
    StringProperty, FloatProperty, EnumProperty, BoolProperty, IntProperty)
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .custom_properties import (
    get_unused_event_name, list_effect_types_as_blender_enum)
from .operator_func import (
    export_model, export_animation, separate_mesh_cubes, set_uvs, round_dimensions,
    import_model, inflate_objects)
from .operator_func.json_tools import CompactEncoder
from .operator_func.exception import (
    NameConflictException, NotEnoughTextureSpace,)
from .operator_func.jsonc_decoder import JSONCDecoder
from .operator_func.texture_generator import (
    list_mask_types_as_blender_enum, UvMaskTypes, MixMaskMode)

from .custom_properties import get_unused_uv_group_name

# Model exporter
class NUSIQ_MCBLEND_OT_ExportModel(
        bpy.types.Operator, ExportHelper):
    '''Operator used for exporting minecraft models from blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.export_model"
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
        bpy.ops.screen.animation_cancel()
        original_frame = context.scene.frame_current
        try:
            context.scene.frame_set(0)
            for obj in context.selected_objects:
                if obj.type == 'MESH' and any(map(lambda x: x < 0, obj.scale)):
                    self.report(
                        {'ERROR'},
                        "Negative object scale is not supported. "
                        f"Object: {obj.name}; Frame: 0.")
                    return {'FINISHED'}
            result = export_model(context)
        except NameConflictException as e:
            self.report({'WARNING'}, str(e))
            return {'FINISHED'}
        finally:
            context.scene.frame_set(original_frame)

        with open(self.filepath, 'w') as f:
            json.dump(result, f, cls=CompactEncoder)

        self.report({'INFO'}, f'Model saved in {self.filepath}.')
        return {'FINISHED'}

def menu_func_nusiq_mcblend_export_model(self, context):
    '''Registers ExportModel operator to the F3 menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(
        NUSIQ_MCBLEND_OT_ExportModel.bl_idname,
        text="Mcblend: Export model"
    )

# Animation exporter
class NUSIQ_MCBLEND_OT_ExportAnimation(
        bpy.types.Operator, ExportHelper):
    '''Operator used for exporting Minecraft animations from blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.export_animation"
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
        if 0 > curr_anim_id >= len_anims:
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
    '''Registers ExportAnimation operator to the F3 menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(
        NUSIQ_MCBLEND_OT_ExportAnimation.bl_idname,
        text="Mcblend: Export animation"
    )

# UV mapper
class NUSIQ_MCBLEND_OT_MapUv(bpy.types.Operator):
    '''
    Operator used for creating UV-mapping and optionally the tamplate texture
    for Minecraft model.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.map_uv"
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
        bpy.ops.screen.animation_cancel()
        original_frame = context.scene.frame_current
        try:
            context.scene.frame_set(0)
            for obj in context.selected_objects:
                if obj.type == 'MESH' and any(map(lambda x: x < 0, obj.scale)):
                    self.report(
                        {'ERROR'},
                        "Negative object scale is not supported. "
                        f"Object: {obj.name}; Frame: 0.")
                    return {'FINISHED'}
            set_uvs(context)
        except NotEnoughTextureSpace:
            self.report(
                {'ERROR'},
                "Not enough texture space to create UV-mapping.")
            return {'FINISHED'}
        except NameConflictException as e:
            self.report({'WARNING'}, str(e))
            return {'FINISHED'}
        finally:
            context.scene.frame_set(original_frame)

        width = context.scene.nusiq_mcblend.texture_width
        height = context.scene.nusiq_mcblend.texture_height
        self.report(
            {'INFO'},
            f'UV map created successfully for {width}x{height} texture.'
        )
        return {'FINISHED'}

# UV grouping
class NUSIQ_MCBLEND_OT_UvGroup(bpy.types.Operator):
    '''Operator used for adding selected objects to an UV-group'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.uv_group"
    bl_label = "Set uv_group for object."
    bl_options = {'UNDO'}
    bl_description = (
        "Set uv_group for bedrock model. Objects that have the same width, "
        "depth and height and are in the same uv_group are mapped to the "
        "same spot on the texture"
    )

    def _list_uv_groups(self, context):
        items = [
            (x.name, x.name, x.name)
            for x in bpy.context.scene.nusiq_mcblend_uv_groups]
        return items
    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        if len(bpy.context.scene.nusiq_mcblend_uv_groups) == 0:
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.nusiq_mcblend_object_properties.uv_group = (
                    self.uv_groups_enum)
        self.report(
            {'INFO'},
            f'Set UV group of selected objects to {self.uv_groups_enum}.')

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_ClearUvGroup(bpy.types.Operator):
    '''Operator used for removing selected objects from their UV-groups'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.clear_uv_group"
    bl_label = "Clear uv_group for object."
    bl_options = {'UNDO'}
    bl_description = 'Clears the UV group from an object.'

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        if len(bpy.context.scene.nusiq_mcblend_uv_groups) == 0:
            return False
        return True

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                obj.nusiq_mcblend_object_properties.uv_group = ''
        self.report({'INFO'}, 'Cleared UV group of selected objects.')

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# Mirror property
class NUSIQ_MCBLEND_OT_ToggleMirror(bpy.types.Operator):
    '''
    Operator used for toggling custom "mirror" propert of selected objects.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.toggle_mirror"
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

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# is_bone property
class NUSIQ_MCBLEND_OT_ToggleIsBone(bpy.types.Operator):
    '''
    Operator used for toggling custom "is_bone" property of selected objects.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.toggle_is_bone"
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
            self.report({'INFO'}, 'Marked selected objects to export as bones')

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# Inflate property
class NUSIQ_MCBLEND_OT_SetInflate(bpy.types.Operator):
    '''
    Operator used for setting the inflate value of selected objects.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.set_inflate"
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
        inflate_objects(
            context, context.selected_objects, self.inflate_value, self.mode)
        return {'FINISHED'}

# Rounding dimensions
class NUSIQ_MCBLEND_OT_RoundDimensions(bpy.types.Operator):
    '''
    Operator used for rounding the width, depth and height of selected objects
    in such way that they'll have integer dimensions in exported Minecraft
    model file.
    '''
    # pylint: disable=unused-argument, R0201, no-member
    bl_idname = "nusiq_mcblend.round_dimensions"
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

# Separate mesh cubes
class NUSIQ_MCBLEND_OT_SeparateMeshCubes(bpy.types.Operator):
    '''
    Separates object with mesh full of cuboids by the loose parts of the mesh.
    Adjusts the rotations of the newly created objects to match the rotations
    of the cubes inside of this object.
    '''
    # pylint: disable=unused-argument, R0201, no-member
    bl_idname = "nusiq_mcblend.separate_mesh_cubes"
    bl_label = "Separate cubes"
    bl_options = {'UNDO'}
    bl_description = (
        "Separate cubes from selected objects and rotate bound boxes to "
        "minimize their size."
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context):
        separate_mesh_cubes(context)
        return {'FINISHED'}

# Model Importer
class NUSIQ_MCBLEND_OT_ImportModel(bpy.types.Operator, ImportHelper):
    '''Operator used for importing Minecraft models to Blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.import_model"
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

# Animation (GUI)
def menu_func_nusiq_mcblend_import_model(self, context):
    '''Registers Import operator to the F3 menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(
        NUSIQ_MCBLEND_OT_ImportModel.bl_idname, text="Mcblend: Import model"
    )

def save_animation_properties(animation, context):
    '''
    Saves animation properties from context to
    NUSIQ_MCBLEND_AnimationProperties object.
    '''
    animation.frame_start = context.scene.frame_start
    animation.frame_end = context.scene.frame_end
    animation.frame_current = context.scene.frame_current

    animation.timeline_markers.clear()
    for timeline_marker in context.scene.timeline_markers:
        anim_timeline_marker = animation.timeline_markers.add()
        anim_timeline_marker.name = timeline_marker.name
        anim_timeline_marker.frame = timeline_marker.frame

def load_animation_properties(animation, context):
    '''
    Saves animation properties from NUSIQ_MCBLEND_AnimationProperties
    object to the context.
    '''
    context.scene.frame_start = animation.frame_start
    context.scene.frame_end = animation.frame_end
    context.scene.frame_current = animation.frame_current

    context.scene.timeline_markers.clear()
    for anim_timeline_marker in animation.timeline_markers:
        context.scene.timeline_markers.new(
            anim_timeline_marker.name,
            frame=anim_timeline_marker.frame)

class NUSIQ_MCBLEND_OT_ListAnimations(bpy.types.Operator):
    '''
    Operator used for listing the animations for GUI.
    '''
    bl_idname = "nusiq_mcblend.list_animations"
    bl_label = "List animations and save them to Enum to display them in GUI"

    def _list_animations(self, context):
        # pylint: disable=unused-argument
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(bpy.context.scene.nusiq_mcblend_animations)]
        return items

    animations_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_animations, name="Animations")

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
        if 0 <= curr_anim_id < len_anims:
            save_animation_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)

        # Set new animation and load its state
        new_anim_id=int(self.animations_enum)
        context.scene.nusiq_mcblend_active_animation=new_anim_id
        load_animation_properties(
                context.scene.nusiq_mcblend_animations[new_anim_id], context)
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_AddAnimation(bpy.types.Operator):
    '''Operator used creating animation settings templates.'''
    bl_idname = "nusiq_mcblend.add_animation"
    bl_label = '''Adds new animation to the list.'''
    bl_options = {'UNDO'}

    def execute(self, context):
        # If OK save old animation
        len_anims = len(context.scene.nusiq_mcblend_animations)
        curr_anim_id = context.scene.nusiq_mcblend_active_animation
        if 0 <= curr_anim_id < len_anims:
            save_animation_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)
            context.scene.timeline_markers.clear()

        # Add new animation and set its properties
        animation_new = context.scene.nusiq_mcblend_animations.add()
        len_anims = len(context.scene.nusiq_mcblend_animations)
        context.scene.nusiq_mcblend_active_animation=len_anims-1
        animation_new.name = f'animation{len_anims}'

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_RemoveAnimation(bpy.types.Operator):
    '''
    Operator used for loading saved animation templates to the context.
    '''
    bl_idname = "nusiq_mcblend.remove_animation"
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
        if 0 <= curr_anim_id < len_anims:
            load_animation_properties(
                context.scene.nusiq_mcblend_animations[curr_anim_id], context)

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# UV group (GUI)
class NUSIQ_MCBLEND_OT_ListUvGroups(bpy.types.Operator):
    '''
    Operator that used for listing the UV-groups for GUI.
    '''
    bl_idname = "nusiq_mcblend.list_uv_groups"
    bl_label = "List UV groups and save them to Enum to display them in GUI"

    def _list_uv_groups(self, context):
        # pylint: disable=unused-argument
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(bpy.context.scene.nusiq_mcblend_uv_groups)]
        return items

    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")

    def execute(self, context):
        '''
        Runs when user picks an item from the dropdown menu in uv_groups
        panel. Sets the active uv_group.
        '''
        # Set new uv_group and load its state
        new_uv_group_id=int(self.uv_groups_enum)
        context.scene.nusiq_mcblend_active_uv_group=new_uv_group_id

        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_AddUvGroup(bpy.types.Operator):
    '''Operator used for creating new UV-groups.'''
    bl_idname = "nusiq_mcblend.add_uv_group"
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
        sides = [
            uv_group_new.side1, uv_group_new.side2, uv_group_new.side3,
            uv_group_new.side4, uv_group_new.side5, uv_group_new.side6]
        colors = [
            (0, 0.15, 0), (0.15, 0, 0.15), (0.15, 0, 0),
            (0, 0.15, 0.15), (0, 0, 0.15), (0.15, 0.15, 0)]
        for color, side in zip(colors, sides):
            mask = side.add()
            mask.mask_type = UvMaskTypes.COLOR_MASK.value
            mask.color.color = color
            mask.colors.add()
            mask.stripes.add()

        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_RemoveUvGroup(bpy.types.Operator):
    '''Operator useful for removing UV-groups.'''
    bl_idname = "nusiq_mcblend.remove_uv_group"
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
        if group_id > 0:
            context.scene.nusiq_mcblend_active_uv_group=group_id-1
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_CopyUvGroupSide(bpy.types.Operator):
    '''Operator used for copying sides of UV-groups.'''
    bl_idname = "nusiq_mcblend.copy_uv_group_side"
    bl_label = 'Copy active UV group side other to UV group'
    bl_options = {'UNDO'}

    def _list_uv_groups(self, context):
        # pylint: disable=unused-argument
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(bpy.context.scene.nusiq_mcblend_uv_groups)]
        return items

    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")
    side1: BoolProperty(name='side1')  # type: ignore
    side2: BoolProperty(name='side2')  # type: ignore
    side3: BoolProperty(name='side3')  # type: ignore
    side4: BoolProperty(name='side4')  # type: ignore
    side5: BoolProperty(name='side5')  # type: ignore
    side6: BoolProperty(name='side6')  # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context):
        return len(context.scene.nusiq_mcblend_uv_groups) >= 1

    def _copy_side(
            self, context,
            source_group_id: int, source_side_id: int,
            target_group_id: int, target_side_id: int):
        if (
            source_group_id == target_group_id and
            source_side_id == target_side_id
        ):
            return  # If source and target is the same don't do anything
        # Get source
        source_group = context.scene.nusiq_mcblend_uv_groups[source_group_id]
        source_sides = [
            source_group.side1, source_group.side2,
            source_group.side3, source_group.side4,
            source_group.side5, source_group.side6]
        source_masks = source_sides[source_side_id]
        # Get target
        target_group = context.scene.nusiq_mcblend_uv_groups[target_group_id]
        target_sides = [
            target_group.side1, target_group.side2,
            target_group.side3, target_group.side4,
            target_group.side5, target_group.side6]
        target_masks = target_sides[target_side_id]
        # Clear target
        target_masks.clear()
        # Copy from source from target
        for mask in source_masks:
            new_mask = target_masks.add()
            new_mask.mask_type = mask.mask_type
            for color in mask.colors:
                new_color = new_mask.colors.add()
                new_color.color = color.color
            new_mask.interpolate = mask.interpolate
            new_mask.normalize = mask.normalize

            new_mask.p1_relative = mask.p1_relative
            new_mask.p2_relative = mask.p2_relative
            new_mask.p1 = mask.p1
            new_mask.p2 = mask.p2
            for stripe in mask.stripes:
                new_stripe = new_mask.stripes.add()
                new_stripe.width = stripe.width
                new_stripe.strength = stripe.strength
            new_mask.relative_boundaries = mask.relative_boundaries
            new_mask.expotent = mask.expotent
            new_mask.strength = mask.strength
            new_mask.hard_edge = mask.hard_edge
            new_mask.horizontal = mask.horizontal
            new_mask.use_seed = mask.use_seed
            new_mask.seed = mask.seed
            new_mask.color.color = mask.color.color  # pointer property
            new_mask.mode = mask.mode
            new_mask.children = mask.children

    def execute(self, context):
        # Get source masks
        source_group_id = context.scene.nusiq_mcblend_active_uv_group
        source_side_id = int(context.scene.nusiq_mcblend_active_uv_groups_side)

        # Get target UV group
        target_group_id = int(self.uv_groups_enum)

        if self.side1:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 0)
        if self.side2:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 1)
        if self.side3:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 2)
        if self.side4:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 3)
        if self.side5:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 4)
        if self.side6:
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 5)
        self.report({'INFO'}, 'Successfully copied UV face.')
        return {'FINISHED'}

# UV Mask (GUI)
def get_active_masks(context):
    '''Returns active masks of active UV Group from context.'''
    curr_group_id = context.scene.nusiq_mcblend_active_uv_group
    curr_group = context.scene.nusiq_mcblend_uv_groups[curr_group_id]
    sides = [
        curr_group.side1, curr_group.side2,
        curr_group.side3, curr_group.side4,
        curr_group.side5, curr_group.side6
    ]
    masks = sides[int(context.scene.nusiq_mcblend_active_uv_groups_side)]
    return masks

class NUSIQ_MCBLEND_OT_AddUvMask(bpy.types.Operator):
    '''Operator used for adding UV-masks to UV groups.'''
    bl_idname = "nusiq_mcblend.add_uv_mask"
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

class NUSIQ_MCBLEND_OT_RemoveUvMask(bpy.types.Operator):
    '''Operator used for removing UV-masks from UV-groups.'''
    bl_idname = "nusiq_mcblend.remove_uv_mask"
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

class NUSIQ_MCBLEND_OT_MoveUvMask(bpy.types.Operator):
    '''Operator used for changing the order of UV-masks in UV groups.'''
    bl_idname = "nusiq_mcblend.move_uv_mask"
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

# UV Mask side colors (GUI)
class NUSIQ_MCBLEND_OT_AddUvMaskColor(bpy.types.Operator):
    '''Operator used for adding colors to UV-masks.'''
    bl_idname = "nusiq_mcblend.add_uv_mask_color"
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

class NUSIQ_MCBLEND_OT_RemoveUvMaskColor(bpy.types.Operator):
    '''Operator used for removing colors from UV-masks.'''
    bl_idname = "nusiq_mcblend.remove_uv_mask_color"
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

class NUSIQ_MCBLEND_OT_MoveUvMaskColor(bpy.types.Operator):
    '''Operator used for changing the order of the colors in UV-masks.'''
    bl_idname = "nusiq_mcblend.move_uv_mask_color"
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

# UV Mask side stripes (GUI)
class NUSIQ_MCBLEND_OT_AddUvMaskStripe(bpy.types.Operator):
    '''Operator used for adding stripes to UV-masks.'''
    bl_idname = "nusiq_mcblend.add_uv_mask_stripe"
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

class NUSIQ_MCBLEND_OT_RemoveUvMaskStripe(bpy.types.Operator):
    '''Operator used for removing UV-masks from UV-groups.'''
    bl_idname = "nusiq_mcblend.remove_uv_mask_stripe"
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

class NUSIQ_MCBLEND_OT_MoveUvMaskStripe(bpy.types.Operator):
    '''Operator used for changing the order of the stripes in UV-groups.'''
    bl_idname = "nusiq_mcblend.move_uv_mask_stripe"
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

# UV Mask exporter
class NUSIQ_MCBLEND_OT_ExportUvGroup(
        bpy.types.Operator, ExportHelper):
    '''Operator used for exporting active UV-group from Blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "nusiq_mcblend.export_uv_group"
    bl_label = "Export UV-group"
    bl_options = {'REGISTER'}
    bl_description = "Exports active UV-group"

    filename_ext = '.uvgroup.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.uvgroup.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        return len(context.scene.nusiq_mcblend_uv_groups) > 0

    def execute(self, context):
        group_id = context.scene.nusiq_mcblend_active_uv_group
        uv_group = context.scene.nusiq_mcblend_uv_groups[group_id]

        with open(self.filepath, 'w') as f:
            json.dump(uv_group.json(), f, cls=CompactEncoder)
        self.report({'INFO'}, f'UV-group saved in {self.filepath}.')
        return {'FINISHED'}

# UV Mask exporter
class NUSIQ_MCBLEND_OT_ImportUvGroup(bpy.types.Operator, ImportHelper):
    '''Operator used for importing Minecraft models to Blender.'''
    # pylint: disable=unused-argument, no-member, too-many-boolean-expressions
    bl_idname = "nusiq_mcblend.import_uv_group"
    bl_label = "Import UV-group"
    bl_options = {'REGISTER'}
    bl_description = "Import UV-group from JSON file."
    # ImportHelper mixin class uses this
    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore
        default="*.json",
        options={'HIDDEN'},
        maxlen=1000,
    )

    def _load_mask_data(self, mask_data, side) -> Optional[str]:
        # pylint: disable=too-many-boolean-expressions, too-many-nested-blocks
        loading_warning: Optional[str] = None
        if "mask_type" not in mask_data:
            return (
                "Some of the masks are missing the 'mask_type' definition.")
        mask_type = mask_data["mask_type"]
        if not isinstance(mask_type, str):
            return  (
                f"Mask type property must be a string not a {type(mask_type)}")
        if mask_type not in [m.value for m in UvMaskTypes]:
            return f'Unknown mask type: {mask_type}'
        mask=side.add()
        mask.mask_type = mask_type

        # Loading properties of the mask
        # Loading relative_boundaries first because they affect other properties
        relative_boundaries: bool = False
        if mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value,
                UvMaskTypes.STRIPES_MASK.value]:
            if 'relative_boundaries' in mask_data:
                if isinstance(mask_data['relative_boundaries'], bool):
                    relative_boundaries = mask_data['relative_boundaries']
                    mask.relative_boundaries = relative_boundaries
                else:
                    loading_warning = (
                        '"relative_boundaries" property must be a boolean')
        if mask_type == UvMaskTypes.MIX_MASK.value:
            if 'mode' in mask_data:
                mode = mask_data['mode']
                if mode not in [m.value for m in MixMaskMode]:
                    loading_warning=f'Unknown mode {mode}'
                else:
                    mask.mode = mode
            if 'children' in mask_data:
                children = mask_data['children']
                if not isinstance(children, int):
                    loading_warning = 'Children property must be an integer'
                else:
                    mask.children = mask_data['children']
        if mask_type == UvMaskTypes.COLOR_PALLETTE_MASK.value:
            if 'colors' in mask_data:
                colors = mask_data['colors']
                if not isinstance(colors, list):
                    loading_warning = (
                        'Colors property must be a list of lists of floats')
                else:
                    for color_data in colors:
                        if (
                                not isinstance(color_data, list) or
                                len(color_data) != 3):
                            loading_warning = (
                                'Every color on colors list should be '
                                'a list of floats.')
                            continue
                        is_color = True
                        for value_data in color_data:
                            if not isinstance(value_data, (float, int)):
                                is_color = False
                                loading_warning =(
                                    'All values of color must be '
                                    'floats in range 0.0-1.0')
                                break
                        if is_color:
                            color = mask.colors.add()
                            color.color = color_data
            if 'interpolate' in mask_data:
                interpolate = mask_data['interpolate']
                if not isinstance(interpolate, bool):
                    loading_warning = 'Interpolate property must be a boolean'
                else:
                    mask.interpolate = interpolate
            if 'normalize' in mask_data:
                normalize = mask_data['normalize']
                if not isinstance(normalize, bool):
                    loading_warning = 'Normalize property must be a boolean'
                else:
                    mask.normalize = normalize
        if mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value]:
            if relative_boundaries:
                if 'p1' in mask_data:
                    if (
                            isinstance(mask_data['p1'], list) and
                            len(mask_data['p1']) == 2 and
                            isinstance(mask_data['p1'][0], (float, int)) and
                            isinstance(mask_data['p1'][1], (float, int)) and
                            0.0 <= mask_data['p1'][0] <= 1.0 and
                            0.0 <= mask_data['p1'][1] <= 1.0):
                        mask.p1_relative = mask_data['p1']
                    else:
                        loading_warning = (
                            '"p1" property must be a float in range 0.0 to '
                            '1.0 if "relative_boundaries" are True')
                if 'p2' in mask_data:
                    if (
                            isinstance(mask_data['p2'], list) and
                            len(mask_data['p2']) == 2 and
                            isinstance(mask_data['p2'][0], (float, int)) and
                            isinstance(mask_data['p2'][1], (float, int)) and
                            0.0 <= mask_data['p2'][0] <= 1.0 and
                            0.0 <= mask_data['p2'][1] <= 1.0):
                        mask.p2_relative = mask_data['p2']
                    else:
                        loading_warning = (
                            '"p2" property must be a float in range 0.0 to '
                            '1.0 if "relative_boundaries" are True')
            else:
                if 'p1' in mask_data:
                    if (
                            isinstance(mask_data['p1'], list) and
                            len(mask_data['p1']) == 2 and
                            isinstance(mask_data['p1'][0], int) and
                            isinstance(mask_data['p1'][1], int)):
                        mask.p1 = mask_data['p1']
                    else:
                        loading_warning = (
                            '"p1" property must be an integer if '
                            '"relative_boundaries" are False')
                if 'p2' in mask_data:
                    if (
                            isinstance(mask_data['p2'], list) and
                            len(mask_data['p2']) == 2 and
                            isinstance(mask_data['p2'][0], int) and
                            isinstance(mask_data['p2'][1], int)):
                        mask.p2 = mask_data['p2']
                    else:
                        loading_warning = (
                            '"p2" property must be an integer if '
                            '"relative_boundaries" are False')
        if mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.STRIPES_MASK.value]:
            if 'stripes' in mask_data:
                stripes = mask_data['stripes']
                if not isinstance(stripes, list):
                    loading_warning = '"stripes" property must be a list.'
                else:
                    for stripe_data in stripes:
                        if not isinstance(stripe_data, dict):
                            loading_warning = (
                                'Every stripe in the stripes list must be an '
                                'object')
                            continue
                        stripe = mask.stripes.add()
                        if 'width' in stripe_data:
                            width = stripe_data['width']
                            if relative_boundaries:
                                if (
                                        isinstance(width, (float, int)) and
                                        0.0 <= width <= 1.0):
                                    stripe.width_relative = width
                                else:
                                    loading_warning = (
                                        "Stripe width must be a float in "
                                        "range 0.0 to 1.0 if "
                                        "relative_boundaries is True")
                            else:
                                if isinstance(width, int):
                                    stripe.width = width
                                else:
                                    loading_warning = (
                                        "Stripe width must be an integer if "
                                        "relative_boundaries is True")
                        if 'strength' in stripe_data:
                            strength = stripe_data['strength']
                            if isinstance(strength, (float, int)):
                                stripe.strength = strength
                            else:
                                loading_warning = (
                                    'Stripe strength must be a float.')
        if mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value, UvMaskTypes.MIX_MASK.value,
                UvMaskTypes.RANDOM_MASK.value]:
            if 'expotent' in mask_data:
                expotent = mask_data['expotent']
                if isinstance(expotent, (float, int)):
                    mask.expotent = mask_data['expotent']
                else:
                    loading_warning = 'Expotent property must be a float.'
        if mask_type in [
                UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value, UvMaskTypes.MIX_MASK.value,
                UvMaskTypes.RANDOM_MASK.value]:
            if 'strength' in mask_data:
                strength = mask_data['strength']
                if (
                        isinstance(strength, list) and len(strength) == 2 and
                        isinstance(strength[0], (float, int)) and
                        isinstance(strength[1], (float, int)) and
                        0.0 <= strength[0] <= 1.0 and
                        0.0 <= strength[1] <= 1.0):
                    mask.strength = mask_data['strength']
                else:
                    loading_warning = (
                        '"strength" property must be a list of '
                        'two floats in range 0.0 to 1.0.')
        if mask_type in [
                UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value]:
            if 'hard_edge' in mask_data:
                if isinstance(mask_data['hard_edge'], bool):
                    hard_edge = mask_data['hard_edge']
                    mask.hard_edge = hard_edge
                else:
                    loading_warning = '"hard_edge" property must be a boolean'
        if mask_type == UvMaskTypes.STRIPES_MASK.value:
            if 'horizontal' in mask_data:
                if isinstance(mask_data['horizontal'], bool):
                    horizontal = mask_data['horizontal']
                    mask.horizontal = horizontal
                else:
                    loading_warning = '"horizontal" property must be a boolean'
        if mask_type == UvMaskTypes.RANDOM_MASK.value:
            if 'use_seed' in mask_data:
                if isinstance(mask_data['use_seed'], bool):
                    use_seed = mask_data['use_seed']
                    mask.use_seed = use_seed
                else:
                    loading_warning = '"use_seed" property must be a boolean'
            if 'seed' in mask_data:
                seed = mask_data['seed']
                if isinstance(seed, int):
                    mask.seed = mask_data['seed']
                else:
                    loading_warning = '"seed" property must be an interger.'
        if mask_type == UvMaskTypes.COLOR_MASK.value:
            if 'color' in mask_data:
                color_data = mask_data['color']
                if (
                        not isinstance(color_data, list) or
                        len(color_data) != 3):
                    loading_warning = (
                        'Every color on colors list should be '
                        'a list of floats.')
                else:
                    is_color = True
                    for value_data in color_data:
                        if not isinstance(value_data, (float, int)):
                            is_color = False
                            loading_warning =(
                                'All values of color must be '
                                'floats in range 0.0-1.0')
                            break
                    if is_color:
                        mask.color.color = color_data
        return loading_warning

    def _load_side(self, side: Any, side_data: List) -> Optional[str]:
        loading_warning = None
        for mask_data in side_data:
            loading_warning = self._load_mask_data(mask_data, side)
        return loading_warning

    def execute(self, context):
        name: str = get_unused_uv_group_name('uv_group')
        # Save file and finish
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f, cls=JSONCDecoder)
            version = data['version']
            if version != 1:
                self.report({'ERROR'}, "Unknown UV-group version.")
                return {'CANCELLED'}
        except (KeyError, TypeError, JSONDecodeError):
            self.report({'ERROR'}, "Unable to to read the UV-group data.")
            return {'CANCELLED'}

        # Create new UV-group
        len_groups = len(context.scene.nusiq_mcblend_uv_groups)
        # Add new uv_group and set its properties
        uv_group_new = context.scene.nusiq_mcblend_uv_groups.add()
        len_groups = len(context.scene.nusiq_mcblend_uv_groups)
        context.scene.nusiq_mcblend_active_uv_group=len_groups-1

        # Currently only version 1 is supported
        if 'name' in data and isinstance(data['name'], str):
            name =  get_unused_uv_group_name(data['name'])
        uv_group_new.name = name

        # Used for showing warnings about loading process (the loader shows
        # only one warning at a time)
        loading_warning: Optional[str] = None
        if 'side1' in data and isinstance(data['side1'], list):
            loading_warning=self._load_side(uv_group_new.side1, data['side1'])
        if 'side2' in data and isinstance(data['side2'], list):
            loading_warning=self._load_side(uv_group_new.side2, data['side2'])
        if 'side3' in data and isinstance(data['side3'], list):
            loading_warning=self._load_side(uv_group_new.side3, data['side3'])
        if 'side4' in data and isinstance(data['side4'], list):
            loading_warning=self._load_side(uv_group_new.side4, data['side4'])
        if 'side5' in data and isinstance(data['side5'], list):
            loading_warning=self._load_side(uv_group_new.side5, data['side5'])
        if 'side6' in data and isinstance(data['side6'], list):
            loading_warning=self._load_side(uv_group_new.side6, data['side6'])

        # If something didn't load propertly also display a warning
        if loading_warning is not None:
            self.report({'WARNING'}, loading_warning)

        if context.area is not None:  # There is no area when running from CLI
            context.area.tag_redraw()
        return {'FINISHED'}

# Events
class NUSIQ_MCBLEND_OT_AddEvent(bpy.types.Operator):
    '''Operator used for adding events to scene.'''
    bl_idname = "nusiq_mcblend.add_event"
    bl_label = '''Adds new event to scene.'''
    bl_options = {'UNDO'}

    def execute(self, context):
        event_new = bpy.context.scene.nusiq_mcblend_events.add()
        event_new.name = get_unused_event_name('event')
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_RemoveEvent(bpy.types.Operator):
    '''Operator used for removing events.'''
    bl_idname = "nusiq_mcblend.remove_event"
    bl_label = '''Removes event from scene.'''
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context: bpy_types.Context):
        events = bpy.context.scene.nusiq_mcblend_events
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        if not 0 <= active_event_id < len(events):
            return False
        return True

    def execute(self, context):
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        # Remove animation
        bpy.context.scene.nusiq_mcblend_events.remove(
            active_event_id)

        # Set new active event
        if active_event_id > 0:
            bpy.context.scene.nusiq_mcblend_active_event=active_event_id-1
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_AddEffect(bpy.types.Operator):
    '''Operator used for adding effects to events.'''
    bl_idname = "nusiq_mcblend.add_effect"
    bl_label = '''Adds new effect to active event.'''
    bl_options = {'UNDO'}

    effect_type: EnumProperty(  # type: ignore
        items=list_effect_types_as_blender_enum, name='Effect type'
    )

    @classmethod
    def poll(cls, context: bpy_types.Context):
        events = bpy.context.scene.nusiq_mcblend_events
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        if not 0 <= active_event_id < len(events):
            return False
        return True

    def execute(self, context):
        events = bpy.context.scene.nusiq_mcblend_events
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        event = events[active_event_id]

        effect = event.effects.add()
        effect.effect_type = self.effect_type
        return {'FINISHED'}

class NUSIQ_MCBLEND_OT_RemoveEffect(bpy.types.Operator):
    '''Operator used for removeing effects effects from events.'''
    bl_idname = "nusiq_mcblend.remove_effect"
    bl_label = '''Remove effect from active event.'''
    bl_options = {'UNDO'}

    effect_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: bpy_types.Context):
        events = bpy.context.scene.nusiq_mcblend_events
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        if not 0 <= active_event_id < len(events):
            return False
        event = events[active_event_id]
        effects = event.effects
        if len(effects) <= 0:
            return False
        return True

    def execute(self, context):
        events = bpy.context.scene.nusiq_mcblend_events
        active_event_id = bpy.context.scene.nusiq_mcblend_active_event
        event = events[active_event_id]
        event.effects.remove(self.effect_index)

        return {'FINISHED'}
