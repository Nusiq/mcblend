'''
This module contains all of the operators.
'''
# don't import future annotations Blender needs that
import json
from pathlib import Path
from json.decoder import JSONDecodeError
from typing import List, Optional, Dict, Any, Set, TYPE_CHECKING, cast

import bpy
from bpy.types import Operator, Context, Event
from bpy.props import (
    StringProperty, FloatProperty, EnumProperty, BoolProperty,  # type: ignore
    IntProperty  # type: ignore
)
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .object_data import (
    get_unused_event_name, list_effect_types_as_blender_enum,
    MCBLEND_AnimationProperties)
from .operator_func.typed_bpy_access import (
    get_mcblend_project,
    get_mcblend_events, get_mcblend_active_event,
    get_mcblend,
    set_mcblend_active_event,
    get_mcblend_uv_groups,
    set_mcblend_active_uv_group, get_mcblend_active_uv_group,
    get_mcblend_active_uv_groups_side)
from .uv_data import get_unused_uv_group_name
from .operator_func.material import MATERIALS_MAP

from .operator_func import (
    export_model, export_animation, fix_uvs, separate_mesh_cubes, set_uvs,
    import_model, inflate_objects, load_rp_to_mcblned, unload_rps,
    import_model_form_project, apply_materials, prepare_physics_simulation,
    merge_models)
from .operator_func.rp_importer import get_pks_for_model_improt
from .operator_func.sqlite_bedrock_packs.better_json_tools import (
    CompactEncoder, JSONCDecoder)
from .operator_func.exception import NotEnoughTextureSpace, ImporterException
from .operator_func.texture_generator import (
    list_mask_types_as_blender_enum, UvMaskTypes, MixMaskMode)
from .operator_func.extra_types import Vector3d

if TYPE_CHECKING:
    from .operator_func.pyi_types import CollectionProperty
    from .uv_data import MCBLEND_UvMaskProperties
else:
    CollectionProperty = List
    MCBLEND_UvMaskProperties = Any

# Model exporter
class MCBLEND_OT_ExportModel(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ExportHelper):
    '''Operator used for exporting Minecraft models from blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.export_model"
    bl_label = "Export Bedrock Model"
    bl_options = {'REGISTER'}
    bl_description = (
        "Export selected armature as a Minecraft Bedrock Edition model")

    filename_ext = '.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    if TYPE_CHECKING:
        filepath: str

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        bpy.ops.screen.animation_cancel()  # pyright: ignore[reportUnknownMemberType]
        original_frame = context.scene.frame_current
        warnings_counter = 0
        try:
            context.scene.frame_set(0)
            # TODO - implement this safety check in export_model
            # for obj in get_context_selected_objects(context):
            #     if obj.type == 'MESH' and any(map(lambda x: x < 0, obj.scale)):
            #         self.report(
            #             {'ERROR'},
            #             "Negative object scale is not supported. "
            #             f"Object: {obj.name}; Frame: 0.")
            #         return {'FINISHED'}
            result, warnings_generator = export_model(context)

            for warning in warnings_generator:
                self.report({'WARNING'}, warning)
                warnings_counter += 1

        finally:
            context.scene.frame_set(original_frame)

        with open(self.filepath, 'w', encoding='utf8') as f:
            json.dump(result, f, cls=CompactEncoder)
        if warnings_counter > 1:
            self.report(
                {'WARNING'},
                f"Model saved in {self.filepath} after exporting with "
                f"{warnings_counter} warnings. See logs for more details.")
        elif warnings_counter == 1:
            self.report(
                {'WARNING'},
                f"Model saved in {self.filepath} after exporting with 1 "
                "warning. See logs for more details.")
        else:
            self.report({'INFO'}, f'Model saved in {self.filepath}.')
        return {'FINISHED'}

def menu_func_mcblend_export_model(self: Any, context: Context):
    '''Used to register the operator in the file export menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(MCBLEND_OT_ExportModel.bl_idname)

# Animation exporter
class MCBLEND_OT_ExportAnimation(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ExportHelper):
    '''Operator used for exporting Minecraft animations from blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.export_animation"
    bl_label = "Export Bedrock Animation"
    bl_options = {'REGISTER'}
    bl_description = (
        "Export the currently active animation of the selected armature as "
        "a Minecraft Bedrock Edition animation")

    filename_ext = '.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if context.mode != 'OBJECT':
            return False
        obj = context.object
        if obj is None:
            return False
        if obj.type != 'ARMATURE':
            return False
        len_anims = len(
            get_mcblend(obj).animations)
        if len_anims == 0:
            return False
        curr_anim_id = get_mcblend(obj).active_animation
        if 0 > curr_anim_id >= len_anims:
            return False
        return True

    def execute(self, context: Context):
        # Read and validate old animation file
        old_dict: Optional[Dict[str, Any]] = None
        filepath: str = self.filepath  # type: ignore
        try:
            with open(filepath, 'r', encoding='utf8') as f:  # type: ignore
                old_dict = json.load(f, cls=JSONCDecoder)
        except (json.JSONDecodeError, OSError):
            pass
        animation_dict = export_animation(context, old_dict)
        # Save file and finish
        with open(filepath, 'w', encoding='utf8') as f:  # type: ignore
            json.dump(animation_dict, f, cls=CompactEncoder)
        self.report({'INFO'}, f'Animation saved in {filepath}.')
        return {'FINISHED'}

def menu_func_mcblend_export_animation(self: Any, context: Context):
    '''Used to register the operator in the file export menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(MCBLEND_OT_ExportAnimation.bl_idname)

