import bpy
from bpy.props import PointerProperty, BoolProperty, FloatVectorProperty
import bmesh
import mathutils


from .operator import (
    OBJECT_OT_NusiqMcblendExportOperator, OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_OT_NusiqMcblendParentOperator, menu_bedrock_parent,
    OBJECT_OT_NusiqMcblendParentClearOperator, menu_bedrock_parent_clear,
    OBJECT_OT_NusiqMcblendMapUvOperator, OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMcMirrorOperator,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
)
from .panel import (
    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_PT_NusiqMcblendCustomPropertiesPanel,
)


bl_info = {
    "name": "Mcblend",
    "author": "Artur",
    "description": "",
    "blender": (2, 80, 0),
    "version": (1, 0, 1),  # COMPATIBILITY BREAKING CHANGE, NEW FEATURE, BUGFIX
    "location": "",
    "warning": "",
    "category": "Generic"
}


classes = (
    OBJECT_OT_NusiqMcblendExportOperator,
    OBJECT_OT_NusiqMcblendExportAnimationOperator,
    OBJECT_PT_NusiqMcblendExportAnimationPanel,
    OBJECT_PT_NusiqMcblendExportPanel,
    OBJECT_NusiqMcblendExporterProperties,
    OBJECT_OT_NusiqMcblendParentOperator,
    OBJECT_OT_NusiqMcblendParentClearOperator,
    OBJECT_OT_NusiqMcblendMapUvOperator,
    OBJECT_PT_NusiqMcblendSetUvsPanel,
    OBJECT_OT_NusiqMcblendUvGroupOperator,
    OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator,
    OBJECT_OT_NusiqMcblendToggleMcMirrorOperator,
    OBJECT_PT_NusiqMcblendCustomPropertiesPanel,
    OBJECT_OT_NusiqMcblendSetInflateOperator,
)


def register():
    for _class in classes:
        bpy.utils.register_class(_class)
    bpy.types.Scene.nusiq_mcblend = PointerProperty(
        type=OBJECT_NusiqMcblendExporterProperties
    )
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent_clear)


def unregister():
    for _class in reversed(classes):
        bpy.utils.unregister_class(_class)
    del bpy.types.Scene.nusiq_mcblend
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent_clear)
