from bpy.types import Context, Object
from ..resource_pack_data import MCBLEND_ProjectProperties

def get_context_object(context) -> Object: ...

def get_context_scene_mcblend_project(
    context: Context) -> MCBLEND_ProjectProperties: ...
