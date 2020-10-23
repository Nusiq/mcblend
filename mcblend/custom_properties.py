from typing import Dict, List, Optional
from dataclasses import dataclass

import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty, FloatProperty,
    FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty,
    IntVectorProperty
)

from .operator_func.texture_generator import (
    list_mask_types_as_blender_enum, UvMaskTypes,
    list_mix_mask_modes_as_blender_enum)


# UV-mask stripe properties
class OBJECT_NusiqMcblendStripeProperties(bpy.types.PropertyGroup):
    '''Properties of a UV-mask stripe.'''
    width: IntProperty(  # type: ignore
        name='Width', default=1)
    width_relative: FloatProperty(  # type: ignore
        name='Width', min=0.0, max=1.0, default=0.1)
    strength: FloatProperty(  # type: ignore
        name='Strength', min=0.0, max=1.0, default=1.0)

    def json(self, relative: bool) -> Dict:
        '''
        :returns: JSON representation of this object.
        '''
        result = {'strength': self.strength}
        if relative:
            result['width'] = self.width_relative
        else:
            result['width'] = self.width
        return result


# UV-mask color properties
class OBJECT_NusiqMcblendColorProperties(bpy.types.PropertyGroup):
    '''Properties of a UV-mask color.'''
    color: FloatVectorProperty(  # type: ignore
        name='Color',  subtype='COLOR',
        min=0, max=1, step=1000, default=(1.0, 1.0, 1.0))

    def json(self) -> List[float]:
        '''
        :returns: JSON representation of this object
        '''
        return list(self.color)

# UV-mask properties
class OBJECT_NusiqMcblendUvMaskProperties(bpy.types.PropertyGroup):
    '''Properties of UV-mask.'''
    ui_hidden: BoolProperty(  # type: ignore
        name='Hide', default=False)
    ui_collapsed: BoolProperty(  # type: ignore
        name='Collapse', default=False)
    mask_type: EnumProperty(  # type: ignore
        items=list_mask_types_as_blender_enum,
        name='Mask type')

    # mode: str  # MixMask
    mode: EnumProperty(  # type: ignore
        items=list_mix_mask_modes_as_blender_enum,
        name='Mix mode')
    # MixMask
    children: IntProperty(  # type: ignore
        name='Number of children', min=1, default=2)
    # colors: List[Color]  # ColorPaletteMask
    colors: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendColorProperties,
        name='Colors')
    # interpolate: bool  # ColorPaletteMask
    interpolate: BoolProperty(  # type: ignore
        name='Interpolate')
    # normalize: bool  # ColorPaletteMask
    normalize: BoolProperty(  # type: ignore
        name='Normalize')
    # p1: Tuple[float, float]  # GradientMask EllipseMask RectangleMask
    p1_relative: FloatVectorProperty(  # type: ignore
        name='Point A', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p2: Tuple[float, float]  # GradientMask EllipseMask RectangleMask
    p2_relative: FloatVectorProperty(  # type: ignore
        name='Point B', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p1: Tuple[float, float]  # GradientMask EllipseMask RectangleMask
    p1: IntVectorProperty(  # type: ignore
        name='Point A', default=(0.1, 0.1), size=2)
    # p2: Tuple[float, float]  # GradientMask EllipseMask RectangleMask
    p2: IntVectorProperty(  # type: ignore
        name='Point B', default=(0.9, 0.9), size=2)
    # stripes: List[Stripe]  # GradientMask StripesMask
    stripes: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendStripeProperties,
        name='Stripes')
    # relative_boundaries: bool  # GradientMask EllipseMask RectangleMask
    # StripesMask
    relative_boundaries: BoolProperty(  # type: ignore
        name='Relative boundaries')
    # expotent: float  # GradientMask EllipseMask RectangleMask RandomMask
    #  MixMask
    expotent: FloatProperty(  # type: ignore
        name='Expotent', default=1.0, soft_min=-10.0, soft_max=10.0)
    # strength: Tuple[float, float]  # EllipseMask RectangleMask RandomMask
    #  MixMask
    strength: FloatVectorProperty(  # type: ignore
        min=0.0, max=1.0, default=(0.0, 1.0), size=2)
    # hard_edge: bool  # EllipseMask RectangleMask
    hard_edge: BoolProperty(  # type: ignore
        name='Hard edge')
    # horizontal: bool  # StripesMask
    horizontal: BoolProperty(  # type: ignore
        name='Horizontal')
    # seed: Optional[int]  # RandomMask
    use_seed: BoolProperty(  # type: ignore
        name='Use seed')
    seed: IntProperty(  # type: ignore
        name='Seed')
    # color: Tuple[float, float, float]  # ColorMask
    color: PointerProperty(  # type: ignore
        type=OBJECT_NusiqMcblendColorProperties,
        name='Color')

    def json(self) -> Dict:
        '''
        :returns: JSON represetnation of this object.
        '''
        result = {
            "mask_type": self.mask_type
        }
        if self.mask_type == UvMaskTypes.MIX_MASK.value:
            result['mode'] = self.mode
            result['children'] = self.children
        if self.mask_type == UvMaskTypes.COLOR_PALLETTE_MASK.value:
            result['colors'] = [color.json() for color in self.colors]
            result['interpolate'] = self.interpolate
            result['normalize'] = self.normalize
        if self.mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value]:
            if self.relative_boundaries:
                result['p1'] = list(self.p1_relative)
                result['p2'] = list(self.p2_relative)
            else:
                result['p1'] = list(self.p1)
                result['p2'] = list(self.p2)
        if self.mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.STRIPES_MASK.value]:
            result['stripes'] = [
                stripe.json(self.relative_boundaries)
                for stripe in self.stripes]
        if self.mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value,
                UvMaskTypes.STRIPES_MASK.value]:
            result['relative_boundaries'] = self.relative_boundaries
        if self.mask_type in [
                UvMaskTypes.GRADIENT_MASK.value, UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value, UvMaskTypes.MIX_MASK.value,
                UvMaskTypes.RANDOM_MASK.value]:
            result['expotent'] = self.expotent
        if self.mask_type in [
                UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value, UvMaskTypes.MIX_MASK.value,
                UvMaskTypes.RANDOM_MASK.value]:
            result['strength'] = list(self.strength)
        if self.mask_type in [
                UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value]:
            result['hard_edge'] = self.hard_edge
        if self.mask_type == UvMaskTypes.STRIPES_MASK.value:
            result['horizontal'] = self.horizontal
        if self.mask_type == UvMaskTypes.RANDOM_MASK.value:
            result['use_seed'] = self.use_seed
            result['seed'] = self.seed
        if self.mask_type == UvMaskTypes.COLOR_MASK.value:
            result['color'] = self.color.json()
        return result

