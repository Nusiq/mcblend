import bpy
from bpy.props import PointerProperty, BoolProperty, FloatVectorProperty
import bmesh
import mathutils


from .operator import (
    OBJECT_OT_NusiqBmodelExportOperator, OBJECT_OT_NusiqBmodelExportAnimationOperator,
    OBJECT_OT_NusiqBmodelParentOperator, menu_bedrock_parent,
    OBJECT_OT_NusiqBmodelParentClearOperator, menu_bedrock_parent_clear,
    OBJECT_OT_NusiqBmodelMapUvOperator,
)
from .panel import (
    OBJECT_PT_NusiqBmodelExportPanel,
    OBJECT_NusiqBmodelExporterProperties,
    OBJECT_PT_NusiqBmodelExportAnimationPanel
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
    OBJECT_OT_NusiqBmodelExportOperator,
    OBJECT_OT_NusiqBmodelExportAnimationOperator,
    OBJECT_PT_NusiqBmodelExportAnimationPanel,
    OBJECT_PT_NusiqBmodelExportPanel,
    OBJECT_NusiqBmodelExporterProperties,
    OBJECT_OT_NusiqBmodelParentOperator,
    OBJECT_OT_NusiqBmodelParentClearOperator,
    OBJECT_OT_NusiqBmodelMapUvOperator,
)


def register():
    for _class in classes:
        bpy.utils.register_class(_class)
    bpy.types.Scene.nusiq_bmodel = PointerProperty(
        type=OBJECT_NusiqBmodelExporterProperties
    )
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.append(menu_bedrock_parent_clear)


def unregister():
    for _class in reversed(classes):
        bpy.utils.unregister_class(_class)
    del bpy.types.Scene.nusiq_bmodel
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent)
    bpy.types.VIEW3D_MT_object_parent.remove(menu_bedrock_parent_clear)
