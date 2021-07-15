'''
Custom Blender objects with additional data for the objects and empties.
'''
import bpy
from bpy.props import (
    FloatProperty, IntVectorProperty, FloatVectorProperty,
    BoolProperty, CollectionProperty, EnumProperty, IntProperty,
    StringProperty)


from .operator_func.common import MeshType
from typing import Dict, List, Tuple
from enum import Enum

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

class MCBLEND_EffectProperties(bpy.types.PropertyGroup):
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
    events = bpy.context.scene.mcblend_events

    name = base_name
    while name in events.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def _update_event_name(event, new_name: str):
    event['name'] = new_name

def _set_event_name(self, value):
    events = bpy.context.scene.mcblend_events

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

class MCBLEND_EventProperties(bpy.types.PropertyGroup):
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
        type=MCBLEND_EffectProperties,
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

class MCBLEND_TimelineMarkerProperties(bpy.types.PropertyGroup):
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

class MCBLEND_AnimationProperties(bpy.types.PropertyGroup):
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
        type=MCBLEND_TimelineMarkerProperties, name='Timeline Markers',
        description='Timeline markers related to this animation.'
    )
    nla_tracks: CollectionProperty(  # type: ignore
        type=MCBLEND_JustName
    )

# Material properties
def list_mesh_types_as_blender_enum(self, context):
    '''List mesh types for EnumProperty.'''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in MeshType]

class MCBLEND_FakeRcMaterialProperties(bpy.types.PropertyGroup):
    '''
    Pattern-material pair for MCBLEND_FakeRcProperties object.
    '''
    pattern: StringProperty(  # type: ignore
        name="", description="The bone name pattern for assigning material.",
        default="", maxlen=1024)
    material: StringProperty(  # type: ignore
        name="",
        description="Name of the material used by this render controller",
        default="",
        maxlen=1024
    )

class MCBLEND_FakeRcProperties(bpy.types.PropertyGroup):
    '''
    Armature property group similar to Minecraft render controller used for
    generating Minecraft materials.
    '''
    texture: StringProperty(  # type: ignore
        name="",
        description="Name of the texture used by this render controller",
        default="",
        maxlen=1024
    )
    materials: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcMaterialProperties, name='Materials')

class MCBLEND_ObjectProperties(bpy.types.PropertyGroup):
    '''Custom properties of an object.'''
    # ARMATURE PROPERTIES (equivalent of minecraft model)
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="model",
        maxlen=1024
    )
    texture_template_resolution: IntProperty(  # type: ignore
        name="Template texture resolution",
        description=(
            'Sets the resolution of the template texture.'
            'describes how many pixels on the image is represented by one '
            'texture_width or texture_height unit in model definition. '
            'The value of 1 gives the standard minecraft texture '
            'resolution.'
        ),
        default=1,
        min=1,
        soft_max=5,
    )
    allow_expanding: BoolProperty(  # type: ignore
        name="Allow Texture Expanding",
        description="Allows expanding texture during texture generation.",
        default=True,
    )
    generate_texture: BoolProperty(  # type: ignore
        name="Generate texture",
        description="Generates texture during UV mapping.",
        default=True,
    )
    visible_bounds_offset: FloatVectorProperty(  # type: ignore
        name="Visible bounds offset",
        description="visible_bounds_offset of the model",
        default=(0.0, 0.0, 0.0)
    )
    visible_bounds_width: FloatProperty(  # type: ignore
        name="Visible bounds width",
        description="visible_bounds_width of the model",
        default=1.0
    )
    visible_bounds_height: FloatProperty(  # type: ignore
        name="Visible bounds height",
        description="visible_bounds_height of the model",
        default=1.0
    )
    texture_width: IntProperty(  # type: ignore
        name="",
        description="Minecraft UV parameter width.",
        default=64,
        min=1
    )
    texture_height: IntProperty(  # type: ignore
        name="",
        description=(
            "Minecraft UV parameter height. If you set it to 0 than the height"
            " of the texture will be picked automatically for you."
        ),
        default=64,
        min=1
    )
    # RENDER CONTROLLERS (armature properties used for generating materials)
    render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_FakeRcProperties, name="Render Controllers"
    )
    # ANIMATIONS
    # Animation properties
    active_animation: IntProperty(default=0)  # type: ignore
    animations: CollectionProperty(  # type: ignore
        type=MCBLEND_AnimationProperties)

    # CUBE PROPERTIES
    mirror: BoolProperty(  # type: ignore
        name="Mirror",
        description="Defines how to layout the UV during UV generation.",
        default=False,
    )
    uv_group: StringProperty(  # type: ignore
        name="UV group",
        description=(
            "Objects with the same UV group can be mapped to the same spot on "
            "the texture if they have the same dimensions. Empty string means "
            "that the object doesn't belong to any UV group."),
        default="",
        maxlen=1024
    )
    is_bone: BoolProperty(  # type: ignore
        name="Export as bone",
        description=(
            "If true than this object will be exported as minecraft bone."),
        default=False,
    )
    inflate: FloatProperty(  # type: ignore
        name="Inflate",
        description="The inflate value of this object.",
        default=0.0
    )
    mesh_type: EnumProperty(  # type: ignore
        items=list_mesh_types_as_blender_enum, # type: ignore
        name='Mesh type')
    min_uv_size: IntVectorProperty(  # type: ignore
        name="Min UV size", default=(0.0, 0.0, 0.0), min=0,
        description=(
            "The lower UV boundary of the length of X dimension of a cube. If "
            "it's greater than the actual X, then the UV-mapper will act as "
            "if the X were equal to this value.")
    )