# UV-group properties
def get_unused_uv_group_name(base_name: str, i=1):
    '''
    Gets the name of UV-group which is not used by any other UV-group. Uses
    the base name and adds number at the end of it to find unique name with
    pattern :code:`{base_name}.{number:04}`.
    '''
    uv_groups = bpy.context.scene.nusiq_mcblend_uv_groups
    name = base_name  # f'{base_name}.{i:04}'
    while name in uv_groups.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def _update_uv_group_name(uv_group, new_name: str):
    # Update the names of all of the meshes
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj_props = obj.nusiq_mcblend_object_properties
            if obj_props.uv_group == uv_group.name:
                obj_props.uv_group = new_name
    # Update the name of the UV group
    uv_group['name'] = new_name

def _set_uv_group_name(self, value):
    groups = bpy.context.scene.nusiq_mcblend_uv_groups

    # Empty name is no allowed
    if value == '':
        return

    # If name already in use rename the other uv group
    for other_group in groups:
        if (  # Change the of the duplicate if there is one
                other_group.path_from_id() != self.path_from_id() and
                other_group.name == value):
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
            other_new_name = get_unused_uv_group_name(base_name, i)
            _update_uv_group_name(other_group, other_new_name)
            break
    _update_uv_group_name(self, value)

def _get_uv_group_name(self):
    if 'name' not in self:
        return ''
    return self['name']

class OBJECT_NusiqMcblendUvGroupProperties(bpy.types.PropertyGroup):
    '''Properties of UV-group.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description='The name of the UV group.',
        # The Add operator overwrites default value on creation to trigger the
        # update function
        default='',
        maxlen=1024, set=_set_uv_group_name, get=_get_uv_group_name)
    side1: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side1 of the cuboid.')
    side2: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side2 of the cuboid.')
    side3: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side3 of the cuboid.')
    side4: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side4 of the cuboid.')
    side5: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side5 of the cuboid.')
    side6: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side6 of the cuboid.')

    def json(self) -> Dict:
        '''
        :returns: JSON representation of this object.
        '''
        return {
            'version': 1,
            'name': self.name,
            'side1': [
                mask.json() for mask in self.side1
            ],
            'side2': [
                mask.json() for mask in self.side2
            ],
            'side3': [
                mask.json() for mask in self.side3
            ],
            'side4': [
                mask.json() for mask in self.side4
            ],
            'side5': [
                mask.json() for mask in self.side5
            ],
            'side6': [
                mask.json() for mask in self.side6
            ]
        }

# Model object properties
class OBJECT_NusiqMcblendObjectProperties(bpy.types.PropertyGroup):
    '''Custom properties of an object.'''
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

# Animation properties
class OBJECT_NusiqMcblendAnimationProperties(bpy.types.PropertyGroup):
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

# Mcblend properties
class OBJECT_NusiqMcblendExporterProperties(bpy.types.PropertyGroup):
    '''Global properties of Mcblend.'''
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="model",
        maxlen=1024
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