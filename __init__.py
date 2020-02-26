import bpy
from bpy.props import PointerProperty, BoolProperty, FloatVectorProperty
import bmesh
import mathutils


from .operators import (
    OBJECT_OT_ExportOperator, OBJECT_OT_ExportAnimationOperator,
    OBJECT_OT_BedrockParentOperator, menu_bedrock_parent,
    OBJECT_OT_BedrockParentClearOperator, menu_bedrock_parent_clear,
)
from .panels import (
    OBJECT_PT_ExportPanel,
    OBJECT_BedrockExporterProperties,
    OBJECT_PT_ExportAnimationPanel
)


bl_info = {
    "name": "MC Bedrock Export",
    "author": "Artur",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


classes = (
    OBJECT_OT_ExportOperator,
    OBJECT_OT_ExportAnimationOperator,
    OBJECT_PT_ExportAnimationPanel,
    OBJECT_PT_ExportPanel,
    OBJECT_BedrockExporterProperties,
    OBJECT_OT_BedrockParentOperator,
    OBJECT_OT_BedrockParentClearOperator,
)


def register():
    for _class in classes:
        bpy.utils.register_class(_class)
    bpy.types.Scene.bedrock_exporter = PointerProperty(
        type=OBJECT_BedrockExporterProperties
    )
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent_clear)


def unregister():
    for _class in reversed(classes):
        bpy.utils.unregister_class(_class)
    del bpy.types.Scene.bedrock_exporter
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent_clear)
