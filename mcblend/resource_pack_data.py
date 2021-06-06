'''
Custom Blender objects with properties of the resource pack.
'''
from typing import List, Tuple

import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, StringProperty)

from .operator_func import reload_rp_entities

# Resource pack (importer)
class NUSIQ_MCBLEND_JustName(bpy.types.PropertyGroup):
    '''Custom property group which has only the "name" property'''
    name: StringProperty(  # type: ignore
        name="",
        description="The identifier of the object",
        default="", maxlen=1024)

class NUSIQ_MCBLEND_NameValuePair(bpy.types.PropertyGroup):
    '''
    Custom property group which has only the "name" and "value" string
    properties.
    '''
    name: StringProperty(  # type: ignore
        name="",
        description="The identifier of the object",
        default="", maxlen=1024)
    value: StringProperty(  # type: ignore
        name="", description="The value of the object",
        default="", maxlen=1024
    )

class NUSIQ_MCBLEND_ProjectEntitiesProperties(bpy.types.PropertyGroup):
    '''
    Cached properties of an entity from resource pack.
    '''
    name: StringProperty(  # type: ignore
        name="", description="Name of the entity from the project",
        default="", maxlen=1024)

    render_controllers: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_JustName, name='Textures')
    textures: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_NameValuePair, name='Textures')
    geometries: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_NameValuePair, name='Geometries')
    materials: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_NameValuePair, name='Materials')

def enum_project_entities(self, context):
    '''List project entities as blender enum list.'''
    # pylint: disable=unused-argument
    return [
        (i, i, i)for i in
        sorted(j.name for j in context.scene.nusiq_mcblend_project.entities)
    ]

def enum_project_entity_rc(self, context):
    '''List entity render controllers as blender enum list.'''
    # pylint: disable=unused-argument
    # entity_names is an enum property (returns string)
    entity_name = self.entity_names
    result: List[Tuple[str, str, str]] = []
    if entity_name == "":
        return result
    for i in sorted(self.entities[entity_name].render_controllers.keys()):
        result.append((i, i, i))
    return result

def enum_project_entity_geo(self, context):
    '''List geometries as blender enum lists.'''
    # pylint: disable=unused-argument
    # entity_names is an enum property (returns string)
    entity_name = self.entity_names
    result: List[Tuple[str, str, str]] = []
    if entity_name == "":
        return result
    for i in sorted(self.entities[entity_name].geometries.keys()):
        result.append((i, i, i))
    return result

def enum_project_entity_texture(self, context):
    '''List textures of an entity as blender enum list.'''
    # pylint: disable=unused-argument
    # entity_names is an enum property (returns string)
    entity_name = self.entity_names
    result: List[Tuple[str, str, str]] = []
    if entity_name == "":
        return result
    for i in sorted(self.entities[entity_name].textures.keys()):
        result.append((i, i, i))
    return result

def _update_entity_names(self, context):
    '''
    Called on update of project.entity_names. Resets the values of the entity
    properties like geometries, textures and render controllers.
    '''
    # pylint: disable=unused-argument
    entity_name = self.entity_names
    rcs = self.entities[entity_name].render_controllers
    if len(rcs) > 0:
        self.render_controller_names = rcs[0].name
    geo = self.entities[entity_name].geometries
    if len(geo) > 0:
        self.geometry_names = geo[0].name
    textures = self.entities[entity_name].textures
    if len(textures) > 0:
        self.texture_names = textures[0].name

class NUSIQ_MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''The properties of the Resource Pack opened in this Blender project.'''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    entities: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_ProjectEntitiesProperties,
        name='Project entities')
    entity_names: EnumProperty(  # type: ignore
        items=enum_project_entities,
        name='Project entities', update=_update_entity_names)
    render_controller_names: EnumProperty(  # type: ignore
        items=enum_project_entity_rc,
        name='Project entities')
    geometry_names: EnumProperty(  # type: ignore
        items=enum_project_entity_geo,
        name='Project entities')
    texture_names: EnumProperty(  # type: ignore
        items=enum_project_entity_texture,
        name='Project entities')
