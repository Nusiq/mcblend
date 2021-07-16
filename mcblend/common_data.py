'''
PropertyGroups commonly used across other PropertyGroups in collections and
as pointers.
'''
import bpy
from bpy.props import (
    CollectionProperty, StringProperty, BoolProperty)

class MCBLEND_JustName(bpy.types.PropertyGroup):
    '''Custom property group which has only the "name" property'''
    name: StringProperty(  # type: ignore
        name="",
        description="The identifier of the object",
        default="", maxlen=1024)

class MCBLEND_NameValuePair(bpy.types.PropertyGroup):
    '''
    Custom property group which has only the "name" and "value" string
    properties.
    '''
    name: StringProperty(  # type: ignore
        name="",
        description="The identifier of the object",
        default="", maxlen=1024)
    value: StringProperty(  # type: ignore
        name="", description="The value of the object",
        default="", maxlen=1024
    )

class MCBLEND_EnumCache(bpy.types.PropertyGroup):
    '''Used from caching values enums in GUI which take a long time to load.'''
    is_cached: BoolProperty(  # type: ignore
        name="Single frame",
        description="Whether this object already stores cached values or not",
        default=False)
    values: CollectionProperty(  # type: ignore
        type=MCBLEND_JustName)
