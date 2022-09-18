'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.

The functions from this module are annotated in typed_bpy_access.pyi
'''
import bpy

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

def set_operator_property(operator, name, value):
    '''
    Sets the property of the operator

    >>> operator.name = value
    '''
    operator.__setattr__(name, value)

def new_colection(name):
    '''
    Creates new collection with given name

    >>> bpy.data.collections.new(name)
    '''
    return bpy.data.collections.new(name)


def get_collection_objects(collection):
    '''
    Returns the objects from collection

    >>> collection.objects
    '''
    return collection.objects

def get_collection_children(collection):
    '''
    Returns the children from collection

    >>> collection.children
    '''
    return collection.children

def get_view_layer_objects(view_layer):
    '''
    Returns the objects from view layer

    >>> view_layer.objects
    '''
    return view_layer.objects

def get_object_material_slots(object):
    '''
    Returns the material slots from object

    >>> object.material_slots
    '''
    return object.material_slots
