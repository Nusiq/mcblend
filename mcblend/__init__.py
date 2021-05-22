'''
This module is used by Blender to register/unregister the plugin.
'''
# don't import future annotations Blender needs that
import bpy
from bpy.props import (
    PointerProperty, CollectionProperty,
    IntProperty, EnumProperty)


from .operator import (
    NUSIQ_MCBLEND_OT_ExportModel, NUSIQ_MCBLEND_OT_ExportAnimation,
    NUSIQ_MCBLEND_OT_MapUv, NUSIQ_MCBLEND_OT_UvGroup,
    NUSIQ_MCBLEND_OT_FixUv, menu_func_nusiq_mcblend_fix_uv,
    NUSIQ_MCBLEND_OT_ClearUvGroup,
    NUSIQ_MCBLEND_OT_ToggleIsBone,
    NUSIQ_MCBLEND_OT_ToggleMirror,
    NUSIQ_MCBLEND_OT_SetInflate,
    menu_func_nusiq_mcblend_export_model, menu_func_nusiq_mcblend_export_animation,
    NUSIQ_MCBLEND_OT_RoundDimensions,
    NUSIQ_MCBLEND_OT_SeparateMeshCubes,
    NUSIQ_MCBLEND_OT_ImportModel, menu_func_nusiq_mcblend_import_model,

    NUSIQ_MCBLEND_OT_ListAnimations,
    NUSIQ_MCBLEND_OT_AddAnimation,
    NUSIQ_MCBLEND_OT_RemoveAnimation,


    NUSIQ_MCBLEND_OT_ListUvGroups,
    NUSIQ_MCBLEND_OT_AddUvGroup,
    NUSIQ_MCBLEND_OT_RemoveUvGroup,
    NUSIQ_MCBLEND_OT_AddUvMask,
    NUSIQ_MCBLEND_OT_RemoveUvMask,
    NUSIQ_MCBLEND_OT_MoveUvMask,
    NUSIQ_MCBLEND_OT_CopyUvGroupSide,
    NUSIQ_MCBLEND_OT_AddUvMaskColor,
    NUSIQ_MCBLEND_OT_RemoveUvMaskColor,
    NUSIQ_MCBLEND_OT_MoveUvMaskColor,
    NUSIQ_MCBLEND_OT_AddUvMaskStripe,
    NUSIQ_MCBLEND_OT_RemoveUvMaskStripe,
    NUSIQ_MCBLEND_OT_MoveUvMaskStripe,

    NUSIQ_MCBLEND_OT_ExportUvGroup,
    NUSIQ_MCBLEND_OT_ImportUvGroup,

    NUSIQ_MCBLEND_OT_AddEvent,
    NUSIQ_MCBLEND_OT_RemoveEvent,
    NUSIQ_MCBLEND_OT_AddEffect,
    NUSIQ_MCBLEND_OT_RemoveEffect,

    NUSIQ_MCBLEND_OT_ImportRpEntity,
    NUSIQ_MCBLEND_OT_ReloadRp,
)
from .custom_properties import (
    NUSIQ_MCBLEND_JustName,
    NUSIQ_MCBLEND_NameValuePair,
    NUSIQ_MCBLEND_ExporterProperties,
    NUSIQ_MCBLEND_ProjectEntitiesProperties,
    NUSIQ_MCBLEND_ProjectProperties,
    NUSIQ_MCBLEND_TimelineMarkerProperties,
    NUSIQ_MCBLEND_AnimationProperties,
    NUSIQ_MCBLEND_ObjectProperties,
    NUSIQ_MCBLEND_StripeProperties,
    NUSIQ_MCBLEND_ColorProperties,
    NUSIQ_MCBLEND_UvMaskProperties,
    NUSIQ_MCBLEND_UvGroupProperties,
    NUSIQ_MCBLEND_EffectProperties,
    NUSIQ_MCBLEND_EventProperties,
)

