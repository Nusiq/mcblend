from __future__ import annotations
from typing import Dict, List, Literal, Tuple
from enum import Enum
from bpy.types import Context
from .operator_func.pyi_types import CollectionProperty
from .common_data import MCBLEND_JustName

# Animation properties
class EffectTypes(Enum):
    SOUND_EFFECT: Literal['Sound Effect'] = ...
    PARTICLE_EFFECT: Literal['Particle Effect'] = ...

def list_effect_types_as_blender_enum(
        self: MCBLEND_EffectProperties, context: Context
    ) -> list[tuple[str, str, str]]: ...

class MCBLEND_EffectProperties:
    effect_type: str
    effect: str
    locator: str
    pre_effect_script: str
    bind_to_actor: bool

def get_unused_event_name(base_name: str, i: int=1) -> str: ...

def _update_event_name(event: MCBLEND_EventProperties, new_name: str) -> None: ...

def _set_event_name(self: MCBLEND_EventProperties, value: str) -> None: ...

def _get_event_name(self: MCBLEND_EventProperties) -> str: ...

class MCBLEND_EventProperties:
    name: str
    effects: CollectionProperty[MCBLEND_EffectProperties]

    def get_effects_dict(self) -> Tuple[List[Dict], List[Dict]]: ...

class MCBLEND_TimelineMarkerProperties:
    name: str
    frame: int

class MCBLEND_AnimationProperties:
    name: str
    world_origin: str
    single_frame: bool
    skip_rest_poses: bool
    override_previous_animation: bool
    anim_time_update: str
    loop: str
    frame_start: int
    frame_current: int
    frame_end: int
    timeline_markers: CollectionProperty[MCBLEND_TimelineMarkerProperties]
    nla_tracks: CollectionProperty[MCBLEND_JustName]

# Material properties
def list_mesh_types_as_blender_enum(
        self: MCBLEND_FakeRcMaterialProperties, context: Context
    ) -> list[tuple[str, str, str]]: ...

class MCBLEND_FakeRcMaterialProperties:
    pattern: str
    material: str

class MCBLEND_FakeRcProperties:
    texture: str
    materials: CollectionProperty[MCBLEND_FakeRcMaterialProperties]

class MCBLEND_ObjectProperties:
    model_name: str
    texture_template_resolution: int
    allow_expanding: bool
    generate_texture: bool
    visible_bounds_offset: tuple[float, float, float]
    visible_bounds_width: float
    visible_bounds_height: float
    texture_width: int
    texture_height: int
    render_controllers: CollectionProperty[MCBLEND_FakeRcProperties]
    active_animation: int
    animations: CollectionProperty[MCBLEND_AnimationProperties]
    mirror: bool
    uv_group: str
    inflate: float
    mesh_type: str  # enum
    min_uv_size: tuple[int, int, int]
    use_world_origin: bool

class MCBLEND_BoneProperties:
    binding: str