# UV mapper
class MCBLEND_OT_MapUv(Operator):
    '''
    Operator used for creating UV mapping and optionally the tamplate texture
    for Minecraft model.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.map_uv"
    bl_label = "Automatic UV mapping"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_description = (
        "UV map child cubes of the currently selected armature"
    )


    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        bpy.ops.screen.animation_cancel()  # pyright: ignore[reportUnknownMemberType]
        original_frame = context.scene.frame_current
        try:
            context.scene.frame_set(0)
            # TODO - add safety check with this to set_uvs() function
            # for obj in get_context_selected_objects(context):
            #     if obj.type == 'MESH' and any(map(lambda x: x < 0, obj.scale)):
            #         self.report(
            #             {'ERROR'},
            #             "Negative object scale is not supported. "
            #             f"Object: {obj.name}; Frame: 0.")
            #         return {'FINISHED'}
            set_uvs(context)
        except NotEnoughTextureSpace:
            self.report(
                {'ERROR'},
                "Not enough texture space to create UV mapping.")
            return {'FINISHED'}
        finally:
            context.scene.frame_set(original_frame)

        self.report({'INFO'}, 'UV maps created successfully.')
        return {'FINISHED'}

class MCBLEND_OT_FixUv(Operator):
    '''
    Fixes the UV mapping of the cubes connected to selected armature.
    After this operator the faces of the cubes on the UV map are rectangular
    and properly rotated.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.fix_uv"
    bl_label = "Fix invalid UV mapping"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Fix invalid UV mapping of the child cubes of the selected armature"
    )

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if obj.type == 'MESH' and any(x < 0 for x in obj.scale):
                self.report(
                    {'ERROR'},
                    "Negative object scale is not supported. "
                    f"Object: {obj.name}; Frame: 0.")
                return {'FINISHED'}
        fixed_cubes, fixed_faces = fix_uvs(context)

        self.report(
            {'INFO'},
            'Successfully fixed the UV mapping of selected '
            f'objects - {fixed_faces} faces of {fixed_cubes} cubes.'
        )
        return {'FINISHED'}

# UV grouping
class MCBLEND_OT_UvGroup(Operator):
    '''Operator used for adding selected objects to an UV group'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.uv_group"
    bl_label = "Set the UV group"
    bl_options = {'UNDO'}
    bl_description = "Set the UV groups of the selected objects"

    def _list_uv_groups(self, context: Context):
        items = [
            (x.name, x.name, x.name)
            for x in get_mcblend_uv_groups(context.scene)]
        return items
    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        if len(get_mcblend_uv_groups(context.scene)) == 0:
            return False
        return True

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                get_mcblend(obj).uv_group = (
                    self.uv_groups_enum)  # type: ignore
        self.report(
            {'INFO'},
            f'Set UV group of selected objects to '
            f'{self.uv_groups_enum}.'  # type: ignore
        )

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

class MCBLEND_OT_ClearUvGroup(Operator):
    '''Operator used for removing selected objects from their UV groups'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.clear_uv_group"
    bl_label = "Clear UV group"
    bl_options = {'UNDO'}
    bl_description = 'Clear the UV group from the selected objects'

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        if len(get_mcblend_uv_groups(context.scene)) == 0:
            return False
        return True

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                get_mcblend(obj).uv_group  = ''
        self.report({'INFO'}, 'Cleared UV group of selected objects.')

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# Inflate property
class MCBLEND_OT_SetInflate(Operator):
    '''
    Operator used for setting the inflate value of selected objects.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.set_inflate"
    bl_label = "Inflate"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Set the \"inflate\" property of the selected objects and adjust "
        "their sizes accordingly"
    )

    inflate_value: FloatProperty(default=0)  # type: ignore
    mode: EnumProperty(  # type: ignore
        items=[
            ('RELATIVE', 'Relative', 'Add or remove to current inflate value'),
            ('ABSOLUTE', 'Absolute', 'Set the inflate value'),
        ],
        name='Mode'
    )

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def invoke(self, context: Context, event: Event):
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                break
        else:
            self.report({'WARNING'}, 'Select at least one mesh to inflate.')
            return {'CANCELLED'}
        self.inflate_value = 0
        self.mode = 'RELATIVE'
        return {'FINISHED'}

    def execute(self, context: Context):
        inflate_objects(
            context, context.selected_objects,
            self.inflate_value, self.mode)  # type: ignore
        return {'FINISHED'}

# Separate mesh cubes
class MCBLEND_OT_SeparateMeshCubes(Operator):
    '''
    Separates object with mesh full of cuboids by the loose parts of the mesh.
    Adjusts the rotations of the newly created objects to match the rotations
    of the cubes inside of this object.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.separate_mesh_cubes"
    bl_label = "Separate and align cubes"
    bl_options = {'UNDO'}
    bl_description = (
        "Separate the parts of the selected objects and rotate their bound "
        "boxes to minimize their sizes"
    )

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) < 1:
            return False
        return True

    def execute(self, context: Context):
        edited_objects = separate_mesh_cubes(context)
        if edited_objects == 1:
            self.report({'INFO'}, "Aligned object orientation to mesh")
        else:
            self.report(
                {'INFO'}, f"Separated mesh into {edited_objects} objects")
        return {'FINISHED'}

# Model Importer
class MCBLEND_OT_ImportModel(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ImportHelper):
    '''Operator used for importing Minecraft models to Blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.import_model"
    bl_label = "Import Bedrock Model"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Import Minecraft Bedrock edition model from a JSON file"
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

    if TYPE_CHECKING:
        filepath: str

    def execute(self, context: Context):
        # Save file and finish
        with open(self.filepath, 'r', encoding='utf8') as f:
            data = json.load(f, cls=JSONCDecoder)
        try:
            warnings = import_model(
                data,
                self.geometry_name,  # type: ignore
                context)
            if len(warnings) > 1:
                for warning in warnings:
                    self.report({'WARNING'}, warning)
                    self.report(
                        {'WARNING'},
                        f"Finished with {len(warnings)} warnings. "
                        "See logs for more details."
                    )
            elif len(warnings) == 1:
                self.report({'WARNING'}, warnings[0])
        except ImporterException as e:
            self.report(
                {'ERROR'}, f'Invalid model: {e}'
            )
        return {'FINISHED'}

# Animation (GUI)
def menu_func_mcblend_import_model(self: Any, context: Context):
    '''Used to register the operator in the file import menu.'''
    # pylint: disable=unused-argument
    self.layout.operator(MCBLEND_OT_ImportModel.bl_idname)

def save_animation_properties(
        animation: MCBLEND_AnimationProperties, context: Context):
    '''
    Saves animation properties from context to
    MCBLEND_AnimationProperties object.
    '''
    animation.frame_start = context.scene.frame_start
    animation.frame_end = context.scene.frame_end
    animation.frame_current = context.scene.frame_current

    animation.timeline_markers.clear()
    for timeline_marker in context.scene.timeline_markers:
        anim_timeline_marker = animation.timeline_markers.add()
        anim_timeline_marker.name = timeline_marker.name
        anim_timeline_marker.frame = timeline_marker.frame
    animation.nla_tracks.clear()
    
    obj = context.object
    if obj is None:  # TODO - should this be an error?
        return
    if obj.animation_data is not None:
        for nla_track in obj.animation_data.nla_tracks:
            if not nla_track.mute:
                cached_nla_track = animation.nla_tracks.add()
                cached_nla_track.name = nla_track.name

def load_animation_properties(animation: MCBLEND_AnimationProperties, context: Context):
    '''
    Saves animation properties from MCBLEND_AnimationProperties
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
    obj = context.object
    if obj is None:
        return
    anim_data = obj.animation_data
    if anim_data is not None:
        object_nla_tracks = anim_data.nla_tracks
        for nla_track in object_nla_tracks:
            nla_track.mute = True
        for cached_nla_track in animation.nla_tracks:
            if cached_nla_track.name in object_nla_tracks:
                object_nla_tracks[cached_nla_track.name].mute = False

