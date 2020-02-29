import bpy

from bpy.props import (
    StringProperty, PointerProperty, IntProperty, BoolProperty
)
from bpy.types import Operator, AddonPreferences

import pathlib


class OBJECT_BedrockExporterProperties(bpy.types.PropertyGroup):
    path: StringProperty(
        name="",
        description="Path to the file for exporting the model.",
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

    path_animation: StringProperty(
        name="",
        description="Path to the file for exporting the animation.",
        default=(
            f"{pathlib.Path.home()}/AppData/Local/Packages/"
            "Microsoft.MinecraftUWP_8wekyb3d8bbwe/LocalState/games/"
            "com.mojang/minecraftWorlds/"
        ),
        maxlen=1024,
        subtype='FILE_PATH',
    )
    loop_animation: BoolProperty(
        name="",
        description="Decides if animation should be looped.",
        default=True,
    )
    anim_time_update: StringProperty(
        name="",
        description="Adds anim_time_update value unless is left empty.",
        default="",
        maxlen=1024
    )
    animation_name: StringProperty(
        name="",
        description="Name of the animation.",
        default="b_model_animation",
        maxlen=1024
    )


class OBJECT_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export bedrock model"
    bl_category = "MC Bedrock exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.bedrock_exporter, "path", text="")
        col.prop(
            context.scene.bedrock_exporter, "model_name", text="Name"
        )
        self.layout.row().operator(
            "object.export_operator", text="Export model"
        )


class OBJECT_PT_ExportAnimationPanel(bpy.types.Panel):
    bl_label = "Export bedrock animation"
    bl_category = "MC Bedrock exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.bedrock_exporter, "path_animation", text="")
        col.prop(
            context.scene.bedrock_exporter, "animation_name", text="Name"
        )
        col.prop(
            context.scene.bedrock_exporter, "loop_animation", text="Loop"
        )
        col.prop(
            context.scene.bedrock_exporter, "anim_time_update", text="anim_time_update"
        )
        self.layout.row().operator(
            "object.export_animation_operator", text="Export animation"
        )
