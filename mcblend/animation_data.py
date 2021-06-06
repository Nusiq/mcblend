'''
Custom blender objects with animation data.
'''
from enum import Enum
from typing import Dict, List, Tuple

import bpy
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty, IntProperty,
    StringProperty)

# Sounds and Particles
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

class NUSIQ_MCBLEND_EffectProperties(bpy.types.PropertyGroup):
    '''
    An effect of an event (sound or particles)
    '''
    effect_type: EnumProperty(  # type: ignore
        items=list_effect_types_as_blender_enum,
        name='Effect type')
    effect: StringProperty(  # type: ignore
        name="Effect",
        description='The identifier of the sound effect.',
        default='',
        maxlen=1024)
    locator: StringProperty(  # type: ignore
        name="Locator",
        description='The identifier of the locator effect.',
        default='',
        maxlen=1024)
    pre_effect_script: StringProperty(  # type: ignore
        name="Locator",
        description='A Molang script that will be run when the particle emitter is initialized.',
        default='',
        maxlen=2048)
    bind_to_actor: BoolProperty(  # type: ignore
        name="Bind to actor",
        description="Whether the should be spawned in the world without being bound to an actor.",
        default=True)

def get_unused_event_name(base_name: str, i=1):
    '''
    Gets the name of event which is not used by any other event in the
    animation. Uses the base name and adds number at the end of it to find
    unique name with pattern :code:`{base_name}.{number:04}`.

    This function assumes there is an active event and active animation. It
    will throw errors without asserting these conditions.
    '''
    events = bpy.context.scene.nusiq_mcblend_events

    name = base_name
    while name in events.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def _update_event_name(event, new_name: str):
    event['name'] = new_name

def _set_event_name(self, value):
    events = bpy.context.scene.nusiq_mcblend_events

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

class NUSIQ_MCBLEND_EventProperties(bpy.types.PropertyGroup):
    '''
    A collection of sound and particle events.
    '''
    name: StringProperty(  # type: ignore
        name="Name",
        description=(
            "The name of the of the event. Also used to identify timeline "
            "markers that trigger this event."),
        # The Add operator overwrites default value on creation to trigger the
        # update function
        default='',
        maxlen=1024, set=_set_event_name, get=_get_event_name)
    effects: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_EffectProperties,
        description='Collection of effects triggered of this event.',
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

# Animations
class NUSIQ_MCBLEND_TimelineMarkerProperties(bpy.types.PropertyGroup):
    '''Saves the data about a timeline marker.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description="Name of the timeline marker.", default="marker",
        maxlen=1024
    )
    frame: IntProperty(  # type: ignore
        name="Frame",
        description="The frame of the timeline marker.",
        default=0
    )

class NUSIQ_MCBLEND_AnimationProperties(bpy.types.PropertyGroup):
    '''Properties of an animation template.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description="Name of the animation.", default="animation",
        maxlen=1024
    )
    single_frame: BoolProperty(  # type: ignore
        name="Single frame",
        description="Exports current pose as single frame animation",
        default=False,
    )
    skip_rest_poses: BoolProperty(  # type: ignore
        name="Skip rest poses",
        description=(
            "Whether bone transformations that represent a rest position "
            "throughout the whole animation should be ignored."),
        default=False,
    )
    anim_time_update: StringProperty(  # type: ignore
        name="anim_time_update",
        description="Adds anim_time_update value unless is left empty",
        default="",
        maxlen=1024
    )
    loop: BoolProperty(  # type: ignore
        name="Loop",
        description="Decides if animation should be looped",
        default=True,
    )
    frame_start: IntProperty(  # type: ignore
        name="Frame start",
        description="The first frame of the animation.",
        default=0,
        min=0
    )
    frame_current: IntProperty(  # type: ignore
        name="Frame current",
        description="The current frame of the animation.",
        default=100,
        min=0
    )
    frame_end: IntProperty(  # type: ignore
        name="Frame end",
        description="The last frame of the animation.",
        default=100,
        min=0
    )
    timeline_markers: CollectionProperty(  # type: ignore
        type=NUSIQ_MCBLEND_TimelineMarkerProperties, name='Timeline Markers',
        description='Timeline markers related to this animation.'
    )