from .panel import (
    NUSIQ_MCBLEND_PT_ObjectPropertiesPanel,
    NUSIQ_MCBLEND_PT_ModelPropertiesPanel,
    NUSIQ_MCBLEND_PT_AnimationPropertiesPanel,
    NUSIQ_MCBLEND_PT_UvMappingPanel,
    NUSIQ_MCBLEND_PT_OperatorsPanel,
    NUSIQ_MCBLEND_PT_UVGroupPanel,
    NUSIQ_MCBLEND_UL_UVGroupList,
    NUSIQ_MCBLEND_PT_EventsPanel,
    NUSIQ_MCBLEND_UL_EventsList,
    NUSIQ_MCBLEND_PT_ProjectPanel,
)


bl_info = {
    "name": "Mcblend",
    "author": "Artur",
    "description": "Minecraft Bedrock Edition addon for creating entity models and animations.",
    "blender": (2, 80, 0),
    "version": (7, 0, 2),  # COMPATIBILITY BREAKING CHANGE, NEW FEATURE, BUGFIX
    "location": "",
    "warning": "",
    "category": "Object"
}


classes = (
    NUSIQ_MCBLEND_JustName,
    NUSIQ_MCBLEND_NameValuePair,

    NUSIQ_MCBLEND_ExporterProperties,

    NUSIQ_MCBLEND_ProjectEntitiesProperties,
    NUSIQ_MCBLEND_ProjectProperties,

    NUSIQ_MCBLEND_EffectProperties,
    NUSIQ_MCBLEND_EventProperties,
    NUSIQ_MCBLEND_TimelineMarkerProperties,
    NUSIQ_MCBLEND_AnimationProperties,

    NUSIQ_MCBLEND_PT_ObjectPropertiesPanel,
    NUSIQ_MCBLEND_OT_ExportModel,
    NUSIQ_MCBLEND_OT_ExportAnimation,
    NUSIQ_MCBLEND_PT_AnimationPropertiesPanel,
    NUSIQ_MCBLEND_PT_ModelPropertiesPanel,
    NUSIQ_MCBLEND_OT_MapUv,
    NUSIQ_MCBLEND_OT_FixUv,
    NUSIQ_MCBLEND_PT_UvMappingPanel,
    NUSIQ_MCBLEND_OT_UvGroup,
    NUSIQ_MCBLEND_OT_ClearUvGroup,
    NUSIQ_MCBLEND_OT_ToggleIsBone,
    NUSIQ_MCBLEND_OT_ToggleMirror,
    NUSIQ_MCBLEND_PT_OperatorsPanel,
    NUSIQ_MCBLEND_OT_SetInflate,
    NUSIQ_MCBLEND_OT_RoundDimensions,
    NUSIQ_MCBLEND_OT_SeparateMeshCubes,
    NUSIQ_MCBLEND_OT_ImportModel,
    NUSIQ_MCBLEND_PT_UVGroupPanel,
    NUSIQ_MCBLEND_UL_UVGroupList,


    NUSIQ_MCBLEND_OT_AddEvent,
    NUSIQ_MCBLEND_OT_RemoveEvent,
    NUSIQ_MCBLEND_OT_AddEffect,
    NUSIQ_MCBLEND_OT_RemoveEffect,
    NUSIQ_MCBLEND_PT_EventsPanel,
    NUSIQ_MCBLEND_UL_EventsList,


    NUSIQ_MCBLEND_OT_ListAnimations,
    NUSIQ_MCBLEND_OT_AddAnimation,
    NUSIQ_MCBLEND_OT_RemoveAnimation,

    NUSIQ_MCBLEND_OT_ListUvGroups,
    NUSIQ_MCBLEND_OT_AddUvGroup,
    NUSIQ_MCBLEND_OT_RemoveUvGroup,
    NUSIQ_MCBLEND_OT_AddUvMask,
    NUSIQ_MCBLEND_OT_RemoveUvMask,
    NUSIQ_MCBLEND_OT_MoveUvMask,
    NUSIQ_MCBLEND_OT_CopyUvGroupSide,
    NUSIQ_MCBLEND_OT_AddUvMaskColor,
    NUSIQ_MCBLEND_OT_RemoveUvMaskColor,
    NUSIQ_MCBLEND_OT_MoveUvMaskColor,
    NUSIQ_MCBLEND_OT_AddUvMaskStripe,
    NUSIQ_MCBLEND_OT_RemoveUvMaskStripe,
    NUSIQ_MCBLEND_OT_MoveUvMaskStripe,

    NUSIQ_MCBLEND_ObjectProperties,

    NUSIQ_MCBLEND_StripeProperties,
    NUSIQ_MCBLEND_ColorProperties,
    NUSIQ_MCBLEND_UvMaskProperties,  # must be before UvGroupProperties
    NUSIQ_MCBLEND_UvGroupProperties,

    NUSIQ_MCBLEND_OT_ExportUvGroup,
    NUSIQ_MCBLEND_OT_ImportUvGroup,

    NUSIQ_MCBLEND_OT_ImportRpEntity,
    NUSIQ_MCBLEND_OT_ReloadRp,
    NUSIQ_MCBLEND_PT_ProjectPanel,
)

