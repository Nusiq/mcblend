'''
Custom Blender objects with exporter data.
'''
import bpy
from bpy.props import (
    BoolProperty, FloatProperty,
    FloatVectorProperty, IntProperty,
    StringProperty)

# Main Mcblend properties
class NUSIQ_MCBLEND_ExporterProperties(bpy.types.PropertyGroup):
    '''Global properties of Mcblend.'''
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
