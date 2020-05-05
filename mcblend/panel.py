'''
This module contains all of the panels for mcblend GUI.
'''
import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty
)


class OBJECT_NusiqMcblendExporterProperties(bpy.types.PropertyGroup):
    '''Global properties used by Mcblend for user settings configuration.'''
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="b_model",
        maxlen=1024
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

    texture_width: IntProperty(  # type: ignore
        name="",
        description="Minecraft UV parameter width.",
        default=512,
        min=1
    )
    texture_height: IntProperty(  # type: ignore
        name="",
        description=(
            "Minecraft UV parameter height. If you set it to 0 than the height"
            " of the texture will be picked automatically for you."
        ),
        default=0,
        min=0
    )
    move_blender_uvs: BoolProperty(  # type: ignore
        name="Move blender UVs",
        description=(
            "Decides if the UV mapping in blender should be moved to fit the"
            " minecraft UV mapping."
        ),
        default=True
    )
    move_existing_mappings: BoolProperty(  # type: ignore
        name="Move existing mappings",
        description=(
            "Decides if the minecraft UV mappings that already exist should be"
            " moved during planning the minecraft UV map."
        ),
        default=True
    )
    remove_old_mappings: BoolProperty(  # type: ignore
        name="Remove old UV-maps",
        description=(
            "Decides if current UV-mapping should be removed from selected "
            "objects."
        ),
        default=True
    )
    texture_template_resolution: IntProperty(  # type: ignore
        name="Template texture resolution",
        description=(
            'Sets the resolution of the template texture. Setting this to 0 '
            'prevents the creation of the template texture. This value '
            'describes how many pixels on the image is represented by one '
            'texture_widht or texture_height unit in model definition. '
            'The value of 1 gives the standard minecraft texture '
            'resolution.'
        ),
        default=0,
        min=0,
        soft_max=5,
    )


class OBJECT_PT_NusiqMcblendExportPanel(bpy.types.Panel):
    '''Panel used for configuration of exporting models'''
    # pylint: disable=C0116, W0613
    bl_label = "Export bedrock model"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.nusiq_mcblend, "path", text="")
        col.prop(
            context.scene.nusiq_mcblend, "model_name", text="Name"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_export_operator", text="Export model"
        )


class OBJECT_PT_NusiqMcblendImportPanel(bpy.types.Panel):
    '''Panel used for configuration of importing models.'''
    # pylint: disable=C0116, W0613
    bl_label = "Import bedrock model"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.nusiq_mcblend, "path", text="")
        self.layout.row().operator(
            "object.nusiq_mcblend_import_operator", text="Import model"
        )


class OBJECT_PT_NusiqMcblendExportAnimationPanel(bpy.types.Panel):
    '''Panel used for configuration of exporting animations.'''
    # pylint: disable=C0116, W0613
    bl_label = "Export bedrock animation"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.nusiq_mcblend, "path_animation", text="")
        col.prop(
            context.scene.nusiq_mcblend, "animation_name", text="Name"
        )
        col.prop(
            context.scene.nusiq_mcblend, "loop_animation", text="Loop"
        )
        col.prop(
            context.scene.nusiq_mcblend, "anim_time_update",
            text="anim_time_update"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_export_animation_operator", text="Export animation"
        )


class OBJECT_PT_NusiqMcblendSetUvsPanel(bpy.types.Panel):
    '''Panel  used for Minecraft UV maping and its configuration.'''
    # pylint: disable=C0116, W0613
    bl_label = "Set bedrock UVs"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(
            context.scene.nusiq_mcblend, "texture_width", text="Texture width"
        )
        col.prop(
            context.scene.nusiq_mcblend, "texture_height", text="Texture height"
        )
        col.prop(
            context.scene.nusiq_mcblend, "move_existing_mappings",
            text="Move existing mcUv mappings"
        )
        col.prop(
            context.scene.nusiq_mcblend, "move_blender_uvs",
            text="Move blender UV mappings"
        )
        col.prop(
            context.scene.nusiq_mcblend, "remove_old_mappings",
            text="Remove old UV maps"
        )
        col.prop(
            context.scene.nusiq_mcblend, "texture_template_resolution",
            text="Template resolution"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_map_uv_operator", text="Set minecraft UVs"
        )


class OBJECT_PT_NusiqMcblendOperatorsPanel(bpy.types.Panel):
    '''
    Panel that gives the user access to various operators used by Mcblend.
    '''
    # pylint: disable=C0116, W0613
    bl_label = "Operators"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        self.layout.row().operator(
            "object.nusiq_mcblend_toggle_mc_mirror_operator",
            text="Toggle mc_mirror"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_uv_group_operator",
            text="Set mc_uv_group"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_toggle_mc_is_bone_operator",
            text="Toggle mc_is_bone"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_set_inflate_operator",
            text="Set mc_inflate"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_round_dimensions_operator",
            text="Round dimensions"
        )
