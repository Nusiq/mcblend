# type: ignore
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

def get_mcblend(obj):
    '''
    >>> obj.mcblend
    '''
    return obj.mcblend

def get_scene_mcblend_active_event(context):
    '''
    Returns the active event id from context

    >>> context.scene.mcblend_active_event
    '''
    return context.scene.mcblend_active_event

def get_scene_mcblend_active_uv_group(context):
    '''
    Returns the active uv group id from context

    >>> context.scene.mcblend_active_uv_group
    '''
    return context.scene.mcblend_active_uv_group


def get_scene_mcblend_active_uv_groups_side(context):
    '''
    Returns the active uv group side from context

    >>> context.scene.mcblend_active_uv_groups_side
    '''
    return context.scene.mcblend_active_uv_groups_side

def get_scene_mcblend_events(context):
    '''
    Returns the events properties from context

    >>> context.scene.mcblend_events
    '''
    return context.scene.mcblend_events

def get_scene_mcblend_project(context):
    '''
    Returns the project properties from context

    >>> context.scene.mcblend_project
    '''
    return context.scene.mcblend_project

def get_scene_mcblend_uv_groups(context):
    '''
    >>> context.scene.mcblend_uv_groups
    '''
    return context.scene.mcblend_uv_groups

def set_operation(obj, operation):
    '''
    >>> obj.operation = operation
    '''
    obj.operation = operation

def set_operator_property(operator, name, value):
    '''
    Sets the property of the operator

    >>> operator.<name> = value
    '''
    setattr(operator, name, value)

def set_parent(obj, value):
    '''
    >>> obj.parent = value
    '''
    obj.parent = value

def set_pose_bone_constraint_property(constraint, name, value):
    '''
    Sets the property of the constraint

    >>> constraint.<name> = value
    '''
    setattr(constraint, name, value)

def set_scene_mcblend_active_event(context, value):
    '''
    Sets the active event id in context

    >>> context.scene.mcblend_active_event = value
    '''
    context.scene.mcblend_active_event = value


def set_scene_mcblend_active_uv_group(context, value):
    '''
    Sets the active uv group id in context

    >>> context.scene.mcblend_active_uv_group = value
    '''
    context.scene.mcblend_active_uv_group = value


def set_use_clamp(obj, use_clamp):
    '''
    >>> obj.use_clamp = use_clamp
    '''
    obj.use_clamp = use_clamp

def set_uv(obj, uv):
    '''
    >>> obj.uv = uv
    '''
    obj.uv = uv

def set_view_layer_objects_active(context, value):
    '''
    Sets the active object in context

    >>> context.view_layer.objects.active = value
    '''
    context.view_layer.objects.active = value

def to_euler(obj, order, euler_compact=None):
    '''
    >>> obj.to_euler(order, euler_compact)
    '''
    if euler_compact is None:
        return obj.to_euler(order)
    return obj.to_euler(order, euler_compact)
