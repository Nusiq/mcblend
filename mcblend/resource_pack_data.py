'''
Custom Blender objects with properties of the resource pack.
'''
import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, IntProperty, StringProperty)

from .common_data import MCBLEND_DbEntry
from .operator_func import reload_rp_entities
from .operator_func.db_handler import get_db_handler


# RENDER CONTROLLER'S MATERIAL FIELD
def enum_materials(self, context):
    return get_db_handler().gui_enum_materials_from_db(
        self.active_rc_pk, self.active_entity_pk, self.pattern)

class MCBLEND_RcMaterialPattern(bpy.types.PropertyGroup):
    '''
    Represents a material field in the render controller.
    '''
    # Reused properties from parent objects for quick access
    active_rc_pk: IntProperty()
    active_entity_pk: IntProperty()

    # Actual properties of the object
    pattern: StringProperty()
    materials: EnumProperty(
        items=enum_materials)

# RENDER CONTROLLER
def enum_geometries(self, context):
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    return get_db_handler().gui_enum_geometries_from_db(
        self.primary_key, entity_pk)

def enum_textures(self, context):
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    return get_db_handler().gui_enum_textures_from_db(
            self.primary_key, entity_pk)

class MCBLEND_RenderController(bpy.types.PropertyGroup):
    '''
    Represents the properties to be selected in the render controller menu:
    geometry, texture, material
    '''
    # Reused properties from parent objects for quick access
    active_entity_pk: IntProperty()

    # Actual properties of the object
    primary_key: IntProperty()
    identifier: StringProperty()

    geometries: EnumProperty(  # type: ignore
        items=enum_geometries)
        # update=update_geometries)
    textures: EnumProperty(  # type: ignore
        items=enum_textures)
    material_patterns: CollectionProperty(
        type=MCBLEND_RcMaterialPattern)

# RESOURCE PACK (PROJECT)
def update_selected_entity(self, context):
    '''
    Called on update of project.selected_entity.
    '''
    # pylint: disable=unused-argument
    pk = self.entities[self.selected_entity].primary_key
    self.render_controllers.clear()
    db_handler = get_db_handler()
    for rc_pk, rc_identifier in db_handler.list_render_controllers_from_db(pk):
        rc = self.render_controllers.add()
        rc.primary_key = rc_pk
        rc.identifier = rc_identifier
        rc.active_entity_pk = pk
        for pattern in db_handler.list_bone_name_patterns_from_rc(rc_pk):
            pattern_field = rc.material_patterns.add()
            pattern_field.pattern = pattern
            # Reused properties
            pattern_field.active_entity_pk = pk
            pattern_field.active_rc_pk = rc_pk


class MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''
    Represents top level selction in ResourcePack menu (the entity selection
    for importing).
    '''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    selected_entity: StringProperty(   # type: ignore
        default="", update=update_selected_entity)
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry)
    render_controllers: CollectionProperty(
        type=MCBLEND_RenderController)
