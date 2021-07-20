'''
Custom mcblend exceptions.
'''
from __future__ import annotations
from typing import List

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

class FileIsNotAModelException(Exception):
    '''
    Raised in importer when the loaded file is not a model.
    '''

class ImportingNotImplementedError(NotImplementedError):
    '''
    Raised by imported when given property is valid but there is no
    implementation for loading it into blender.
    '''
    def __init__(self, what: str, path: List):
        super().__init__(
            f'{path}:: importing {what} is not implemented in this version of'
            ' mcblend.')
