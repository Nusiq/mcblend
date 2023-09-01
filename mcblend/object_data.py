'''
Custom Blender objects with additional data for the objects and empties.
'''
from typing import Dict, List, Tuple
from enum import Enum

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    FloatProperty, IntVectorProperty, FloatVectorProperty,
    BoolProperty, CollectionProperty, EnumProperty, IntProperty,
    StringProperty)


from .operator_func.common import MeshType, AnimationLoopType, ModelOriginType
from .operator_func.typed_bpy_access import get_scene_mcblend_events
from .common_data import MCBLEND_JustName

# Animation properties
class EffectTypes(Enum):
    '''
    EffectTypes types of the effects in the event.
    '''
    SOUND_EFFECT='Sound Effect'
    PARTICLE_EFFECT='Particle Effect'

def list_effect_types_as_blender_enum(self, context):
    '''
    List effect types for EnumProperty.
    '''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in EffectTypes]

class MCBLEND_EffectProperties(PropertyGroup):
    '''
    An effect of an event (sound or particles)
    '''
    effect_type: EnumProperty(  # type: ignore
        items=list_effect_types_as_blender_enum,
        name='Effect type')
    effect: StringProperty(  # type: ignore
        name="Effect",
        description='The name of the effect',
        default='',
        maxlen=1024)
    locator: StringProperty(  # type: ignore
        name="Locator",
        description='The name of the locator',
        default='',
        maxlen=1024)
    pre_effect_script: StringProperty(  # type: ignore
        name="Pre effect script",
        description='A Molang script to run before the effect is played',
        default='',
        maxlen=2048)
    bind_to_actor: BoolProperty(  # type: ignore
        name="Bind to actor",
        description=(
            "Specifies whether the effect should be spawned in the world "
            "without being bound to the model"),
        default=True)

def get_unused_event_name(base_name: str, i=1):
    '''
    Gets the name of event which is not used by any other event in the
    animation. Uses the base name and adds number at the end of it to find
    unique name with pattern :code:`{base_name}.{number:04}`.

    This function assumes there is an active event and active animation. It
    will throw errors without asserting these conditions.
    '''
    events = get_scene_mcblend_events(bpy.context)
    name = base_name
    while name in events.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def _update_event_name(event, new_name: str):
    event['name'] = new_name


def _set_event_name(self: 'MCBLEND_EventProperties', value: str):
    events = get_scene_mcblend_events(bpy.context)
    # Empty name is no allowed
    if value == '':
        return

    # If name already in use rename the other uv group
    for other_event in events:
        if (  # Change the of the duplicate if there is one
                other_event.path_from_id() != self.path_from_id() and
                other_event.name == value):
            # Get starting name index
            i = 1
            base_name = value
            split_name = value.split('.')
            try:
                prev_i = int(split_name[-1])
                i = i if prev_i <= 0 else prev_i
                base_name = '.'.join(split_name[:-1])
            except ValueError:
                pass
            other_new_name = get_unused_event_name(base_name, i)
            _update_event_name(other_event, other_new_name)
            break
        _update_event_name(self, value)

def _get_event_name(self):
    if 'name' not in self:
        return ''
    return self['name']

class MCBLEND_EventProperties(PropertyGroup):
    '''
    A collection of sound and particle events.
    '''
    name: StringProperty(  # type: ignore
        name="Name",
        description="The name of the of the event",
        # The Add operator overwrites default value on creation to trigger the
        # update function
        default='',
        maxlen=1024, set=_set_event_name, get=_get_event_name)
    effects: CollectionProperty(  # type: ignore
        type=MCBLEND_EffectProperties,
        name='Sound effects')

    def get_effects_dict(self) -> Tuple[List[Dict], List[Dict]]:
        '''
        Returns tuple of two lists (sound effects, particle effects).
        '''
        sound_effects: List[Dict] = []
        particle_effects: List[Dict] = []
        for effect in self.effects:
            if effect.effect_type == EffectTypes.PARTICLE_EFFECT.value:
                result = {"effect": effect.effect}
                if effect.locator != '':
                    result["locator"] = effect.locator
                if effect.pre_effect_script != '':
                    result["pre_effect_script"] = (
                        effect.pre_effect_script)
                if not effect.bind_to_actor:
                    result["bind_to_actor"] = effect.bind_to_actor
                particle_effects.append(result)
            elif effect.effect_type == EffectTypes.SOUND_EFFECT.value:
                sound_effects.append({"effect": effect.effect})
            else:
                raise ValueError('Unknown effect type.')
        return sound_effects, particle_effects

