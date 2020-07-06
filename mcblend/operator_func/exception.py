'''
Custom mcblend xceptions.
'''
from __future__ import annotations


class NameConflictException(Exception):
    '''Raise when two bones in Minecraft model have the same name.'''

class NotEnoughTextureSpace(Exception):
    '''Raise when there is no enough UV space for uv-mapping.'''

class InvalidDictPathException(LookupError):
    '''
    Raise when using using function for quick access to dictonary path fails.
    '''

class NoCubePolygonsException(Exception):
    '''
    Raise when trying to get CubePolygons from McblendObject but some data is
    missing.
    '''
