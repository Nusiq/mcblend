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
    # TODO - remove this class