class MCBLEND_OT_ListAnimations(Operator):
    '''
    Operator used for listing the animations for GUI.
    '''
    bl_idname = "mcblend.list_animations"
    bl_label = "Select animation"
    bl_description = "Select the active animation for editing"
    bl_options = {'INTERNAL'}

    def _list_animations(self, context: Context):
        # pylint: disable=unused-argument
        if context.object is None:
            return []
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(get_mcblend(context.object).animations)]
        return items

    animations_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_animations, name="Animations")

    @classmethod
    def poll(cls, context: Context):
        if context.object is None:
            return False
        if context.mode != 'OBJECT':
            return False
        if context.object.type != 'ARMATURE':
            return False
        return True

    def execute(self, context: Context):
        '''
        Runs when user picks an item from the dropdown menu in animations
        panel. Sets the active animation.
        '''
        # Cancel operation if there is an action being edited
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        anim_data = obj.animation_data
        if anim_data is None:
            return {'CANCELLED'}
        if anim_data.action is not None:  # type: ignore
            # TODO - stash action and activate the action strip for current
            # animation if a new aniamtion has been selected
            self.report(
                {'WARNING'},
                "Stash, push down or delete the active action before "
                "selecting new animation")
            return {'CANCELLED'}
        # If OK than save old animation state
        len_anims = len(get_mcblend(obj).animations)
        curr_anim_id = get_mcblend(obj).active_animation
        if 0 <= curr_anim_id < len_anims:
            save_animation_properties(
                get_mcblend(obj).animations[curr_anim_id], context)

        # Set new animation and load its state
        new_anim_id=int(self.animations_enum)  # type: ignore
        get_mcblend(obj).active_animation=new_anim_id
        load_animation_properties(
                get_mcblend(obj).animations[new_anim_id], context)
        return {'FINISHED'}

class MCBLEND_OT_AddAnimation(Operator):
    '''Operator used creating animation settings templates.'''
    bl_idname = "mcblend.add_animation"
    bl_label = "New animation"
    bl_description = "Create new Minecraft animation"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        if context.object is None:
            return False
        if context.mode != 'OBJECT':
            return False
        if context.object.type != 'ARMATURE':
            return False
        return True

    def execute(self, context: Context):
        # Cancel operation if there is an action being edited
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        anim_data = obj.animation_data
        if (
                anim_data is not None and
                anim_data.action is not None):  # type: ignore
            # TODO - stash action if mcblend animation already exists or
            # don't do anything if that's the first mcblend aniamtion
            self.report(
                {'WARNING'},
                "Stash, push down or delete the active action before "
                "adding new animation")
            return {'CANCELLED'}
        # If OK save old animation
        len_anims = len(get_mcblend(obj).animations)
        curr_anim_id = get_mcblend(obj).active_animation
        if 0 <= curr_anim_id < len_anims:
            save_animation_properties(
                get_mcblend(obj).animations[curr_anim_id], context)
            context.scene.timeline_markers.clear()

        # Add new animation and set its properties
        animation_new = get_mcblend(obj).animations.add()
        len_anims = len(get_mcblend(obj).animations)
        get_mcblend(obj).active_animation=len_anims-1
        animation_new.name = f'animation{len_anims}'

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

class MCBLEND_OT_RemoveAnimation(Operator):
    '''
    Operator used for loading saved animation templates to the context.
    '''
    bl_idname = "mcblend.remove_animation"
    bl_label = "Remove this animation"
    bl_description = "Remove the currently active Minecraft animation"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        if context.object is None:
            return False
        if context.mode != 'OBJECT':
            return False
        if context.object.type != 'ARMATURE':
            return False
        return len(get_mcblend(context.object).animations) > 0

    def execute(self, context: Context):
        # Cancel operation if there is an action being edited
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        anim_data = obj.animation_data
        if (
                anim_data is not None and
                anim_data.action is not None):  # type: ignore
            # TODO - automatically remove the active animation instead of pringint a warning
            self.report(
                {'WARNING'},
                "Stash, push down or delete the active action before "
                "removing new animation")
            return {'CANCELLED'}

        # Remove animation
        get_mcblend(obj).animations.remove(
            get_mcblend(obj).active_animation)

        # Set new active animation
        last_active=get_mcblend(obj).active_animation
        len_anims=len(get_mcblend(obj).animations)
        if last_active > 0:
            get_mcblend(obj).active_animation=last_active-1

        # Load data from new active animation
        curr_anim_id=get_mcblend(obj).active_animation
        if 0 <= curr_anim_id < len_anims:
            load_animation_properties(
                get_mcblend(obj).animations[curr_anim_id], context)

        # The object properties display the property edited by this operator
        # redraw it.
        for area in context.screen.areas:
            if area.type == 'PROPERTIES':
                area.tag_redraw()
        return {'FINISHED'}

# UV group (GUI)
class MCBLEND_OT_ListUvGroups(Operator):
    '''
    Operator that used for listing the UV groups for GUI.
    '''
    bl_idname = "mcblend.list_uv_groups"
    bl_label = "Select UV group"
    bl_description = "Select the active UV group for editing"
    bl_options = {'INTERNAL'}

    def _list_uv_groups(self, context: Context):
        # pylint: disable=unused-argument
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(
                get_mcblend_uv_groups(context.scene))
            ]
        return items

    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")

    def execute(self, context: Context):
        '''
        Runs when user picks an item from the dropdown menu in uv_groups
        panel. Sets the active uv_group.
        '''
        # Set new uv_group and load its state
        new_uv_group_id=int(self.uv_groups_enum)  # type: ignore
        set_mcblend_active_uv_group(context.scene, new_uv_group_id)
        return {'FINISHED'}

