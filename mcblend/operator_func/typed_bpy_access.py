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

def get_mcblend_active_event(scene):
    '''
    Returns the active event id from scene

    >>> scene.mcblend_active_event
    '''
    return scene.mcblend_active_event

def get_mcblend_active_uv_group(scene):
    '''
    Returns the active uv group id from scene

    >>> scene.mcblend_active_uv_group
    '''
    return scene.mcblend_active_uv_group


def get_mcblend_active_uv_groups_side(scene):
    '''
    Returns the active uv group side from context

    >>> scene.mcblend_active_uv_groups_side
    '''
    return scene.mcblend_active_uv_groups_side

def get_mcblend_events(scene):
    '''
    Returns the events properties from context

    >>> scene.mcblend_events
    '''
    return scene.mcblend_events

def get_mcblend_project(scene):
    '''
    Returns the project properties from context

    >>> scene.mcblend_project
    '''
    return scene.mcblend_project

def get_mcblend_uv_groups(scene):
    '''
    >>> scene.mcblend_uv_groups
    '''
    return scene.mcblend_uv_groups

def set_mcblend_active_event(scene, value):
    '''
    Sets the active event id in scene

    >>> scene.mcblend_active_event = value
    '''
    scene.mcblend_active_event = value


def set_mcblend_active_uv_group(scene, value):
    '''
    Sets the active uv group id in scene

    >>> scene.mcblend_active_uv_group = value
    '''
    scene.mcblend_active_uv_group = value
