'''
This module contains all of the panels for mcblend GUI.
'''
# don't import future annotations Blender needs that
import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty, FloatProperty,
    FloatVectorProperty
)

class OBJECT_NusiqMcblendObjectProperties(bpy.types.PropertyGroup):
    mirror: BoolProperty(  # type: ignore
        name="Mirror",
        description="Defines how to layout the UV during UV generation.",
        default=False,
    )
    uv_group: StringProperty(  # type: ignore
        name="UV group",
        description=(
            "Objects with the same UV group can be mapped to the same spot on "
            "the texture if they have the same dimensions. Empty string means "
            "that the object doesn't belong to any UV group."),
        default="",
        maxlen=1024
    )
    is_bone: BoolProperty(  # type: ignore
        name="Export as bone",
        description=(
            "If true than this object will be exported as minecraft bone."),
        default=False,
    )
    inflate: FloatProperty(  # type: ignore
        name="Inflate",
        description="The inflate value of this object.",
        default=0.0
    )


class OBJECT_NusiqMcblendAnimationProperties(bpy.types.PropertyGroup):
    name: StringProperty(  # type: ignore
        name="Name",
        description="Name of the animation.", default="animation",
        maxlen=1024
    )
    single_frame: BoolProperty(  # type: ignore
        name="Single frame",
        description="Exports current pose as single frame animation",
        default=False,
    )
    anim_time_update: StringProperty(  # type: ignore
        name="anim_time_update",
        description="Adds anim_time_update value unless is left empty",
        default="",
        maxlen=1024
    )
    loop: BoolProperty(  # type: ignore
        name="Loop",
        description="Decides if animation should be looped",
        default=True,
    )
    frame_start: IntProperty(  # type: ignore
        name="Frame start",
        description="The first frame of the animation.",
        default=0,
        min=0
    )
    frame_current: IntProperty(  # type: ignore
        name="Frame current",
        description="The current frame of the animation.",
        default=100,
        min=0
    )
    frame_end: IntProperty(  # type: ignore
        name="Frame end",
        description="The last frame of the animation.",
        default=100,
        min=0
    )

class OBJECT_NusiqMcblendExporterProperties(bpy.types.PropertyGroup):
    '''Global properties used by Mcblend for user settings configuration.'''
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="model",
        maxlen=1024
    )
    visible_bounds_offset: FloatVectorProperty(  # type: ignore
        name="Visible bounts offset",
        description="visible_bounds_offset of the model",
        default=(0.0, 0.0, 0.0)
    )
    visible_bounds_width: FloatProperty(  # type: ignore
        name="Visible bounds width",
        description="visible_bounds_width of the model",
        default=1.0
    )
    visible_bounds_height: FloatProperty(  # type: ignore
        name="Visible bounds height",
        description="visible_bounds_height of the model",
        default=1.0
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

class OBJECT_PT_NusiqMcblendObjectPropertiesPanel(bpy.types.Panel):
    '''Panel with custom object properties (for meshes and empties)'''
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "Mcblend object properties"

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return (
                context.active_object.type == "MESH" or
                context.active_object.type == "EMPTY")

    def draw(self, context):
        col = self.layout.column(align=True)

        if context.mode == "OBJECT" and context.object != None:
            col.prop(
                context.object.nusiq_mcblend_object_properties, "is_bone",
                text="Export as bone")
            if context.object.type == 'MESH':
                col.prop(
                    context.object.nusiq_mcblend_object_properties, "mirror",
                    text="Mirror")
                col.prop(
                    context.object.nusiq_mcblend_object_properties, "uv_group",
                    text="UV group")
                col.prop(
                    context.object.nusiq_mcblend_object_properties, "inflate",
                    text="Inflate")


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
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_width", text="Visible bounds width"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_height", text="Visible bounds height"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_offset", text="Visible bounds offset"
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

        row = col.row()
        row.operator(
            "object.nusiq_mcblend_add_animation", text="New animation"
        )

        active_anim_id = bpy.context.scene.nusiq_mcblend_active_animation
        anims = bpy.context.scene.nusiq_mcblend_animations
        if active_anim_id < len(anims):
            row.operator(
                "object.nusiq_mcblend_remove_animation", text="Remove this animation"
            )
            col.operator_menu_enum(
                "object.nusiq_mcblend_list_animations", "animations_enum",
                text="Select animation"
            )

            active_anim = anims[active_anim_id]
            col.prop(active_anim, "name", text="Name")
            col.prop(active_anim, "single_frame", text="Export as pose")
            if active_anim.single_frame:
                col.prop(bpy.context.scene, "frame_current", text="Frame")
            else:
                col.prop(active_anim, "loop", text="Loop")
                col.prop(active_anim, "anim_time_update", text="anim_time_update")
                col.prop(bpy.context.scene, "frame_start", text="Frame start")
                col.prop(bpy.context.scene, "frame_end", text="Frame end")
                
            col.operator(
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
            "object.nusiq_mcblend_toggle_mirror_operator",
            text="Toggle mirror for UV mapping"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_uv_group_operator",
            text="Set the UV group"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_toggle_is_bone_operator",
            text="Toggle export as bones"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_set_inflate_operator",
            text="Inflate"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_round_dimensions_operator",
            text="Round dimensions"
        )