class MCBLEND_OT_AddUvGroup(Operator):
    '''Operator used for creating new UV groups.'''
    bl_idname = "mcblend.add_uv_group"
    bl_label = "New UV group"
    bl_description = "New UV group"
    bl_options = {'UNDO', 'INTERNAL'}

    def execute(self, context: Context):
        # If OK save old uv_group
        len_groups = len(get_mcblend_uv_groups(context.scene))

        # Add new uv_group and set its properties
        uv_group_new = get_mcblend_uv_groups(context.scene).add()
        len_groups = len(get_mcblend_uv_groups(context.scene))
        set_mcblend_active_uv_group(context.scene, len_groups-1)

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

class MCBLEND_OT_RemoveUvGroup(Operator):
    '''Operator useful for removing UV groups.'''
    bl_idname = "mcblend.remove_uv_group"
    bl_label = "Delete this UV group"
    bl_description = "Delete the currently active UV group"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        return len(get_mcblend_uv_groups(context.scene)) > 0

    def execute(self, context: Context):
        group_id = get_mcblend_active_uv_group(context.scene)
        group_name = get_mcblend_uv_groups(context.scene)[group_id].name
        # Remove uv_group
        get_mcblend_uv_groups(context.scene).remove(group_id)

        # Update the names of all of the meshes
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                obj_props = get_mcblend(obj)
                if obj_props.uv_group == group_name:
                    obj_props.uv_group = ''

        # Set new active uv_group
        if group_id > 0:
            set_mcblend_active_uv_group(context.scene, group_id-1)
        return {'FINISHED'}

class MCBLEND_OT_CopyUvGroupSide(Operator):
    '''Operator used for copying sides of UV groups.'''
    bl_idname = "mcblend.copy_uv_group_side"
    bl_label = "Copy current UV face"
    bl_description = (
        "Copy the currently active UV face to another UV group face")
    bl_options = {'UNDO', 'INTERNAL'}

    def _list_uv_groups(self, context: Context):
        # pylint: disable=unused-argument
        items = [
            (str(i), x.name, x.name)
            for i, x in enumerate(get_mcblend_uv_groups(context.scene))]
        return items

    uv_groups_enum: bpy.props.EnumProperty(  # type: ignore
        items=_list_uv_groups, name="UV Groups")
    side1: BoolProperty(name='side1')  # type: ignore
    side2: BoolProperty(name='side2')  # type: ignore
    side3: BoolProperty(name='side3')  # type: ignore
    side4: BoolProperty(name='side4')  # type: ignore
    side5: BoolProperty(name='side5')  # type: ignore
    side6: BoolProperty(name='side6')  # type: ignore

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context: Context):
        return len(get_mcblend_uv_groups(context.scene)) >= 1

    def _copy_side(
            self, context: Context,
            source_group_id: int, source_side_id: int,
            target_group_id: int, target_side_id: int):
        if (
            source_group_id == target_group_id and
            source_side_id == target_side_id
        ):
            return  # If source and target is the same don't do anything
        # Get source
        source_group = get_mcblend_uv_groups(
            context.scene)[source_group_id]
        source_sides = [
            source_group.side1, source_group.side2,
            source_group.side3, source_group.side4,
            source_group.side5, source_group.side6]
        source_masks = source_sides[source_side_id]
        # Get target
        target_group = get_mcblend_uv_groups(
            context.scene)[target_group_id]
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

    def execute(self, context: Context):
        # Get source masks
        source_group_id = get_mcblend_active_uv_group(context.scene)
        source_side_id = int(get_mcblend_active_uv_groups_side(context.scene))

        # Get target UV group
        target_group_id = int(self.uv_groups_enum)  # type: ignore

        if self.side1:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 0)
        if self.side2:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 1)
        if self.side3:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 2)
        if self.side4:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 3)
        if self.side5:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 4)
        if self.side6:  # type: ignore
            self._copy_side(
                context, source_group_id, source_side_id, target_group_id, 5)
        self.report({'INFO'}, 'Successfully copied UV face.')
        return {'FINISHED'}

# UV Mask (GUI)
def get_active_masks(context: Context):
    '''Returns active masks of active UV Group from context.'''
    curr_group_id = get_mcblend_active_uv_group(context.scene)
    curr_group = get_mcblend_uv_groups(context.scene)[curr_group_id]
    sides = [
        curr_group.side1, curr_group.side2,
        curr_group.side3, curr_group.side4,
        curr_group.side5, curr_group.side6
    ]
    masks = sides[int(get_mcblend_active_uv_groups_side(context.scene))]
    return masks

class MCBLEND_OT_AddUvMask(Operator):
    '''Operator used for adding UV masks to UV groups.'''
    bl_idname = "mcblend.add_uv_mask"
    bl_label = "Add mask"
    bl_description = "Add a new mask to the currently active UV group"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_type: EnumProperty(  # type: ignore
        items=list_mask_types_as_blender_enum, name='Mask type'
    )

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        new_mask = masks.add()
        new_mask.mask_type = self.mask_type  # type: ignore
        new_mask.colors.add()
        new_mask.stripes.add()
        return {'FINISHED'}

class MCBLEND_OT_RemoveUvMask(Operator):
    '''Operator used for removing UV masks from UV groups.'''
    bl_idname = "mcblend.remove_uv_mask"
    bl_label = "Remove this mask"
    bl_description = "Remove this mask from the UV group"
    bl_options = {'UNDO', 'INTERNAL'}

    target: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        masks.remove(self.target)  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_MoveUvMask(Operator):
    '''Operator used for changing the order of UV masks in UV groups.'''
    bl_idname = "mcblend.move_uv_mask"
    bl_label = "Move this UV mask"
    bl_description = "Change the order of masks in the UV group"
    bl_options = {'UNDO', 'INTERNAL'}

    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        masks.move(self.move_from, self.move_to)  # type: ignore
        return {'FINISHED'}

# UV Mask side colors (GUI)
class MCBLEND_OT_AddUvMaskColor(Operator):
    '''Operator used for adding colors to UV masks.'''
    bl_idname = "mcblend.add_uv_mask_color"
    bl_label = "Add color"
    bl_description = "Add a new color to the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.colors.add()
        return {'FINISHED'}

