from typing import Iterable, overload, Any
from bpy.types import (
    Context, Object, OperatorProperties, Collection, CollectionObjects,
    CollectionChildren, ViewLayer, LayerObjects, MaterialSlot, Constraint,
    ObjectConstraints, PoseBoneConstraints, Image, EditBone,
    MeshUVLoopLayer, MeshPolygon, PoseBone, Mesh, Scene, Action, FCurve,
    AnimData, NlaTrack, MeshVertex, Material, NodeTree, Node, NodeSocket,
    MeshUVLoop, LayerCollection)
from mathutils import Matrix, Euler, Vector, Quaternion
from .common import NumpyTable
from .pyi_types import (
    CollectionProperty, DataMeshes, ArmatureDataBones, DataImages,
    ObjectDataMaterials,
    MeshUVLoopLayerData, ObjectDataEdges,
    ArmaturePoseBones,
    ObjectDataPolygons)

from ..object_data import (
    MCBLEND_EventProperties, MCBLEND_ObjectProperties, MCBLEND_BoneProperties)
from ..uv_data import MCBLEND_UvGroupProperties
from ..resource_pack_data import MCBLEND_ProjectProperties

@overload
def get_mcblend(obj: Object) -> MCBLEND_ObjectProperties: ...

@overload
def get_mcblend(obj: PoseBone) -> MCBLEND_BoneProperties: ...

def get_scene_mcblend_active_event(context: Context) -> int: ...

def get_scene_mcblend_active_uv_group(context: Context) -> int: ...

def get_scene_mcblend_active_uv_groups_side(context: Context) -> int: ...

def get_scene_mcblend_events(context: Context) ->\
    CollectionProperty[MCBLEND_EventProperties]: ...

def get_scene_mcblend_project(context: Context) ->\
    MCBLEND_ProjectProperties: ...

def get_scene_mcblend_uv_groups(context: Context) ->\
    CollectionProperty[MCBLEND_UvGroupProperties]: ...

def set_node_tree(obj: Node, node_tree: NodeTree) -> None: ...

def set_operation(obj: Node, operation: str) -> None: ...

def set_operator_property(
    operator: OperatorProperties, name: str,
    value: bool | int | float | str | list[Any] | dict[Any, Any] | Object
) -> None: ...

def set_parent(obj: Object, parent: Object | None) -> None: ...

def set_pose_bone_constraint_property(
    constraint: Constraint, name: str,
    value: bool | int | float | str | list[Any] | dict[Any, Any] | Object
) -> None: ...

def set_scene_mcblend_active_event(
    context: Context, value: int) -> None: ...

def set_scene_mcblend_active_uv_group(
    context: Context, value: int) -> None: ...

def set_use_clamp(obj: Node, use_clamp: bool) -> None: ...

def set_uv(obj: MeshUVLoop, uv: tuple[float, float] | NumpyTable) -> None: ...

def set_view_layer_objects_active(context: Context, obj: Object) -> None: ...

@overload
def to_euler(
    obj: Matrix, order: str, euler_compact: None | Euler=None
) -> Euler: ...

@overload
def to_euler(
    obj: Quaternion, order: str, euler_compact: None | Euler=None
) -> Euler: ...
