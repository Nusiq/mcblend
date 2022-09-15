'''
Custom Blender objects with properties of the resource pack.
'''
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, IntProperty, StringProperty)

from .common_data import MCBLEND_DbEntry
from .operator_func import load_rp_entities
from .operator_func.db_handler import get_db_handler
from .extra_types import CollectionPropertyAnnotation

# RENDER CONTROLLER'S MATERIAL FIELD FOR ENTITY SELECTION
def enum_entity_materials(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the materials enum property of the
    MCBLEND_EntityMaterialPattern.
    '''
    return get_db_handler().gui_enum_entity_materials(
        self.active_rc_pk, self.active_entity_pk, self.pattern)

class MCBLEND_EntityMaterialPattern(bpy.types.PropertyGroup):
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
        items=enum_entity_materials,
        description="The material value of this material pattern")

if TYPE_CHECKING:
    class MCBLEND_EntityMaterialPattern:
        active_rc_pk: int
        active_entity_pk: int
        pattern: str
        materials: str

# RENDER CONTROLLER FOR ENTITY SELECTION
def enum_entity_geometries(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the geometries enum property of the
    MCBLEND_EntityRenderController.
    '''
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    if self.primary_key != -1:
        return get_db_handler().gui_enum_entity_geometries(
            self.primary_key, entity_pk)
    else:
        return get_db_handler().gui_enum_entity_geometries_for_fake_rc(
            entity_pk)

def enum_entity_textures(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the textues enum property of the
    MCBLEND_EntityRenderController.
    '''
    # pylint: disable=unused-argument
    entity_pk = self.active_entity_pk
    if self.primary_key != -1:
        return get_db_handler().gui_enum_entity_textures(
                self.primary_key, entity_pk)
    else:
        return get_db_handler().gui_enum_entity_textures_for_fake_rc(
            entity_pk)

def enum_fake_entity_material_patterns(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the fake_material_patterns enum property of the
    MCBLEND_EntityRenderController.

    Fake marerial patterns are used only when the render controller is not
    found. It lists all of the materials defined in the entity.
    '''
    # pylint: disable=unused-argument
    return get_db_handler().gui_enum_entity_fake_material_patterns(
        self.active_entity_pk)

class MCBLEND_EntityRenderController(bpy.types.PropertyGroup):
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
        items=enum_entity_geometries,
        description="List of geometries of this render controller")
        # update=update_geometries)
    textures: EnumProperty(  # type: ignore
        items=enum_entity_textures,
        description="List of textures of this render controller")

    # Material pattern is a star pattern that matches the names of the bones
    # in the geometry to assign materials
    material_patterns: CollectionProperty(  # type: ignore
        type=MCBLEND_EntityMaterialPattern,
        description="List of material patters used by this render controller")
    fake_material_patterns: EnumProperty(  # type: ignore
        description=(
            "List of materials that can be used by this render controller "
            "when it is a fake render controller (i.e. it is not in the "
            "database). It's applied to '*' pattern."),
        items=enum_fake_entity_material_patterns)

if TYPE_CHECKING:
    class MCBLEND_EntityRenderController:
        active_entity_pk: int
        primary_key: int
        identifier: str
        geometries: str
        textures: str
        material_patterns: CollectionPropertyAnnotation[MCBLEND_EntityMaterialPattern]
        fake_material_patterns: str

# RENDER CONTROLLER'S MATERIAL FIELD FOR ATTACHABLE SELECTION
def enum_attachable_materials(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the materials enum property of the
    MCBLEND_AttachableMaterialPattern.
    '''
    return get_db_handler().gui_enum_attachable_materials(
        self.active_rc_pk, self.active_attachable_pk, self.pattern)

class MCBLEND_AttachableMaterialPattern(bpy.types.PropertyGroup):
    '''
    Used to store information about material field in a render controller of
    the selected attachable in the GUI of the model importer.
    '''
    # Reused properties from parent objects for quick access
    active_rc_pk: IntProperty(  # type: ignore
        description=(
            "Primary key of the render controller that owns this material"
            " pattern")
    )
    active_attachable_pk: IntProperty(  # type: ignore
        description="Primary key of the active attachable")

    # Actual properties of the object
    pattern: StringProperty(  # type: ignore
        description="The pattern value of this material pattern")
    materials: EnumProperty(  # type: ignore
        items=enum_attachable_materials,
        description="The material value of this material pattern")

if TYPE_CHECKING:
    class MCBLEND_AttachableMaterialPattern:
        active_rc_pk: int
        active_attachable_pk: int
        pattern: str
        materials: str

# RENDER CONTROLLER FOR ATTACHABLE SELECTION
def enum_attachable_geometries(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the geometries enum property of the
    MCBLEND_AttachableRenderController.
    '''
    # pylint: disable=unused-argument
    attachable_pk = self.active_attachable_pk
    if self.primary_key != -1:
        return get_db_handler().gui_enum_attachable_geometries(
            self.primary_key, attachable_pk)
    else:
        return get_db_handler().gui_enum_attachable_geometries_for_fake_rc(
            attachable_pk)

def enum_attachable_textures(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the textues enum property of the
    MCBLEND_AttachableRenderController.
    '''
    # pylint: disable=unused-argument
    attachable_pk = self.active_attachable_pk
    if self.primary_key != -1:
        return get_db_handler().gui_enum_attachable_textures(
                self.primary_key, attachable_pk)
    else:
        return get_db_handler().gui_enum_attachable_textures_for_fake_rc(
            attachable_pk)

def enum_fake_attachable_material_patterns(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the fake_material_patterns enum property of the
    MCBLEND_AttachableRenderController.

    Fake marerial patterns are used only when the render controller is not
    found. It lists all of the materials defined in the attachable.
    '''
    # pylint: disable=unused-argument
    return get_db_handler().gui_enum_attachable_fake_material_patterns(
        self.active_attachable_pk)

class MCBLEND_AttachableRenderController(bpy.types.PropertyGroup):
    '''
    Used to store infromation about one of the render controllers of the
    selected attachable in the GUI of the model impoerter.
    '''
    # Reused properties from parent objects for quick access
    active_attachable_pk: IntProperty(  # type: ignore
        description="Primary key of the selected attachable")

    # Actual properties of the object
    primary_key: IntProperty(  # type: ignore
        description="Primary key of this render controller")
    identifier: StringProperty(   # type: ignore
        description="Identifier of this render controller")

    geometries: EnumProperty(  # type: ignore
        items=enum_attachable_geometries,
        description="List of geometries of this render controller")
        # update=update_geometries)
    textures: EnumProperty(  # type: ignore
        items=enum_attachable_textures,
        description="List of textures of this render controller")

    # Material pattern is a star pattern that matches the names of the bones
    # in the geometry to assign materials
    material_patterns: CollectionProperty(  # type: ignore
        type=MCBLEND_AttachableMaterialPattern,
        description="List of material patters used by this render controller")
    fake_material_patterns: EnumProperty(  # type: ignore
        description=(
            "List of materials that can be used by this render controller "
            "when it is a fake render controller (i.e. it is not in the "
            "database). It's applied to '*' pattern."),
        items=enum_fake_attachable_material_patterns)

if TYPE_CHECKING:
    class MCBLEND_AttachableRenderController:
        active_attachable_pk: int
        primary_key: int
        identifier: str
        geometries: str
        textures: str
        material_patterns: CollectionPropertyAnnotation[MCBLEND_AttachableMaterialPattern]
        fake_material_patterns: str

# RESOURCE PACK (PROJECT)
def update_selected_entity(self, context) -> None:
    '''
    Called on update of selected_entity property of the
    MCBLEND_ProjectProperties. Loads the data related to the selected entity
    from the database and assigns it to self.entities and
    self.render_Controllers.
    '''
    # pylint: disable=unused-argument
    self = cast(MCBLEND_ProjectProperties, self)
    pk = self.entities[self.selected_entity].primary_key
    self.entity_render_controllers.clear()
    db_handler = get_db_handler()
    for rc_pk, rc_identifier in db_handler.list_entity_render_controllers(pk):
        rc = self.entity_render_controllers.add()
        rc.primary_key = -1 if rc_pk is None else rc_pk 
        rc.identifier = rc_identifier
        rc.active_entity_pk = pk
        for pattern in db_handler.list_bone_name_patterns(rc_pk):
            pattern_field = rc.material_patterns.add()
            pattern_field.pattern = pattern
            # Reused properties
            pattern_field.active_entity_pk = pk
            pattern_field.active_rc_pk = rc_pk

def update_selected_attachable(self, context) -> None:
    '''
    Called on update of selected_attachable property of the
    MCBLEND_ProjectProperties. Loads the data related to the selected
    attachable from the database and assigns it to self.attachables and
    self.render_Controllers.
    '''
    # pylint: disable=unused-argument
    self = cast(MCBLEND_ProjectProperties, self)
    pk = self.attachables[self.selected_attachable].primary_key
    self.attachable_render_controllers.clear()
    db_handler = get_db_handler()
    for rc_pk, rc_identifier in db_handler.list_attachable_render_controllers(pk):
        rc = self.attachable_render_controllers.add()
        rc.primary_key = -1 if rc_pk is None else rc_pk 
        rc.identifier = rc_identifier
        rc.active_attachable_pk = pk
        for pattern in db_handler.list_bone_name_patterns(rc_pk):
            pattern_field = rc.material_patterns.add()
            pattern_field.pattern = pattern
            # Reused properties
            pattern_field.active_attachable_pk = pk
            pattern_field.active_rc_pk = rc_pk

class MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''
    Used to store information about the resource pack for the GUI of the model
    importer.
    '''
    importer_type: EnumProperty(  # type: ignore
        items=[
            (
                "ENTITY",
                "Import from entity",
                "Imports models for entity selected from resource pack"
            ),
            (
                "ATTACHABLE",
                "Import from attachable",
                "Imports models for attachable selected from resource pack"
            )
        ],
        name="Importer type",
        description=(
            "Selects the type of the importer to use for importing models"
            "from the resource pack")
    )
    selected_entity: StringProperty(   # type: ignore
        default="",
        description="Name that identifies one of the loaded entities",
        update=update_selected_entity)
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry,
        description="List of the loaded entities")
    entity_render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_EntityRenderController,
        description="List of render controllers of the entity")

    selected_attachable: StringProperty(   # type: ignore
        default="",
        description="Name that identifies one of the loaded attachables",
        update=update_selected_attachable)
    attachables: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry,
        description="List of the loaded attachables")
    attachable_render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_AttachableRenderController,
        description="List of render controllers of the attachable")

if TYPE_CHECKING:
    class MCBLEND_ProjectProperties:
        importer_type: Literal["ENTITY", "ATTACHABLE"]
        rp_path: str
        selected_entity: str
        entities: CollectionPropertyAnnotation[MCBLEND_DbEntry]
        entity_render_controllers: CollectionPropertyAnnotation[
            MCBLEND_EntityRenderController]

        selected_attachable: str
        attachables: CollectionPropertyAnnotation[MCBLEND_DbEntry]
        attachable_render_controllers: CollectionPropertyAnnotation[
            MCBLEND_AttachableRenderController]