class MCBLEND_OT_RemoveUvMaskColor(Operator):
    '''Operator used for removing colors from UV masks.'''
    bl_idname = "mcblend.remove_uv_mask_color"
    bl_label = "Remove color"
    bl_description = "Remove the color from the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore
    color_index: IntProperty()  # type: ignore


    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.colors.remove(self.color_index)  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_MoveUvMaskColor(Operator):
    '''Operator used for changing the order of the colors in UV masks.'''
    bl_idname = "mcblend.move_uv_mask_color"
    bl_label = "Move this color"
    bl_description = "Change the order of colors in the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore
    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.colors.move(self.move_from, self.move_to)  # type: ignore
        return {'FINISHED'}

# UV Mask side stripes (GUI)
class MCBLEND_OT_AddUvMaskStripe(Operator):
    '''Operator used for adding stripes to UV masks.'''
    bl_idname = "mcblend.add_uv_mask_stripe"
    bl_label = "Add strip"
    bl_description = "Add a new strip to the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.stripes.add()
        return {'FINISHED'}

class MCBLEND_OT_RemoveUvMaskStripe(Operator):
    '''Operator used for removing UV masks from UV groups.'''
    bl_idname = "mcblend.remove_uv_mask_stripe"
    bl_label = "Remove strip"
    bl_description = "Remove the strip from the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore
    stripe_index: IntProperty()  # type: ignore


    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.stripes.remove(self.stripe_index)  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_MoveUvMaskStripe(Operator):
    '''Operator used for changing the order of the stripes in UV groups.'''
    bl_idname = "mcblend.move_uv_mask_stripe"
    bl_label = "Move this strip"
    bl_description = "Change the order of strips in the UV mask"
    bl_options = {'UNDO', 'INTERNAL'}

    mask_index: IntProperty()  # type: ignore
    move_from: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        if len(get_mcblend_uv_groups(context.scene)) < 1:
            return False
        return True

    def execute(self, context: Context):
        masks = get_active_masks(context)
        mask = masks[self.mask_index]  # type: ignore
        mask.stripes.move(self.move_from, self.move_to)  # type: ignore
        return {'FINISHED'}