class MCBLEND_TimelineMarkerProperties(PropertyGroup):
    '''Saves the data about a timeline marker.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description="The name of the timeline marker",
        default="marker",
        maxlen=1024
    )
    frame: IntProperty(  # type: ignore
        name="Frame",
        default=0
    )

class MCBLEND_AnimationProperties(PropertyGroup):
    '''Properties of an animation template.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description="The name of the animation",
        default="animation",
        maxlen=1024
    )
    single_frame: BoolProperty(  # type: ignore
        name="Single frame",
        description=(
            "Whether the animation should be exported as a single, "
            "looped frame"),
        default=False,
    )
    skip_rest_poses: BoolProperty(  # type: ignore
        name="Skip rest poses",
        description=(
            "Whether bone transformations that represent a rest position "
            "throughout the whole animation should be ignored"),
        default=False,
    )
    override_previous_animation: BoolProperty(  # type: ignore
        name="Override previos animation",
        description=(
            "Sets the \"override_previous_animation\" property of the "
            "Minecraft animation"),
        default=False,
    )
    anim_time_update: StringProperty(  # type: ignore
        name="anim_time_update",
        description=(
            "Sets the \"anim_time_update\" value of the Minecraft animation"),
        default="",
        maxlen=1024
    )
    loop: EnumProperty(  # type: ignore
        items=(
            (  # type: ignore
                AnimationLoopType.TRUE.value, AnimationLoopType.TRUE.value,
                'The animation is looped'
            ),
            (  # type: ignore
                AnimationLoopType.FALSE.value, AnimationLoopType.FALSE.value,
                'The animation has no effect on entity after it finished'
            ),
            (  # type: ignore
                AnimationLoopType.HOLD_ON_LAST_FRAME.value,
                AnimationLoopType.HOLD_ON_LAST_FRAME.value,
                'After the end of animation the entity stays in the pose from '
                'the last frame'
            )
        ), name='Loop')
    frame_start: IntProperty(  # type: ignore
        name="Frame start",
        description="The first frame of the animation",
        default=0,
        min=0
    )
    frame_current: IntProperty(  # type: ignore
        name="Frame current",
        description="The current frame of the animation",
        default=100,
        min=0
    )
    frame_end: IntProperty(  # type: ignore
        name="Frame end",
        description="The last frame of the animation",
        default=100,
        min=0
    )
    timeline_markers: CollectionProperty(  # type: ignore
        type=MCBLEND_TimelineMarkerProperties,
    )
    nla_tracks: CollectionProperty(  # type: ignore
        type=MCBLEND_JustName
    )

# Material properties
def list_mesh_types_as_blender_enum(self, context):
    '''List mesh types for EnumProperty.'''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in MeshType]

class MCBLEND_FakeRcMaterialProperties(PropertyGroup):
    '''
    Pattern-material pair for MCBLEND_FakeRcProperties object.
    '''
    pattern: StringProperty(  # type: ignore
        name="Pattern",
        description=(
            "The pattern that matches the name of the bones that should use "
            "this material"),
        default="", maxlen=1024)
    material: StringProperty(  # type: ignore
        name="Material",
        description="The name of the material used by this render controller",
        default="",
        maxlen=1024
    )

class MCBLEND_FakeRcProperties(PropertyGroup):
    '''
    Armature property group similar to Minecraft render controller used for
    generating Minecraft materials.
    '''
    texture: StringProperty(  # type: ignore
        name="Texture",
        description="The name of the texture used by this render controller",
        default="",
        maxlen=1024
    )
    materials: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcMaterialProperties, name='Materials')

