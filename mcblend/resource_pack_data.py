'''
Custom Blender objects with properties of the resource pack.
'''
from typing import Any

import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, PointerProperty, StringProperty)

from .operator_func import reload_rp_entities
from .common_data import (
    MCBLEND_EnumCache, MCBLEND_JustName,
    MCBLEND_NameValuePair)
from .operator_func.db_handler import get_db


def enum_project_entities(self, context):
    '''List project entities as blender enum list.'''
    # pylint: disable=unused-argument
    connection = get_db()
    return [
        (str(i),j,k)  # It must be tuple of strings
        for i,j,k in connection.execute(
            '''
            SELECT ClientEntity_pk, identifier, identifier
            FROM ClientEntity;'''
        )]

def update_entity_names(self, context):
    '''
    Called on update of project.entity_names. Resets the values of selected
    enum items in 'entities' and 'render_controllers'. If necessary updates
    the cached values of selected entity and its render controllers.
    '''
    # pylint: disable=unused-argument


class MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''
    The properties of the Resource Pack opened in this Blender project.
    '''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    entity_names: EnumProperty(  # type: ignore
        items=enum_project_entities,
        update=update_entity_names)


