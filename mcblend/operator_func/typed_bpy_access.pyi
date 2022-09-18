from bpy.types import (
    Context, Object, OperatorProperties, Collection, CollectionObjects,
    CollectionChildren, ViewLayer, LayerObjects, MaterialSlot)

from .pyi_types import CollectionProperty, DataObjects, ArmatureDataBones

from ..object_data import MCBLEND_EventProperties, MCBLEND_ObjectProperties
from ..uv_data import MCBLEND_UvGroupProperties
from ..resource_pack_data import MCBLEND_ProjectProperties

def get_context_object(context: Context) -> Object: ...

def get_context_scene_mcblend_project(context: Context) ->\
    MCBLEND_ProjectProperties: ...

def get_context_scene_mcblend_events(context: Context) ->\
    CollectionProperty[MCBLEND_EventProperties]: ...

def get_context_scene_mcblend_active_event(context: Context) -> int: ...

def set_context_scene_mcblend_active_event(context: Context, value: int) ->\
    None: ...

def get_context_scene_mcblend_uv_groups(context: Context) ->\
    CollectionProperty[MCBLEND_UvGroupProperties]: ...

def get_context_selected_objects(context: Context) -> list[Object]: ...

def get_data_objects() -> DataObjects[Object]: ...

def get_object_mcblend(object: Object) -> MCBLEND_ObjectProperties: ...

def set_operator_property(
    operator: OperatorProperties, name: str,
    value: bool | int | float | str | list | dict) -> None: ...

def new_colection(name: str) -> Collection: ...

def get_collection_objects(collection: Collection) -> CollectionObjects: ...

def get_collection_children(collection: Collection) -> CollectionChildren: ...

def get_view_layer_objects(view_layer: ViewLayer) -> LayerObjects: ...

def get_object_material_slots(object: Object) -> list[MaterialSlot]: ...

def get_armature_data_bones(armature: Object) -> ArmatureDataBones: ...
