import bpy

from bpy.props import StringProperty, PointerProperty
from bpy.types import Operator, AddonPreferences

import pathlib


class OBJECT_BedrockExporterProperties(bpy.types.PropertyGroup):
    path: StringProperty(
        name="",
        description="Path to Directory",
        default=(
            f"{pathlib.Path.home()}/AppData/Local/Packages/"
            "Microsoft.MinecraftUWP_8wekyb3d8bbwe/LocalState/games/"
            "com.mojang/minecraftWorlds/"
        ),
        maxlen=1024,
        subtype='FILE_PATH',
    )

    model_name: StringProperty(
        name="",
        description="Name of the model",
        default="b_model",
        maxlen=1024
    )


class OBJECT_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export bedrock model"
    bl_category = "Export Bedrock Model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.bedrock_exporter, "path", text="")
        col.prop(
            context.scene.bedrock_exporter, "model_name", text="Name"
        )

        self.layout.row().operator(
            "object.export_operator", text="Export"
        )
