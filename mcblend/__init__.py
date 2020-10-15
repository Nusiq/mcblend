'''
This module is used by Blender to register/unregister the plugin.
'''
# don't import future annotations Blender needs that
import bpy
from bpy.props import (
    PointerProperty, BoolProperty, FloatVectorProperty, CollectionProperty,
    IntProperty, EnumProperty)


from .operator import (
    OBJECT_OT_NusiqMcblendExportModelOperator, OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_OT_NusiqMcblendMapUvOperator, OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendClearUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMirrorOperator,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
    menu_func_nusiq_mcblend_export_model, menu_func_nusiq_mcblend_export_animation,
    OBJECT_OT_NusiqMcblendRoundDimensionsOperator,
    OBJECT_OT_NusiqMcblendImport, menu_func_nusiq_mcblend_import,

    OBJECT_OT_NusiqMcblendListAnimations,
    OBJECT_OT_NusiqMcblendAddAnimation,
    OBJECT_OT_NusiqMcblendRemoveAnimation,


    OBJECT_OT_NusiqMcblendListUvGroups,
    OBJECT_OT_NusiqMcblendAddUvGroup,
    OBJECT_OT_NusiqMcblendRemoveUvGroup,
    OBJECT_OT_NusiqMcblendAddUvMask,
    OBJECT_OT_NusiqMcblendRemoveUvMask,
    OBJECT_OT_NusiqMcblendMoveUvMask,
    OBJECT_OT_NusiqMcblendCopyUvGroupSide,
    OBJECT_OT_NusiqMcblendAddUvMaskColor,
    OBJECT_OT_NusiqMcblendRemoveUvMaskColor,
    OBJECT_OT_NusiqMcblendMoveUvMaskColor,
    OBJECT_OT_NusiqMcblendAddUvMaskStripe,
    OBJECT_OT_NusiqMcblendRemoveUvMaskStripe,
    OBJECT_OT_NusiqMcblendMoveUvMaskStripe,
)
from .panel import (
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_NusiqMcblendAnimationProperties,

    OBJECT_NusiqMcblendObjectProperties,

    OBJECT_PT_NusiqMcblendObjectPropertiesPanel,
    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_PT_NusiqMcblendOperatorsPanel,
    OBJECT_PT_NusiqMcblendImportPanel,
    OBJECT_PT_NusiqMcblendUVGroupPanel,
    OBJECT_UL_NusiqMcblendUVGroupList,

    OBJECT_NusiqMcblendStripeProperties,
    OBJECT_NusiqMcblendColorProperties,
    OBJECT_NusiqMcblendUvMaskProperties,
    OBJECT_NusiqMcblendUvGroupProperties,
)


bl_info = {
    "name": "Mcblend",
    "author": "Artur",
    "description": "",
    "blender": (2, 80, 0),
    "version": (5, 0, 4),  # COMPATIBILITY BREAKING CHANGE, NEW FEATURE, BUGFIX
    "location": "",
    "warning": "",
    "category": "Generic"
}


classes = (
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_NusiqMcblendAnimationProperties,

    OBJECT_PT_NusiqMcblendObjectPropertiesPanel,
    OBJECT_OT_NusiqMcblendExportModelOperator,
    OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_OT_NusiqMcblendMapUvOperator,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendClearUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMirrorOperator,
    OBJECT_PT_NusiqMcblendOperatorsPanel,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
    OBJECT_OT_NusiqMcblendRoundDimensionsOperator,
    OBJECT_OT_NusiqMcblendImport,
    OBJECT_PT_NusiqMcblendImportPanel,
    OBJECT_PT_NusiqMcblendUVGroupPanel,
    OBJECT_UL_NusiqMcblendUVGroupList,

    OBJECT_OT_NusiqMcblendListAnimations,
    OBJECT_OT_NusiqMcblendAddAnimation,
    OBJECT_OT_NusiqMcblendRemoveAnimation,

    OBJECT_OT_NusiqMcblendListUvGroups,
    OBJECT_OT_NusiqMcblendAddUvGroup,
    OBJECT_OT_NusiqMcblendRemoveUvGroup,
    OBJECT_OT_NusiqMcblendAddUvMask,
    OBJECT_OT_NusiqMcblendRemoveUvMask,
    OBJECT_OT_NusiqMcblendMoveUvMask,
    OBJECT_OT_NusiqMcblendCopyUvGroupSide,
    OBJECT_OT_NusiqMcblendAddUvMaskColor,
    OBJECT_OT_NusiqMcblendRemoveUvMaskColor,
    OBJECT_OT_NusiqMcblendMoveUvMaskColor,
    OBJECT_OT_NusiqMcblendAddUvMaskStripe,
    OBJECT_OT_NusiqMcblendRemoveUvMaskStripe,
    OBJECT_OT_NusiqMcblendMoveUvMaskStripe,

    OBJECT_NusiqMcblendObjectProperties,

    OBJECT_NusiqMcblendStripeProperties,
    OBJECT_NusiqMcblendColorProperties,
    OBJECT_NusiqMcblendUvMaskProperties,  # must be before UvGroupProperties
    OBJECT_NusiqMcblendUvGroupProperties,
)

def register():
    '''Registers the plugin'''
    # pylint: disable=assignment-from-no-return, no-member
    for _class in classes:
        bpy.utils.register_class(_class)

    # Model export properties (the scope is the whole scene)
    bpy.types.Scene.nusiq_mcblend = PointerProperty(
        type=OBJECT_NusiqMcblendExporterProperties)

    # Animation properties
    bpy.types.Scene.nusiq_mcblend_active_animation = IntProperty(
        default=0)
    bpy.types.Scene.nusiq_mcblend_animations = CollectionProperty(
        type=OBJECT_NusiqMcblendAnimationProperties)

    # UV Groups
    bpy.types.Scene.nusiq_mcblend_active_uv_group = IntProperty(
        default=0)
    bpy.types.Scene.nusiq_mcblend_uv_groups = CollectionProperty(
        type=OBJECT_NusiqMcblendUvGroupProperties)

    sides = [(str(i), f'side{i+1}', f'side{i+1}') for i in range(6)]
    bpy.types.Scene.nusiq_mcblend_active_uv_groups_side = EnumProperty(
        items=sides, name="Face")

    # Object properties
    bpy.types.Object.nusiq_mcblend_object_properties = PointerProperty(
        type=OBJECT_NusiqMcblendObjectProperties)

    # Append operators to the F3 menu
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_nusiq_mcblend_export_model
    )
    bpy.types.TOPBAR_MT_file_export.append(
        menu_func_nusiq_mcblend_export_animation
    )
    bpy.types.TOPBAR_MT_file_import.append(
        menu_func_nusiq_mcblend_import
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
        menu_func_nusiq_mcblend_import
    )
