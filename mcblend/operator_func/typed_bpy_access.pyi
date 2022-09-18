from bpy.types import Context, Object
from .extra_types import CollectionProperty

from ..object_data import MCBLEND_EventProperties
from ..resource_pack_data import MCBLEND_ProjectProperties

def get_context_object(context: Context) -> Object: ...

def get_context_scene_mcblend_project(context: Context) ->\
    MCBLEND_ProjectProperties: ...

def get_context_scene_mcblend_events(context: Context) ->\
    CollectionProperty[MCBLEND_EventProperties]: ...

def get_context_scene_mcblend_active_event(context: Context) -> int: ...

def set_context_scene_mcblend_active_event(context: Context, value: int) ->\
    None: ...