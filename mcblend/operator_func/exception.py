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

class NoCubePolygonsException(Exception):
    '''
    Raise when trying to get CubePolygons from McblendObject but some data is
    missing.
    '''

class InvalidUvShape(Exception):
    '''
    Raise when the UV-mapping of exported model is not valid.
    '''

class ImporterException(Exception):
    '''
    Something went wrong while importing the mode.
    '''