class MCBLEND_ObjectProperties(PropertyGroup):
    '''Custom properties of an object.'''
    # ARMATURE PROPERTIES (equivalent of minecraft model)
    model_name: StringProperty(  # type: ignore
        name="Model name",
        description="The name of the Minecraft model used during exporting",
        default="model",
        maxlen=1024
    )
    texture_template_resolution: IntProperty(  # type: ignore
        name="Template resolution",
        description=(
            "The number of pixels per single unit of length of the texture "
            "size"
        ),
        default=1,
        min=1,
        soft_max=5,
    )
    allow_expanding: BoolProperty(  # type: ignore
        name="Allow texture expanding",
        description=(
            "Whether the Automatic UV mapping is allowed to expand the "
            "texture size"),
        default=True,
    )
    generate_texture: BoolProperty(  # type: ignore
        name="Generate texture",
        description=(
            "Whether the Automatic UV mapping should generate a texture"
        ),
        default=True,
    )
    visible_bounds_offset: FloatVectorProperty(  # type: ignore
        name="Visible bounds offset",
        description=(
            "The \"visible_bounds_offset\" property of the Minecraft model"),
        default=(0.0, 0.0, 0.0)
    )
    visible_bounds_width: FloatProperty(  # type: ignore
        name="Visible bounds width",
        description=(
            "The \"visible_bounds_width\" property of the Minecraft model"),
        default=1.0
    )
    visible_bounds_height: FloatProperty(  # type: ignore
        name="Visible bounds height",
        description=(
            "The \"visible_bounds_height\" property of the Minecraft model"),
        default=1.0
    )
    texture_width: IntProperty(  # type: ignore
        name="Texture width",
        description="The \"texture_width\" property of the Minecraft model",
        default=64,
        min=1
    )
    texture_height: IntProperty(  # type: ignore
        name="Texture height",
        description="The \"texture_height\" property of the Minecraft model",
        default=64,
        min=1
    )
    # RENDER CONTROLLERS (armature properties used for generating materials)
    render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcProperties)
    # ANIMATIONS
    # Animation properties
    active_animation: IntProperty(default=0)  # type: ignore
    animations: CollectionProperty(  # type: ignore
        type=MCBLEND_AnimationProperties)

    # CUBE PROPERTIES
    mirror: BoolProperty(  # type: ignore
        name="Mirror",
        description=(
            "The \"mirror\" property of this cube in the Minecraft model"),
        default=False,
    )
    uv_group: StringProperty(  # type: ignore
        name="UV group",
        description=(
            "The name of the UV group that this cube belongs to"),
        default="",
        maxlen=1024
    )
    inflate: FloatProperty(  # type: ignore
        name="Inflate",
        description=(
            "The \"inflate\" value of this cube in the Minecraft model"),
        default=0.0
    )
    mesh_type: EnumProperty(  # type: ignore
        items=list_mesh_types_as_blender_enum, # type: ignore
        name='Mesh type')
    min_uv_size: IntVectorProperty(  # type: ignore
        name="Min UV bound", default=(0, 0, 0), min=0,
        description=(
            "The minimum size of the UV map for this cube for its "
            "width, height and depth")
    )
    model_origin: EnumProperty(  # type: ignore
        items=(
            (  # type: ignore
                ModelOriginType.WORLD.value, ModelOriginType.WORLD.value,
                'Use the world origin as the model origin'
            ),
            (  # type: ignore
                ModelOriginType.ARMATURE.value, ModelOriginType.ARMATURE.value,
                'Use the armature origin as the model origin'
            ),
        ),
        name='Model origin',
        default=ModelOriginType.ARMATURE.value)

class MCBLEND_BoneProperties(PropertyGroup):
    '''
    Custom properties of a bone
    '''
    binding: StringProperty(  # type: ignore
        name="Binding",
        description=(
            "The \"binding\" property of this bone in the "
            "Minecraft model"),
        default="",
        maxlen=1024
    )
