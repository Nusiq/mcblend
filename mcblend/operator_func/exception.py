'''
Custom mcblend exceptions.
'''
from __future__ import annotations

class NotEnoughTextureSpace(Exception):
    '''Raise when there is no enough UV space for uv-mapping.'''

class InvalidDictPathException(LookupError):
    '''
    Raise when using using function for quick access to dictionary path fails.
    '''

class ExporterException(Exception):
    '''
    Something went wrong during exporting. The exception is raised when Mcblend
    is unable to convert the Blender object into Minecraft format.

    Examples:
    - the UV-mapping of exported model is not valid (impossible to map with
        Minecraft UV-mapping system).
    - trying to export model part as a cube insteaad of polymesh, when the
        model is not a cube.
    '''

class ImporterException(Exception):
    '''
    Something went wrong while importing the model.
    '''
