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

def get_mcblend_active_event(scene: Scene) -> int: ...

def get_mcblend_active_uv_group(scene: Scene) -> int: ...

def get_mcblend_active_uv_groups_side(scene: Scene) -> int: ...

def get_mcblend_events(scene: Scene) ->\
    CollectionProperty[MCBLEND_EventProperties]: ...

def get_mcblend_project(scene: Scene) ->\
    MCBLEND_ProjectProperties: ...

def get_mcblend_uv_groups(scene: Scene) ->\
    CollectionProperty[MCBLEND_UvGroupProperties]: ...

def set_mcblend_active_event(
    scene: Scene, value: int) -> None: ...

def set_mcblend_active_uv_group(
    scene: Scene, value: int) -> None: ...
