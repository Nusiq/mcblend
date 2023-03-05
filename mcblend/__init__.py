'''
This module is used by Blender to register/unregister the plugin.
'''
# don't import future annotations Blender needs that
import bpy
from bpy.props import (
    PointerProperty, CollectionProperty,
    IntProperty, EnumProperty)


from .operator import (
    MCBLEND_OT_ExportModel, MCBLEND_OT_ExportAnimation,
    MCBLEND_OT_MapUv, MCBLEND_OT_UvGroup,
    MCBLEND_OT_FixUv,
    MCBLEND_OT_ClearUvGroup,
    MCBLEND_OT_SetInflate,
    menu_func_mcblend_export_model, menu_func_mcblend_export_animation,
    MCBLEND_OT_SeparateMeshCubes,
    MCBLEND_OT_ImportModel, menu_func_mcblend_import_model,

    MCBLEND_OT_ListAnimations,
    MCBLEND_OT_AddAnimation,
    MCBLEND_OT_RemoveAnimation,


    MCBLEND_OT_ListUvGroups,
    MCBLEND_OT_AddUvGroup,
    MCBLEND_OT_RemoveUvGroup,
    MCBLEND_OT_AddUvMask,
    MCBLEND_OT_RemoveUvMask,
    MCBLEND_OT_MoveUvMask,
    MCBLEND_OT_CopyUvGroupSide,
    MCBLEND_OT_AddUvMaskColor,
    MCBLEND_OT_RemoveUvMaskColor,
    MCBLEND_OT_MoveUvMaskColor,
    MCBLEND_OT_AddUvMaskStripe,
    MCBLEND_OT_RemoveUvMaskStripe,
    MCBLEND_OT_MoveUvMaskStripe,

    MCBLEND_OT_ExportUvGroup,
    MCBLEND_OT_ImportUvGroup,

    MCBLEND_OT_AddEvent,
    MCBLEND_OT_RemoveEvent,
    MCBLEND_OT_AddEffect,
    MCBLEND_OT_RemoveEffect,

    MCBLEND_OT_ImportRpEntity,
    MCBLEND_OT_ImportAttachable,
    MCBLEND_OT_LoadRp,
    MCBLEND_OT_UnloadRps,
    MCBLEND_OT_LoadDatabase,
    MCBLEND_OT_SaveDatabase,

    MCBLEND_OT_AddFakeRc,
    MCBLEND_OT_RemoveFakeRc,
    MCBLEND_OT_MoveFakeRc,
    MCBLEND_OT_FakeRcSelectTexture,
    MCBLEND_OT_FakeRcOpenTexture,
    MCBLEND_OT_AddFakeRcMaterial,
    MCBLEND_OT_RemoveFakeRcMaterial,
    MCBLEND_OT_MoveFakeRcMaterial,
    MCBLEND_OT_FakeRcSMaterailSelectTemplate,
    MCBLEND_OT_FakeRcApplyMaterials,
    MCBLEND_OT_PreparePhysicsSimulation,
    MCBLEND_OT_MergeModels,
)

from .common_data import (
    MCBLEND_JustName,
    MCBLEND_DbEntry,
)

from .resource_pack_data import (
    MCBLEND_EntityMaterialPattern,
    MCBLEND_EntityRenderController,
    MCBLEND_AttachableMaterialPattern,
    MCBLEND_AttachableRenderController,
    MCBLEND_ProjectProperties,
)

from .object_data import (
    MCBLEND_EffectProperties,
    MCBLEND_EventProperties,
    MCBLEND_TimelineMarkerProperties,
    MCBLEND_AnimationProperties,

    MCBLEND_FakeRcMaterialProperties,
    MCBLEND_FakeRcProperties,
    MCBLEND_ObjectProperties,
    MCBLEND_BoneProperties,
)
from .uv_data import (
    MCBLEND_StripeProperties,
    MCBLEND_ColorProperties,
    MCBLEND_UvMaskProperties,
    MCBLEND_UvGroupProperties,
)

from .panel import (
    MCBLEND_PT_ObjectPropertiesPanel,
    MCBLEND_PT_ModelPropertiesPanel,
    MCBLEND_PT_ArmatureRenderControllersPanel,
    MCBLEND_PT_AnimationPropertiesPanel,
    MCBLEND_PT_OperatorsPanel,
    MCBLEND_PT_UVGroupPanel,
    MCBLEND_UL_UVGroupList,
    MCBLEND_PT_EventsPanel,
    MCBLEND_UL_EventsList,
    MCBLEND_PT_ProjectPanel,
    MCBLEND_PT_BonePanel,
)

bl_info = {
    "name": "Mcblend",
    "author": "Artur",
    "description": "An addon that allows to design and animate Minecraft Bedrock Edition models",
    "blender": (3, 3, 0),
    "version": (10, 1, 0),  # Remember to update the version in the "docs/conf.py"
    "location": "",
    "warning": "",
    "category": "Object"
}

