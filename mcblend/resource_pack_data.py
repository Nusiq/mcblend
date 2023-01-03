'''
Custom Blender objects with properties of the resource pack.
'''
from typing import cast

from bpy.types import PropertyGroup
from bpy.props import (
    CollectionProperty, EnumProperty, IntProperty, StringProperty)

from .common_data import MCBLEND_DbEntry
from .operator_func.db_handler import get_db_handler

# RENDER CONTROLLER'S MATERIAL FIELD FOR ENTITY SELECTION
def enum_entity_materials(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the materials enum property of the
    MCBLEND_EntityMaterialPattern.
    '''
    return get_db_handler().gui_enum_entity_materials(
        self.active_rc_pk, self.active_entity_pk, self.pattern)


class MCBLEND_EntityMaterialPattern(PropertyGroup):
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


class MCBLEND_EntityRenderController(PropertyGroup):
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

# RENDER CONTROLLER'S MATERIAL FIELD FOR ATTACHABLE SELECTION
def enum_attachable_materials(self, context) -> list[tuple[str, str, str]]:
    '''
    Generates list for the materials enum property of the
    MCBLEND_AttachableMaterialPattern.
    '''
    return get_db_handler().gui_enum_attachable_materials(
        self.active_rc_pk, self.active_attachable_pk, self.pattern)


class MCBLEND_AttachableMaterialPattern(PropertyGroup):
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


class MCBLEND_AttachableRenderController(PropertyGroup):
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


class MCBLEND_ProjectProperties(PropertyGroup):
    '''
    Used to store information about the resource pack for the GUI of the model
    importer.
    '''
    importer_type: EnumProperty(  # type: ignore
        items=[
            (
                "ENTITY",
                "Import from entity",
                "Import models of an entity selected from resource pack"
            ),
            (
                "ATTACHABLE",
                "Import from attachable",
                "Import models of an attachable selected from resource pack"
            )
        ],
        name="Importer type",
        description="The type of the model importer"
    )
    selected_entity: StringProperty(   # type: ignore
        default="",
        description="Name that identifies the entity to be loaded",
        update=update_selected_entity)
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry,
        description="List of the loaded entities")
    entity_render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_EntityRenderController,
        description="List of render controllers of the entity")

    selected_attachable: StringProperty(   # type: ignore
        default="",
        description="Name that identifies the attachable to be loaded",
        update=update_selected_attachable)
    attachables: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry,
        description="List of the loaded attachables")
    attachable_render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_AttachableRenderController,
        description="List of render controllers of the attachable")
