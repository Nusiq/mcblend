import bpy

from bpy.props import (
    StringProperty, PointerProperty, IntProperty, BoolProperty
)
from bpy.types import Operator, AddonPreferences

import pathlib


class OBJECT_NusiqBmodelExporterProperties(bpy.types.PropertyGroup):
    path: StringProperty(  # type: ignore
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
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="b_model",
        maxlen=1024
    )

    path_animation: StringProperty(  # type: ignore
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
    loop_animation: BoolProperty(  # type: ignore
        name="",
        description="Decides if animation should be looped.",
        default=True,
    )
    anim_time_update: StringProperty(  # type: ignore
        name="",
        description="Adds anim_time_update value unless is left empty.",
        default="",
        maxlen=1024
    )
    animation_name: StringProperty(  # type: ignore
        name="",
        description="Name of the animation.",
        default="b_model_animation",
        maxlen=1024
    )


class OBJECT_PT_NusiqBmodelExportPanel(bpy.types.Panel):
    bl_label = "Export bedrock model"
    bl_category = "MC Bedrock exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.nusiq_bmodel, "path", text="")
        col.prop(
            context.scene.nusiq_bmodel, "model_name", text="Name"
        )
        self.layout.row().operator(
            "object.nusiq_bmodel_export_operator", text="Export model"
        )


class OBJECT_PT_NusiqBmodelExportAnimationPanel(bpy.types.Panel):
    bl_label = "Export bedrock animation"
    bl_category = "MC Bedrock exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.nusiq_bmodel, "path_animation", text="")
        col.prop(
            context.scene.nusiq_bmodel, "animation_name", text="Name"
        )
        col.prop(
            context.scene.nusiq_bmodel, "loop_animation", text="Loop"
        )
        col.prop(
            context.scene.nusiq_bmodel, "anim_time_update",
            text="anim_time_update"
        )
        self.layout.row().operator(
            "object.nusiq_bmodel_export_animation_operator", text="Export animation"
        )
