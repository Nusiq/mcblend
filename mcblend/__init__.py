'''
This module is used by Blender to register/unregister the plugin.
'''
# don't import future annotations Blender needs that
import bpy
from bpy.props import (
    PointerProperty, BoolProperty, FloatVectorProperty, CollectionProperty,
    IntProperty)
import mathutils


from .operator import (
    OBJECT_OT_NusiqMcblendExportModelOperator, OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_OT_NusiqMcblendMapUvOperator, OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMcMirrorOperator,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
    menu_func_nusiq_mcblend_export_model, menu_func_nusiq_mcblend_export_animation,
    OBJECT_OT_NusiqMcblendRoundDimensionsOperator,
    OBJECT_OT_NusiqMcblendImport, menu_func_nusiq_mcblend_import,

    OBJECT_OT_NusiqMcblendListAnimations,
    OBJECT_OT_NusiqMcblendAddAnimation,
    OBJECT_OT_NusiqMcblendRemoveAnimation,
)
from .panel import (
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_NusiqMcblendAnimationProperties,

    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_PT_NusiqMcblendOperatorsPanel,
    OBJECT_PT_NusiqMcblendImportPanel,
)


bl_info = {
    "name": "Mcblend",
    "author": "Artur",
    "description": "",
    "blender": (2, 80, 0),
    "version": (4, 0, 1),  # COMPATIBILITY BREAKING CHANGE, NEW FEATURE, BUGFIX
    "location": "",
    "warning": "",
    "category": "Generic"
}


classes = (
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_NusiqMcblendAnimationProperties,

    OBJECT_OT_NusiqMcblendExportModelOperator,
    OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_OT_NusiqMcblendMapUvOperator,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMcMirrorOperator,
    OBJECT_PT_NusiqMcblendOperatorsPanel,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
    OBJECT_OT_NusiqMcblendRoundDimensionsOperator,
    OBJECT_OT_NusiqMcblendImport,
    OBJECT_PT_NusiqMcblendImportPanel,

    OBJECT_OT_NusiqMcblendListAnimations,
    OBJECT_OT_NusiqMcblendAddAnimation,
    OBJECT_OT_NusiqMcblendRemoveAnimation,
)

def register():
    '''Register the plugin'''
    # pylint: disable=assignment-from-no-return, no-member
    for _class in classes:
        bpy.utils.register_class(_class)
    
    # Add properties to Scene
    bpy.types.Scene.nusiq_mcblend = PointerProperty(
        type=OBJECT_NusiqMcblendExporterProperties
    )
    bpy.types.Scene.nusiq_mcblend_animations = CollectionProperty(
        type=OBJECT_NusiqMcblendAnimationProperties)
    bpy.types.Scene.nusiq_mcblend_active_animation = bpy.props.IntProperty(
        default=0)

    # Add properties to objects
    # TODO - implement

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
    '''Unregister the plugin'''
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
