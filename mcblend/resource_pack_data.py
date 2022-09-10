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
def enum_materials(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the materials enum property of the
    MCBLEND_MaterialPattern.
    '''
    return get_db_handler().gui_enum_materials_from_db(
        self.active_rc_pk, self.active_entity_pk, self.pattern)

class MCBLEND_MaterialPattern(bpy.types.PropertyGroup):
    '''
    Used to store information about material field in a render controller of
    the selected entity in the GUI of the model importer.
    '''
    # Reused properties from parent objects for quick access
    active_rc_pk: IntProperty(  # type: ignore
        description=(
            "Primary key of the render controller that owns this material"
            " pattern")
    )
    active_entity_pk: IntProperty(  # type: ignore
        description="Primary key of the active entity")

    # Actual properties of the object
    pattern: StringProperty(  # type: ignore
        description="The pattern value of this material pattern")
    materials: EnumProperty(  # type: ignore
        items=enum_materials,
        description="The material value of this material pattern")

# RENDER CONTROLLER
def enum_geometries(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the geometries enum property of the
    MCBLEND_RenderController.
    '''
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    return get_db_handler().gui_enum_geometries_from_db(
        self.primary_key, entity_pk)

def enum_textures(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the textues enum property of the
    MCBLEND_RenderController.
    '''
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    return get_db_handler().gui_enum_textures_from_db(
            self.primary_key, entity_pk)

class MCBLEND_RenderController(bpy.types.PropertyGroup):
    '''
    Used to store infromation about one of the render controllers of the
    selected entity in the GUI of the model impoerter.
    '''
    # Reused properties from parent objects for quick access
    active_entity_pk: IntProperty(  # type: ignore
        description="Primary key of the selected entity")

    # Actual properties of the object
    primary_key: IntProperty(  # type: ignore
        description="Primary key of this render controller")
    identifier: StringProperty(   # type: ignore
        description="Identifier of this render controller")

    geometries: EnumProperty(  # type: ignore
        items=enum_geometries,
        description="List of geometries of this render controller")
        # update=update_geometries)
    textures: EnumProperty(  # type: ignore
        items=enum_textures,
        description="List of textures of this render controller")

    # Material pattern is a star pattern that matches the names of the bones
    # in the geometry to assign materials
    material_patterns: CollectionProperty(  # type: ignore
        type=MCBLEND_MaterialPattern,
        description="List of material patters used by this render controller")

# RESOURCE PACK (PROJECT)
def update_selected_entity(self, context) -> None:
    '''
    Called on update of selected_entity property of the
    MCBLEND_ProjectProperties. Loads the data related to the selected entity
    from the database and assigns it to self.entities and
    self.render_Controllers.
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
    Used to store information about the resource pack for the GUI of the model
    importer.
    '''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    selected_entity: StringProperty(   # type: ignore
        default="",
        description="Name that identifies one of the loaded entities",
        update=update_selected_entity)
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry,
        description="List of the loaded entities")
    render_controllers: CollectionProperty(
        type=MCBLEND_RenderController,
        description="List of loaded render controllers")
