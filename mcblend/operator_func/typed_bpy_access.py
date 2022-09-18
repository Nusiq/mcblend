'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.

The functions from this module are annotated in typed_bpy_access.pyi
'''
def get_context_object(context):
    '''
    Returns the object from the context
    
    >>> context.object
    '''
    return context.object

def get_context_scene_mcblend_project(context):
    '''
    Returns the project properties from context
    
    >>> context.scene.mcblend_project
    '''
    return context.scene.mcblend_project

def get_context_scene_mcblend_events(context):
    '''
    Returns the events properties from context
    
    >>> context.scene.mcblend_events
    '''
    return context.scene.mcblend_events

def get_context_scene_mcblend_active_event(context):
    '''
    Returns the active event id from context
    
    >>> context.scene.mcblend_active_event
    '''
    return context.scene.mcblend_active_event

def set_context_scene_mcblend_active_event(context, value):
    '''
    Sets the active event id in context

    >>> context.scene.mcblend_active_event = value
    '''
    context.scene.mcblend_active_event = value

def get_context_scene_mcblend_uv_groups(context):
    '''
    Returns the uv groups from context
    
    >>> context.scene.mcblend_uv_groups
    '''
    return context.scene.mcblend_uv_groups

def get_context_selected_objects(context):
    '''
    Returns selected objects list from context

    >>> context.selected_objects
    '''
    return context.selected_objects

def get_object_mcblend(object):
    '''
    Returns the mcblend property from object

    >>> object.mcblend
    '''
    return object.mcblend
