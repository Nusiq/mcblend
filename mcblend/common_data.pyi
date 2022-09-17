'''
PropertyGroups commonly used across other PropertyGroups in collections and
as pointers.
'''
from bpy.types import PropertyGroup

class MCBLEND_JustName(PropertyGroup):
    name: str

class MCBLEND_DbEntry(PropertyGroup):
    primary_key: int
    name: str
