'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.

The functions from this module are annotated in typed_bpy_access.pyi to avoid
errors from mypy.
'''
def get_context_object(context):
    '''Returns the object from the context'''
    return context.object

def get_context_scene_mcblend_project(context):
    '''Returns the project properties from context'''
    return context.scene.mcblend_project