# UV Mask exporter
class MCBLEND_OT_ExportUvGroup(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ExportHelper):
    '''Operator used for exporting active UV group from Blender.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.export_uv_group"
    bl_label = "Export UV group"
    bl_description = "Exports the currently active UV group"
    bl_options = {'REGISTER', 'INTERNAL'}

    filename_ext = '.json'

    filter_glob: StringProperty(  # type: ignore
        default='*.uvgroup.json',
        options={'HIDDEN'},
        maxlen=1000
    )

    if TYPE_CHECKING:
        filepath: str

    @classmethod
    def poll(cls, context: Context):
        return len(get_mcblend_uv_groups(context.scene)) > 0

    def execute(self, context: Context):
        group_id = get_mcblend_active_uv_group(context.scene)
        uv_group = get_mcblend_uv_groups(context.scene)[group_id]

        with open(self.filepath, 'w', encoding='utf8') as f:
            json.dump(uv_group.json(), f, cls=CompactEncoder)
        self.report({'INFO'}, f'UV group saved in {self.filepath}.')
        return {'FINISHED'}

# UV Mask exporter
class MCBLEND_OT_ImportUvGroup(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ImportHelper):
    '''Operator used for importing UV groups to Blender.'''
    # pylint: disable=unused-argument, no-member, too-many-boolean-expressions
    bl_idname = "mcblend.import_uv_group"
    bl_label = "Import UV group"
    bl_description = "Import an UV group from JSON file"
    bl_options = {'REGISTER', 'INTERNAL'}
    # ImportHelper mixin class uses this
    filename_ext = ".json"
    filter_glob: StringProperty(  # type: ignore
        default="*.json",
        options={'HIDDEN'},
        maxlen=1000,
    )

    def _load_mask_data(
            self,
            mask_data: Dict[str, Any],
            side: CollectionProperty[MCBLEND_UvMaskProperties]
    ) -> Optional[str]:
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
                    colors = cast(List[Any], colors)
                    for color_data in colors:
                        if (
                                not isinstance(color_data, list) or
                                len(color_data) != 3):  # type: ignore
                            loading_warning = (
                                'Every color on colors list should be '
                                'a list of floats.')
                            continue
                        is_color = True
                        color_data = cast(List[Any], color_data)
                        for value_data in color_data:
                            if not isinstance(value_data, (float, int)):
                                is_color = False
                                loading_warning =(
                                    'All values of color must be '
                                    'floats in range 0.0-1.0')
                                break
                        if is_color:
                            color = mask.colors.add()
                            color.color = cast(Vector3d, color_data)
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
                            len(mask_data['p1']) == 2 and  # type: ignore
                            isinstance(mask_data['p1'][0], (float, int)) and
                            isinstance(mask_data['p1'][1], (float, int)) and
                            0.0 <= mask_data['p1'][0] <= 1.0 and
                            0.0 <= mask_data['p1'][1] <= 1.0):
                        mask.p1_relative = mask_data['p1']  # type: ignore
                    else:
                        loading_warning = (
                            '"p1" property must be a float in range 0.0 to '
                            '1.0 if "relative_boundaries" are True')
                if 'p2' in mask_data:
                    if (
                            isinstance(mask_data['p2'], list) and
                            len(mask_data['p2']) == 2 and  # type: ignore
                            isinstance(mask_data['p2'][0], (float, int)) and
                            isinstance(mask_data['p2'][1], (float, int)) and
                            0.0 <= mask_data['p2'][0] <= 1.0 and
                            0.0 <= mask_data['p2'][1] <= 1.0):
                        mask.p2_relative = mask_data['p2']  # type: ignore
                    else:
                        loading_warning = (
                            '"p2" property must be a float in range 0.0 to '
                            '1.0 if "relative_boundaries" are True')
            else:
                if 'p1' in mask_data:
                    if (
                            isinstance(mask_data['p1'], list) and
                            len(mask_data['p1']) == 2 and  # type: ignore
                            isinstance(mask_data['p1'][0], int) and
                            isinstance(mask_data['p1'][1], int)):
                        mask.p1 = mask_data['p1']  # type: ignore
                    else:
                        loading_warning = (
                            '"p1" property must be an integer if '
                            '"relative_boundaries" are False')
                if 'p2' in mask_data:
                    if (
                            isinstance(mask_data['p2'], list) and
                            len(mask_data['p2']) == 2 and  # type: ignore
                            isinstance(mask_data['p2'][0], int) and
                            isinstance(mask_data['p2'][1], int)):
                        mask.p2 = mask_data['p2']  # type: ignore
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
                    for stripe_data in stripes:  # type: ignore
                        if not isinstance(stripe_data, dict):
                            loading_warning = (
                                'Every stripe in the stripes list must be an '
                                'object')
                            continue
                        stripe = mask.stripes.add()
                        if 'width' in stripe_data:
                            width = stripe_data['width']  # type: ignore
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
                            strength = stripe_data['strength']  # type: ignore
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
                        isinstance(strength, list) and len(strength) == 2 and  # type: ignore
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
                        len(color_data) != 3):  # type: ignore
                    loading_warning = (
                        'Every color on colors list should be '
                        'a list of floats.')
                else:
                    is_color = True
                    for value_data in color_data:  # type: ignore
                        if not isinstance(value_data, (float, int)):
                            is_color = False
                            loading_warning =(
                                'All values of color must be '
                                'floats in range 0.0-1.0')
                            break
                    if is_color:
                        mask.color.color = cast(Vector3d, color_data)
        return loading_warning

    def _load_side(
            self,
            side: CollectionProperty[MCBLEND_UvMaskProperties],
            side_data: List[Any]
    ) -> Optional[str]:
        loading_warning = None
        for mask_data in side_data:
            if not isinstance(mask_data, dict):
                continue
            mask_data = cast(Dict[str, Any], mask_data)
            loading_warning = self._load_mask_data(mask_data, side)
        return loading_warning

    def execute(self, context: Context) -> Set[str]:
        name: str = get_unused_uv_group_name('uv_group')
        # Save file and finish
        try:
            filepath: str = cast(str, self.filepath)  # type: ignore
            with open(filepath, 'r', encoding='utf8') as f:
                data: Dict[str, Any] = json.load(f, cls=JSONCDecoder)
            version = data['version']
            if version != 1:
                self.report({'ERROR'}, "Unknown UV group version.")
                return {'CANCELLED'}
        except (KeyError, TypeError, JSONDecodeError):
            self.report({'ERROR'}, "Unable to to read the UV group data.")
            return {'CANCELLED'}

        # Create new UV group
        len_groups = len(get_mcblend_uv_groups(context.scene))
        # Add new uv_group and set its properties
        uv_group_new = get_mcblend_uv_groups(context.scene).add()
        len_groups = len(get_mcblend_uv_groups(context.scene))
        set_mcblend_active_uv_group(context.scene, len_groups-1)

        # Currently only version 1 is supported
        if 'name' in data and isinstance(data['name'], str):
            name =  get_unused_uv_group_name(data['name'])
        uv_group_new.name = name

        # Used for showing warnings about loading process (the loader shows
        # only one warning at a time)
        loading_warning: Optional[str] = None
        if 'side1' in data and isinstance(data['side1'], list):
            loading_warning=self._load_side(uv_group_new.side1, data['side1'])  # type: ignore
        if 'side2' in data and isinstance(data['side2'], list):
            loading_warning=self._load_side(uv_group_new.side2, data['side2'])  # type: ignore
        if 'side3' in data and isinstance(data['side3'], list):
            loading_warning=self._load_side(uv_group_new.side3, data['side3'])  # type: ignore
        if 'side4' in data and isinstance(data['side4'], list):
            loading_warning=self._load_side(uv_group_new.side4, data['side4'])  # type: ignore
        if 'side5' in data and isinstance(data['side5'], list):
            loading_warning=self._load_side(uv_group_new.side5, data['side5'])  # type: ignore
        if 'side6' in data and isinstance(data['side6'], list):
            loading_warning=self._load_side(uv_group_new.side6, data['side6'])  # type: ignore

        # If something didn't load propertly also display a warning
        if loading_warning is not None:
            self.report({'WARNING'}, loading_warning)

        if context.area is not None:  # pyright: ignore[reportUnnecessaryComparison]
            # There is no area when running from CLI
            context.area.tag_redraw()
        return {'FINISHED'}

# Events
class MCBLEND_OT_AddEvent(Operator):
    '''Operator used for adding events to scene.'''
    bl_idname = "mcblend.add_event"
    bl_label = "New event"
    bl_description = "Create a new event"
    bl_options = {'UNDO', 'INTERNAL'}

    def execute(self, context: Context):
        event_new = get_mcblend_events(context.scene).add()
        event_new.name = get_unused_event_name('event')
        return {'FINISHED'}

class MCBLEND_OT_RemoveEvent(Operator):
    '''Operator used for removing events.'''
    bl_idname = "mcblend.remove_event"
    bl_label = "Delete this event"
    bl_description = "Delete the currently active event"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        events = get_mcblend_events(context.scene)
        active_event_id = get_mcblend_active_event(context.scene)
        if not 0 <= active_event_id < len(events):
            return False
        return True

    def execute(self, context: Context):
        active_event_id = get_mcblend_active_event(context.scene)
        # Remove animation
        get_mcblend_events(context.scene).remove(
            active_event_id)

        # Set new active event
        if active_event_id > 0:
            set_mcblend_active_event(context.scene, active_event_id-1)
        return {'FINISHED'}

class MCBLEND_OT_AddEffect(Operator):
    '''Operator used for adding effects to events.'''
    bl_idname = "mcblend.add_effect"
    bl_label = "Add effect"
    bl_description = "Add a new effect to the currently active event"
    bl_options = {'UNDO', 'INTERNAL'}

    effect_type: EnumProperty(  # type: ignore
        items=list_effect_types_as_blender_enum, name='Effect type'
    )

    @classmethod
    def poll(cls, context: Context):
        events = get_mcblend_events(context.scene)
        active_event_id = get_mcblend_active_event(context.scene)
        if not 0 <= active_event_id < len(events):
            return False
        return True

    def execute(self, context: Context):
        events = get_mcblend_events(context.scene)
        active_event_id = get_mcblend_active_event(context.scene)
        event = events[active_event_id]

        effect = event.effects.add()
        effect.effect_type = self.effect_type  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_RemoveEffect(Operator):
    '''Operator used for removeing effects effects from events.'''
    bl_idname = "mcblend.remove_effect"
    bl_label = "Remove effect"
    bl_description = "Remove the effect from the currently active event"
    bl_options = {'UNDO', 'INTERNAL'}

    effect_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        events = get_mcblend_events(context.scene)
        active_event_id = get_mcblend_active_event(context.scene)
        if not 0 <= active_event_id < len(events):
            return False
        event = events[active_event_id]
        effects = event.effects
        if len(effects) <= 0:
            return False
        return True

    def execute(self, context: Context):
        events = get_mcblend_events(context.scene)
        active_event_id = get_mcblend_active_event(context.scene)
        event = events[active_event_id]
        event.effects.remove(self.effect_index)  # type: ignore

        return {'FINISHED'}

# Project - RP entity import
class MCBLEND_OT_LoadRp(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ImportHelper):
    '''Imports entity form Minecraft project into blender'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.load_rp"
    bl_label = "Load Resource Pack"
    bl_description = "Loads a resource pack to the project"
    bl_options = {'REGISTER'}

    filter_glob: StringProperty(  # type: ignore
        default="",
        options={'HIDDEN'},
        maxlen=1000,
    )

    def execute(self, context: Context) -> Set[str]:
        rp_path: Path = Path(self.filepath)  # type: ignore
        load_rp_to_mcblned(context, rp_path)
        return {'FINISHED'}