def register():
    '''Registers the plugin'''
    # pylint: disable=assignment-from-no-return, no-member
    for _class in classes:
        bpy.utils.register_class(_class)

    # Model export properties (the scope is the whole scene)
    bpy.types.Scene.nusiq_mcblend = PointerProperty(
        type=NUSIQ_MCBLEND_ExporterProperties)

    # Project properties
    bpy.types.Scene.nusiq_mcblend_project = PointerProperty(
        type=NUSIQ_MCBLEND_ProjectProperties
    )

    # Animation properties
    bpy.types.Scene.nusiq_mcblend_active_animation = IntProperty(
        default=0)
    bpy.types.Scene.nusiq_mcblend_animations = CollectionProperty(
        type=NUSIQ_MCBLEND_AnimationProperties)

    # Events
    bpy.types.Scene.nusiq_mcblend_events = CollectionProperty(
        type=NUSIQ_MCBLEND_EventProperties)
    bpy.types.Scene.nusiq_mcblend_active_event = IntProperty(
        default=0)

    # UV Groups
    bpy.types.Scene.nusiq_mcblend_active_uv_group = IntProperty(
        default=0)
    bpy.types.Scene.nusiq_mcblend_uv_groups = CollectionProperty(
        type=NUSIQ_MCBLEND_UvGroupProperties)

    sides = [(str(i), f'side{i+1}', f'side{i+1}') for i in range(6)]
    bpy.types.Scene.nusiq_mcblend_active_uv_groups_side = EnumProperty(
        items=sides, name="Face")

    # Object properties
    bpy.types.Object.nusiq_mcblend_object_properties = PointerProperty(
        type=NUSIQ_MCBLEND_ObjectProperties)

    # Append operators to the F3 menu
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_nusiq_mcblend_export_model
    )
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_nusiq_mcblend_export_animation
    )
    bpy.types.TOPBAR_MT_file_import.append(
        menu_func_nusiq_mcblend_import_model
    )

def unregister():
    '''Unregisters the plugin'''
    # pylint: disable=no-member
    for _class in reversed(classes):
        bpy.utils.unregister_class(_class)
    del bpy.types.Scene.nusiq_mcblend
    bpy.types.TOPBAR_MT_file_export.remove(
        menu_func_nusiq_mcblend_export_model
    )
    bpy.types.TOPBAR_MT_file_export.remove(
        menu_func_nusiq_mcblend_export_animation
    )
    bpy.types.TOPBAR_MT_file_import.remove(
        menu_func_nusiq_mcblend_import_model
    )
