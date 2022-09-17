'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.

'''
from typing import TYPE_CHECKING
from bpy.types import Context, Object

if TYPE_CHECKING:
    from ..object_data import MCBLEND_EventProperties
    from ..resource_pack_data import MCBLEND_ProjectProperties
    from .pyi_types import CollectionProperty
else:
    MCBLEND_EventProperties = None
    MCBLEND_ProjectProperties = None
    CollectionProperty = None

def get_context_object(context: Context) -> Object:
    '''Returns the object from the context'''
    return context.object  # type: ignore[attr-defined]

def get_context_scene_mcblend_project(
        context: Context) -> MCBLEND_ProjectProperties:
    '''Returns the project properties from context'''
    return context.scene.mcblend_project  # type: ignore[attr-defined]

def get_context_scene_mcblend_events(
        context: Context) -> CollectionProperty[MCBLEND_EventProperties]:
    '''Returns the events properties from context'''
    return context.scene.mcblend_events  # type: ignore[attr-defined]

def get_context_scene_mcblend_active_event(context: Context) -> int:
    '''Returns the active event id from context'''
    return context.scene.mcblend_active_event  # type: ignore[attr-defined]

def set_context_scene_mcblend_active_event(
        context: Context, value: int) -> None:
    '''Sets the active event id in context'''
    context.scene.mcblend_active_event = value  # type: ignore[attr-defined]