class MCBLEND_OT_UnloadRps(Operator):
    '''Unloads all resource packs from the database'''
    bl_idname = "mcblend.unload_rps"
    bl_label = "Unload Resource Packs"
    bl_description = "Unloads all resource packs from the project"
    bl_options = {'REGISTER'}


    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context):
        unload_rps(context)
        return {'FINISHED'}

class MCBLEND_OT_LoadDatabase(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ImportHelper):
    '''Loads SQLite database with resource pack data.'''
    # pylit: disable=unused-argument, no-member
    bl_idname = "mcblend.load_database"
    bl_label = "Load database"
    bl_description = "Loads the SQLite database with a resource pack data"
    bl_options = {'REGISTER'}

    filter_glob: StringProperty(  # type: ignore
        default="*.db",
        options={'HIDDEN'},
        maxlen=1000,
    )

    if TYPE_CHECKING:
        filepath: str

    def execute(self, context: Context):
        self.report({'INFO'}, f"Loading database from {self.filepath}")
        return {'FINISHED'}

class MCBLEND_OT_SaveDatabase(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ExportHelper):
    '''Saves SQLite database with resource packs data.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.save_database"
    bl_label = "Save database"
    bl_description = "Saves the SQLite database with resource packs data"
    bl_options = {'REGISTER'}

    filename_ext = ".db"

    if TYPE_CHECKING:
        filepath: str

    def execute(self, context: Context):
        self.report({'INFO'}, f"Saving database to {self.filepath}")
        return {'FINISHED'}

class MCBLEND_OT_ImportRpEntity(Operator):
    '''Imports entity form Minecraft project into blender'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.import_rp_entity"
    bl_label = "Import entity from project"
    bl_description = "Import an entity from the resource pack"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        return len(get_mcblend_project(context.scene).entities) > 0

    def execute(self, context: Context):
        try:
            query_data = get_pks_for_model_improt(context, 'entity')
            warnings = import_model_form_project(
                context, 'entity', query_data)
            if len(warnings) > 1:
                for warning in warnings:
                    self.report({'WARNING'}, warning)
                    self.report(
                        {'WARNING'},
                        f"Finished with {len(warnings)} warnings. "
                        "See logs for more details."
                    )
            elif len(warnings) == 1:
                self.report({'WARNING'}, warnings[0])
        except ImporterException as e:
            self.report(
                {'ERROR'}, f'Invalid model: {e}'
            )
        return {'FINISHED'}

