'''
PropertyGroups commonly used across other PropertyGroups in collections and
as pointers.
'''
from typing import TYPE_CHECKING
import bpy
from bpy.props import (
    CollectionProperty, StringProperty, BoolProperty, IntProperty)

class MCBLEND_JustName(bpy.types.PropertyGroup):
    '''Custom property group which has only the "name" property'''
    name: StringProperty(  # type: ignore
        name="",
        description="The identifier of the object",
        default="", maxlen=1024)

if TYPE_CHECKING:
    class MCBLEND_JustName:
        name: str

class MCBLEND_DbEntry(bpy.types.PropertyGroup):
    '''
    Used for creating CollectionProperties that store primary keys from some
    query in the database and a name for displaying in the GUI.
    '''
    primary_key: IntProperty()
    name: StringProperty(default="")

if TYPE_CHECKING:
    class MCBLEND_DbEntry:
        primary_key: int
        name: str