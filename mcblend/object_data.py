'''
Custom Blender objects with additional data for the objects and empties.
'''
import bpy
from bpy.props import (
    BoolProperty, EnumProperty, FloatProperty, IntVectorProperty,
    StringProperty, IntProperty, FloatVectorProperty, CollectionProperty)

from .operator_func.common import MeshType

# Blender object
def list_mesh_types_as_blender_enum(self, context):
    '''List mesh types for EnumProperty.'''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in MeshType]


class MCBLEND_FakeRcMaterialProperties(bpy.types.PropertyGroup):
    '''
    Pattern-material pair for MCBLEND_FakeRcProperties object.
    '''
    pattern: StringProperty(  # type: ignore
        name="", description="The bone name pattern for assigning material.",
        default="", maxlen=1024)
    material: StringProperty(  # type: ignore
        name="",
        description="Name of the material used by this render controller",
        default="",
        maxlen=1024
    )

class MCBLEND_FakeRcProperties(bpy.types.PropertyGroup):
    '''
    Armature property group similar to Minecraft render controller used for
    generating Minecraft materials.
    '''
    texture: StringProperty(  # type: ignore
        name="",
        description="Name of the texture used by this render controller",
        default="",
        maxlen=1024
    )
    materials: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcMaterialProperties, name='Materials')

class MCBLEND_ObjectProperties(bpy.types.PropertyGroup):
    '''Custom properties of an object.'''
    # ARMATURE PROPERTIES (equivalent of minecraft model)
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="model",
        maxlen=1024
    )
    texture_template_resolution: IntProperty(  # type: ignore
        name="Template texture resolution",
        description=(
            'Sets the resolution of the template texture.'
            'describes how many pixels on the image is represented by one '
            'texture_width or texture_height unit in model definition. '
            'The value of 1 gives the standard minecraft texture '
            'resolution.'
        ),
        default=1,
        min=1,
        soft_max=5,
    )
    allow_expanding: BoolProperty(  # type: ignore
        name="Allow Texture Expanding",
        description="Allows expanding texture during texture generation.",
        default=True,
    )
    generate_texture: BoolProperty(  # type: ignore
        name="Generate texture",
        description="Generates texture during UV mapping.",
        default=True,
    )
    visible_bounds_offset: FloatVectorProperty(  # type: ignore
        name="Visible bounds offset",
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
        default=64,
        min=1
    )
    texture_height: IntProperty(  # type: ignore
        name="",
        description=(
            "Minecraft UV parameter height. If you set it to 0 than the height"
            " of the texture will be picked automatically for you."
        ),
        default=64,
        min=1
    )
    # RENDER CONTROLLERS (armature properties used for generating materials)
    render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcProperties, name="Render Controllers"
    )

    # CUBE PROPERTIES
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
    mesh_type: EnumProperty(  # type: ignore
        items=list_mesh_types_as_blender_enum, # type: ignore
        name='Mesh type')
    min_uv_size: IntVectorProperty(  # type: ignore
        name="Min UV size", default=(0.0, 0.0, 0.0), min=0,
        description=(
            "The lower UV boundary of the length of X dimension of a cube. If "
            "it's greater than the actual X, then the UV-mapper will act as "
            "if the X were equal to this value.")
    )