class MCBLEND_OT_ImportAttachable(Operator):
    '''Imports attachable form Minecraft project into blender'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.import_attachable"
    bl_label = "Import attachable from project"
    bl_description = "Import an attachable from the resource pack"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        return len(get_mcblend_project(context.scene).attachables) > 0

    def execute(self, context: Context):
        try:
            query_data = get_pks_for_model_improt(context, 'attachable')
            warnings = import_model_form_project(
                context, 'attachable', query_data)
            if len(warnings) > 1:
                for warning in warnings:
                    self.report({'WARNING'}, warning)
                    self.report(
                        {'WARNING'},
                        f"Finished with {len(warnings)} warnings. "
                        "See logs for more details."
                    )
            elif len(warnings) == 1:
                self.report({'WARNING'}, warnings[0])
        except ImporterException as e:
            self.report(
                {'ERROR'}, f'Invalid model: {e}'
            )
        return {'FINISHED'}

# Armature render controllers
class MCBLEND_OT_AddFakeRc(Operator):
    '''Adds new render controller to active model (armature).'''
    bl_idname = "mcblend.add_fake_rc"
    bl_label = "Add render controller"
    bl_description = "Create a new render controller for the entity"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        rc = get_mcblend(obj).render_controllers.add()
        material = rc.materials.add()
        material.pattern = '*'
        material.material = 'entity_alphatest'
        return {'FINISHED'}

class MCBLEND_OT_RemoveFakeRc(Operator):
    '''Removes render controller from active model (armature).'''
    bl_idname = "mcblend.remove_fake_rc"
    bl_label = "Remove render controller"
    bl_description = "Remove this render controller from the entity"
    bl_options = {'UNDO', 'INTERNAL'}

    rc_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        rcs = get_mcblend(context.object).render_controllers
        rcs.remove(self.rc_index)  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_MoveFakeRc(Operator):
    '''Moves render controller in active to a different spot on the list.'''
    bl_idname = "mcblend.move_fake_rc"
    bl_label = "Move render controller"
    bl_description = "Change the order of render controllers in this entity"

    bl_options = {'UNDO', 'INTERNAL'}

    if TYPE_CHECKING:
        rc_index: int
        move_to: int
    else:
        rc_index: IntProperty()  # type: ignore
        move_to: IntProperty()  # type: ignore


    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        rcs = get_mcblend(context.object).render_controllers
        rcs.move(self.rc_index, self.move_to)
        return {'FINISHED'}

class MCBLEND_OT_FakeRcSelectTexture(Operator):
    '''Selects the name of the texture for render controller of a model.'''
    bl_idname = "mcblend.fake_rc_select_texture"
    bl_label = "Select texture by name"
    bl_description = (
        "Select the texture used by the entity using the name of the texture")
    bl_options = {'UNDO', 'INTERNAL'}

    rc_index: IntProperty(options={'HIDDEN'})  # type: ignore

    def list_images(self, context: Context):
        '''Lists images for dropdown list'''
        # pylint: disable=unused-argument
        items = [
            (x.name, x.name, x.name)
            for x in bpy.data.images]
        return items
    image: bpy.props.EnumProperty(  # type: ignore
        items=list_images, name="Image")

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        get_mcblend(context.object).render_controllers[
            self.rc_index  # type: ignore
        ].texture = self.image  # type: ignore
        return {'FINISHED'}


class MCBLEND_OT_FakeRcOpenTexture(  # pyright: ignore[reportIncompatibleMethodOverride]
        Operator, ImportHelper):
    '''Opens a texture from a file for render controller of a model.'''
    bl_idname = "mcblend.fake_rc_open_texture"
    bl_label = "Open texture"
    bl_description = (
        "Load a texture from a file and assign it to the render controller")
    bl_options = {'UNDO', 'INTERNAL'}

    filename_ext = ".png"
    filter_glob: StringProperty(  # type: ignore
        default="*.png;*.jpg;*.jpeg;*.bmp;*.tga",
        options={'HIDDEN'},
    )

    rc_index: IntProperty(options={'HIDDEN'})  # type: ignore

    if TYPE_CHECKING:
        filepath: str

    def list_images(self, context: Context):
        '''Lists images for dropdown list'''
        # pylint: disable=unused-argument
        items = [
            (x.name, x.name, x.name)
            for x in bpy.data.images]
        return items

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        img = bpy.data.images.load(
            self.filepath, check_existing=True)
        get_mcblend(context.object).render_controllers[
            self.rc_index  # type: ignore
        ].texture = img.name
        return {'FINISHED'}

# Armature render controllers materials
class MCBLEND_OT_AddFakeRcMaterial(Operator):
    '''
    Adds new material to active render controller of active model (armature)
    '''
    bl_idname = "mcblend.add_fake_rc_material"
    bl_label = "Add material"
    bl_description = "Add new material to this render controller"
    bl_options = {'UNDO', 'INTERNAL'}

    rc_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        rc = get_mcblend(context.object).render_controllers[
            self.rc_index]  # type: ignore
        material = rc.materials.add()
        material.pattern = '*'
        material.material = 'entity_alphatest'
        return {'FINISHED'}

class MCBLEND_OT_RemoveFakeRcMaterial(Operator):
    '''
    Removes material from active render controller of active model (armature).
    '''
    bl_idname = "mcblend.remove_fake_rc_material"
    bl_label = "Remove material"
    bl_description = "Remove this material from this render controller"
    bl_options = {'UNDO', 'INTERNAL'}

    rc_index: IntProperty()  # type: ignore
    material_index: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        if context.object is None:
            return {'CANCELLED'}
        get_mcblend(context.object).render_controllers[
            self.rc_index  # type: ignore
        ].materials.remove(
            self.material_index  # type: ignore
        )
        return {'FINISHED'}

class MCBLEND_OT_MoveFakeRcMaterial(Operator):
    '''
    Moves material of active render controller in active model to a
    different spot on the list.
    '''
    bl_idname = "mcblend.move_fake_rc_material"
    bl_label = "Move material"
    bl_description = (
        "Change the order of the materials in the render controller")
    bl_options = {'UNDO', 'INTERNAL'}

    rc_index: IntProperty()  # type: ignore
    material_index: IntProperty()  # type: ignore
    move_to: IntProperty()  # type: ignore

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        get_mcblend(
            obj
        ).render_controllers[
            self.rc_index  # type: ignore
        ].materials.move(self.material_index, self.move_to)  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_FakeRcSMaterailSelectTemplate(Operator):
    '''Selects the material type.'''
    bl_idname = "mcblend.fake_rc_material_select_template"
    bl_label = "Select material"
    bl_description = "Select the material used by this render controller"
    bl_options = {'UNDO', 'INTERNAL'}

    material: bpy.props.EnumProperty(  # type: ignore
        items=[(i, i, i) for i in MATERIALS_MAP], name="Material")

    rc_index: IntProperty(options={'HIDDEN'})  # type: ignore
    material_index: IntProperty(options={'HIDDEN'})  # type: ignore

    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        get_mcblend(
            obj
        ).render_controllers[
            self.rc_index  # type: ignore
        ].materials[
            self.material_index  # type: ignore
        ].material = self.material  # type: ignore
        return {'FINISHED'}

class MCBLEND_OT_FakeRcApplyMaterials(Operator):
    '''Applies the materials to the model'''
    bl_idname = "mcblend.fake_rc_apply_materials"
    bl_label = "Apply materials"
    bl_description = (
        "Apply the render controllers to create materials for the model")
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: Context):
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        apply_materials(context)
        return {'FINISHED'}

# Automation
class MCBLEND_OT_PreparePhysicsSimulation(Operator):
    '''Operator used for adding objects used for rigid body simulation.'''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.prepare_physics_simulation"
    bl_label = "Prepare physics simulation"
    bl_options = {'REGISTER'}
    bl_description = (
        "Create objects used for the rigid body simulation")

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        obj = context.object
        if obj is None:
            return False
        return obj.type == 'ARMATURE'

    def execute(self, context: Context):
        prepare_physics_simulation(context)
        return {'FINISHED'}

class MCBLEND_OT_MergeModels(Operator):
    '''
    Merges all selected models. A model can be selected by selecting its
    armature. The merge models operation also creates new combined textures
    so that they can be easily imported into Minecraft.
    '''
    # pylint: disable=unused-argument, no-member
    bl_idname = "mcblend.merge_models"
    bl_label = "Merge models"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Merge models of all selected armatures and create new textures for "
        "them"
    )

    def draw(self, context: Context):
        layout = self.layout
        layout.label(
            text="You're about to merge multiple using their main textures")
        row = layout.row()
        # layout.operator("mcblend.fix_uv")
        selected_objects = context.selected_objects
        for obj in selected_objects:
            if obj.type != 'ARMATURE':
                continue
            obj_mcblend = get_mcblend(obj)
            if len(obj_mcblend.render_controllers) == 0:
                continue
            rc = obj_mcblend.render_controllers[0]
            row = layout.row()
            row.label(text=f'geometry.{obj_mcblend.model_name}')
            row.label(text=rc.texture)


    def invoke(self, context: Context, event: Event):
        return context.window_manager.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context: Context):
        if context.mode != 'OBJECT':
            return False
        selected_objects = context.selected_objects
        for obj in selected_objects:
            if obj.type == 'ARMATURE':
                return True
        return False

    def execute(self, context: Context):
        merge_models(context)
        return {'FINISHED'}
