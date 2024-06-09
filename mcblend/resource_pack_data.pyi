'''
Custom Blender objects with properties of the resource pack.
'''
from typing import Literal, Any
from bpy.types import Context
from .common_data import MCBLEND_DbEntry
from .operator_func.pyi_types import CollectionProperty

# RENDER CONTROLLER'S MATERIAL FIELD FOR ENTITY SELECTION
def enum_entity_materials(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

class MCBLEND_EntityMaterialPattern:
    active_rc_pk: int
    active_entity_pk: int
    pattern: str
    materials: str


# RENDER CONTROLLER FOR ENTITY SELECTION
def enum_entity_geometries(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

def enum_entity_textures(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

def enum_fake_entity_material_patterns(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

class MCBLEND_EntityRenderController:
    active_entity_pk: int
    primary_key: int
    identifier: str
    geometries: str
    textures: str
    material_patterns: CollectionProperty[MCBLEND_EntityMaterialPattern]
    fake_material_patterns: str

# RENDER CONTROLLER'S MATERIAL FIELD FOR ATTACHABLE SELECTION
def enum_attachable_materials(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

class MCBLEND_AttachableMaterialPattern:
    active_rc_pk: int
    active_attachable_pk: int
    pattern: str
    materials: str


# RENDER CONTROLLER FOR ATTACHABLE SELECTION
def enum_attachable_geometries(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

def enum_attachable_textures(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

def enum_fake_attachable_material_patterns(self: Any, context: Context) -> list[tuple[str, str, str]]: ...

class MCBLEND_AttachableRenderController:
    active_attachable_pk: int
    primary_key: int
    identifier: str
    geometries: str
    textures: str
    material_patterns: CollectionProperty[MCBLEND_AttachableMaterialPattern]
    fake_material_patterns: str


# RESOURCE PACK (PROJECT)
def update_selected_entity(self: Any, context: Context) -> None: ...

def update_selected_attachable(self: Any, context: Context) -> None: ...

class MCBLEND_ProjectProperties:
    importer_type: Literal["ENTITY", "ATTACHABLE"]
    rp_path: str
    selected_entity: str
    entities: CollectionProperty[MCBLEND_DbEntry]
    entity_render_controllers: CollectionProperty[
        MCBLEND_EntityRenderController]

    selected_attachable: str
    attachables: CollectionProperty[MCBLEND_DbEntry]
    attachable_render_controllers: CollectionProperty[
        MCBLEND_AttachableRenderController]