classes = (
    MCBLEND_JustName,
    MCBLEND_DbEntry,

    MCBLEND_EntityMaterialPattern,
    MCBLEND_EntityRenderController,
    MCBLEND_AttachableMaterialPattern,
    MCBLEND_AttachableRenderController,
    MCBLEND_ProjectProperties,

    MCBLEND_PT_ObjectPropertiesPanel,
    MCBLEND_PT_ModelPropertiesPanel,
    MCBLEND_PT_ArmatureRenderControllersPanel,
    MCBLEND_OT_ExportModel,
    MCBLEND_OT_ExportAnimation,
    MCBLEND_PT_AnimationPropertiesPanel,
    MCBLEND_OT_MapUv,
    MCBLEND_OT_FixUv,
    MCBLEND_OT_UvGroup,
    MCBLEND_OT_ClearUvGroup,
    MCBLEND_PT_OperatorsPanel,
    MCBLEND_OT_SetInflate,
    MCBLEND_OT_SeparateMeshCubes,
    MCBLEND_OT_ImportModel,
    MCBLEND_PT_UVGroupPanel,
    MCBLEND_UL_UVGroupList,


    MCBLEND_OT_AddEvent,
    MCBLEND_OT_RemoveEvent,
    MCBLEND_OT_AddEffect,
    MCBLEND_OT_RemoveEffect,
    MCBLEND_PT_EventsPanel,
    MCBLEND_UL_EventsList,


    MCBLEND_OT_ListAnimations,
    MCBLEND_OT_AddAnimation,
    MCBLEND_OT_RemoveAnimation,

    MCBLEND_OT_ListUvGroups,
    MCBLEND_OT_AddUvGroup,
    MCBLEND_OT_RemoveUvGroup,
    MCBLEND_OT_AddUvMask,
    MCBLEND_OT_RemoveUvMask,
    MCBLEND_OT_MoveUvMask,
    MCBLEND_OT_CopyUvGroupSide,
    MCBLEND_OT_AddUvMaskColor,
    MCBLEND_OT_RemoveUvMaskColor,
    MCBLEND_OT_MoveUvMaskColor,
    MCBLEND_OT_AddUvMaskStripe,
    MCBLEND_OT_RemoveUvMaskStripe,
    MCBLEND_OT_MoveUvMaskStripe,

    MCBLEND_EffectProperties,
    MCBLEND_EventProperties,
    MCBLEND_TimelineMarkerProperties,
    MCBLEND_AnimationProperties,
    MCBLEND_FakeRcMaterialProperties,
    MCBLEND_FakeRcProperties,
    MCBLEND_ObjectProperties,
    MCBLEND_BoneProperties,

    MCBLEND_StripeProperties,
    MCBLEND_ColorProperties,
    MCBLEND_UvMaskProperties,  # must be before UvGroupProperties
    MCBLEND_UvGroupProperties,

    MCBLEND_OT_ExportUvGroup,
    MCBLEND_OT_ImportUvGroup,

    MCBLEND_OT_ImportRpEntity,
    MCBLEND_OT_ImportAttachable,
    MCBLEND_OT_LoadRp,
    MCBLEND_OT_UnloadRps,
    MCBLEND_OT_LoadDatabase,
    MCBLEND_OT_SaveDatabase,
    MCBLEND_PT_ProjectPanel,
    MCBLEND_PT_BonePanel,

    MCBLEND_OT_AddFakeRc,
    MCBLEND_OT_RemoveFakeRc,
    MCBLEND_OT_MoveFakeRc,
    MCBLEND_OT_FakeRcSelectTexture,
    MCBLEND_OT_FakeRcOpenTexture,
    MCBLEND_OT_AddFakeRcMaterial,
    MCBLEND_OT_RemoveFakeRcMaterial,
    MCBLEND_OT_MoveFakeRcMaterial,
    MCBLEND_OT_FakeRcSMaterailSelectTemplate,
    MCBLEND_OT_FakeRcApplyMaterials,
    MCBLEND_OT_PreparePhysicsSimulation,
    MCBLEND_OT_MergeModels,
)

def register():
    '''Registers the plugin'''
    # pylint: disable=assignment-from-no-return, no-member
    for _class in classes:
        bpy.utils.register_class(_class)

    # Project properties
    bpy.types.Scene.mcblend_project = PointerProperty(
        type=MCBLEND_ProjectProperties
    )

    # Events
    bpy.types.Scene.mcblend_events = CollectionProperty(
        type=MCBLEND_EventProperties)
    bpy.types.Scene.mcblend_active_event = IntProperty(
        default=0)

    # UV Groups
    bpy.types.Scene.mcblend_active_uv_group = IntProperty(
        default=0)
    bpy.types.Scene.mcblend_uv_groups = CollectionProperty(
        type=MCBLEND_UvGroupProperties)

    sides = [
        ("0", "Left", "The left side of the cube"),
        ("1", "Front", "The front side of the cube"),
        ("2", "Right", "The right side of the cube"),
        ("3", "Back", "The back side of the cube"),
        ("4", "Top", "The top side of the cube"),
        ("5", "Bottom", "The bottom side of the cube")
    ]
    bpy.types.Scene.mcblend_active_uv_groups_side = EnumProperty(
        items=sides, name="Face")

    # Object properties
    bpy.types.Object.mcblend = PointerProperty(
        type=MCBLEND_ObjectProperties)

    # Pose bone properties
    bpy.types.PoseBone.mcblend = PointerProperty(
        type=MCBLEND_BoneProperties)

    # Append operators to the F3 menu
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_mcblend_export_model
    )
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_mcblend_export_animation
    )
    bpy.types.TOPBAR_MT_file_import.append(
        menu_func_mcblend_import_model
    )

def unregister():
    '''Unregisters the plugin'''
    # pylint: disable=no-member
    for _class in reversed(classes):
        bpy.utils.unregister_class(_class)

    bpy.types.TOPBAR_MT_file_export.remove(
        menu_func_mcblend_export_model
    )
    bpy.types.TOPBAR_MT_file_export.remove(
        menu_func_mcblend_export_animation
    )
    bpy.types.TOPBAR_MT_file_import.remove(
        menu_func_mcblend_import_model
    )
