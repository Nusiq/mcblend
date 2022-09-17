'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.
'''
from bpy.types import Context, Object

def get_context_object(context: Context) -> Object:
    '''Returns the object from the context.'''
    return context.object  # type: ignore[attr-defined]
