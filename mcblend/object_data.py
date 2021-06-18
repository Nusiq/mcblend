'''
Custom Blender objects with additional data for the objects and empties.
'''
import bpy
from bpy.props import (
    BoolProperty, EnumProperty, FloatProperty, IntVectorProperty, StringProperty, IntProperty)

from .operator_func.common import MeshType

# Blender object
def list_mesh_types_as_blender_enum(self, context):
    '''List mesh types for EnumProperty.'''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in MeshType]

class NUSIQ_MCBLEND_ObjectProperties(bpy.types.PropertyGroup):
    '''Custom properties of an object.'''
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
        items=list_mesh_types_as_blender_enum, name='Mesh type')
    min_uv_size: IntVectorProperty(
        name="Min UV size", default=(0.0, 0.0, 0.0), min=0,
        description=(
            "The lower UV boundary of the length of X dimension of a cube. If "
            "it's greater than the actual X, then the UV-mapper will act as "
            "if the X were equal to this value.")
    )
