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


import bpy
from .operators import NUSIQ_OT_MainOperator
from .panels import NUSIQ_PT_ExportPanel

classes = (NUSIQ_OT_MainOperator, NUSIQ_PT_ExportPanel)

register, unregister = bpy.utils.register_classes_factory(classes)
