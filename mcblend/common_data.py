'''
PropertyGroups commonly used across other PropertyGroups in collections and
as pointers.
'''
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty


class MCBLEND_JustName(PropertyGroup):
    '''Custom property group which has only the "name" property'''
    name: StringProperty(  # type: ignore
        name="",
        default="", maxlen=1024)

class MCBLEND_DbEntry(PropertyGroup):
    '''
    Used for creating CollectionProperties that store primary keys from some
    query in the database and a name for displaying in the GUI.
    '''
    primary_key: IntProperty()  # type: ignore
    name: StringProperty(default="")  # type: ignore
