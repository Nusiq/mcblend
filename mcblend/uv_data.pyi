'''
Custom blender objects with additional properties of the UV.
'''
from typing import Dict, List, Any

from bpy.types import PropertyGroup
from operator_func.extra_types import Vector3d, Vector2d, Vector2di
from .operator_func.pyi_types import CollectionProperty

# UV mask
class MCBLEND_StripeProperties(PropertyGroup):
    '''Properties of a UV mask stripe.'''
    width: int
    width_relative: float
    strength: float
    def json(self, relative: bool) -> Dict[str, Any]: ...

class MCBLEND_ColorProperties(PropertyGroup):
    '''Properties of a UV mask color.'''
    color: Vector3d
    def json(self) -> List[float]: ...

class MCBLEND_UvMaskProperties(PropertyGroup):
    '''Properties of UV mask.'''
    ui_hidden: bool
    ui_collapsed: bool
    mask_type: str  # enum
    mode: str # enum
    children: int
    colors: CollectionProperty[MCBLEND_ColorProperties]
    interpolate: bool
    normalize: bool
    p1_relative: Vector2d
    p2_relative: Vector2d
    p1: Vector2di
    p2: Vector2di
    stripes: CollectionProperty[MCBLEND_StripeProperties]
    relative_boundaries: bool
    expotent: float
    strength: Vector2d
    hard_edge: bool
    horizontal: bool
    use_seed: bool
    seed: int
    color: MCBLEND_ColorProperties  # PointerProperty

    def json(self) -> Dict[str, Any]: ...

# UV group
def get_unused_uv_group_name(base_name: str, i: int=1) -> str: ...

def _update_uv_group_name(
        uv_group: MCBLEND_UvGroupProperties, new_name: str,
        update_references: bool) -> None: ...

def _set_uv_group_name(self: Any, value: str) -> None: ...

def _get_uv_group_name(self: Any) -> str: ...

class MCBLEND_UvGroupProperties(PropertyGroup):
    name: str
    side1: CollectionProperty[MCBLEND_UvMaskProperties]
    side2: CollectionProperty[MCBLEND_UvMaskProperties]
    side3: CollectionProperty[MCBLEND_UvMaskProperties]
    side4: CollectionProperty[MCBLEND_UvMaskProperties]
    side5: CollectionProperty[MCBLEND_UvMaskProperties]
    side6: CollectionProperty[MCBLEND_UvMaskProperties]

    def json(self) -> Dict[str, Any]: ...
