# type: ignore
'''
Custom blender objects with additional properties of the UV.
'''
from typing import Dict, List, Any

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty, CollectionProperty, EnumProperty, FloatProperty,
    FloatVectorProperty, IntProperty, IntVectorProperty,
    PointerProperty, StringProperty)

from .operator_func.typed_bpy_access import (
    get_data_objects, get_mcblend, get_scene_mcblend_uv_groups)
from .operator_func.texture_generator import (
    UvMaskTypes, list_mask_types_as_blender_enum,
    list_mix_mask_modes_as_blender_enum)

# UV mask
class MCBLEND_StripeProperties(PropertyGroup):
    '''Properties of a UV mask stripe.'''
    width: IntProperty(  # type: ignore
        name='Width', default=1)
    width_relative: FloatProperty(  # type: ignore
        name='Width', min=0.0, max=1.0, default=0.1)
    strength: FloatProperty(  # type: ignore
        name='Strength', min=0.0, max=1.0, default=1.0)

    def json(self, relative: bool) -> Dict[str, Any]:
        '''
        :returns: JSON representation of this object.
        '''
        result = {'strength': self.strength}
        if relative:
            result['width'] = round(self.width_relative, 5)
        else:
            result['width'] = self.width
        return result

class MCBLEND_ColorProperties(PropertyGroup):
    '''Properties of a UV mask color.'''
    color: FloatVectorProperty(  # type: ignore
        name='Color',  subtype='COLOR',
        min=0, max=1, step=1000, default=(1.0, 1.0, 1.0))

    def json(self) -> List[float]:
        '''
        :returns: JSON representation of this object
        '''
        # 1/256 = 0.00390625 (8 digits precision)
        return [round(i, 8) for i in self.color]

class MCBLEND_UvMaskProperties(PropertyGroup):
    '''Properties of UV mask.'''
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
        type=MCBLEND_ColorProperties,
        name='Colors')
    # interpolate: bool  # ColorPaletteMask
    interpolate: BoolProperty(  # type: ignore
        name='Interpolate')
    # normalize: bool  # ColorPaletteMask
    normalize: BoolProperty(  # type: ignore
        name='Normalize')
    # p1: Vector2d  # GradientMask EllipseMask RectangleMask
    p1_relative: FloatVectorProperty(  # type: ignore
        name='Point A', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p2: Vector2d  # GradientMask EllipseMask RectangleMask
    p2_relative: FloatVectorProperty(  # type: ignore
        name='Point B', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p1: Vector2d  # GradientMask EllipseMask RectangleMask
    p1: IntVectorProperty(  # type: ignore
        name='Point A', default=(0, 0), size=2)
    # p2: Vector2d  # GradientMask EllipseMask RectangleMask
    p2: IntVectorProperty(  # type: ignore
        name='Point B', default=(0, 0), size=2)
    # stripes: List[Stripe]  # GradientMask StripesMask
    stripes: CollectionProperty(  # type: ignore
        type=MCBLEND_StripeProperties,
        name='Stripes')
    # relative_boundaries: bool  # GradientMask EllipseMask RectangleMask
    # StripesMask
    relative_boundaries: BoolProperty(  # type: ignore
        name='Relative boundaries')
    # expotent: float  # GradientMask EllipseMask RectangleMask RandomMask
    #  MixMask
    expotent: FloatProperty(  # type: ignore
        name='Expotent', default=1.0, soft_min=-10.0, soft_max=10.0)
    # strength: Vector2d  # EllipseMask RectangleMask RandomMask
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
    # color: Vector3d  # ColorMask
    color: PointerProperty(  # type: ignore
        type=MCBLEND_ColorProperties,
        name='Color')

    def json(self) -> Dict[str, Any]:
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
                result['p1'] = [round(i, 5) for i in self.p1_relative]
                result['p2'] = [round(i, 5) for i in self.p2_relative]
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
            result['expotent'] = round(self.expotent, 5)
        if self.mask_type in [
                UvMaskTypes.ELLIPSE_MASK.value,
                UvMaskTypes.RECTANGLE_MASK.value, UvMaskTypes.MIX_MASK.value,
                UvMaskTypes.RANDOM_MASK.value]:
            result['strength'] = [round(i, 5) for i in self.strength]
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

# UV group
def get_unused_uv_group_name(base_name: str, i: int=1):
    '''
    Gets the name of UV group which is not used by any other UV group. Uses
    the base name and adds number at the end of it to find unique name with
    pattern :code:`{base_name}.{number:04}`.
    '''
    uv_groups = get_scene_mcblend_uv_groups(bpy.context)
    name = base_name  # f'{base_name}.{i:04}'
    while name in uv_groups.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def _update_uv_group_name(uv_group, new_name: str, update_references: bool):
    # Update the names of all of the meshes
    if update_references:
        for obj in get_data_objects():
            if obj.type == "MESH":
                obj_props = get_mcblend(obj)
                if obj_props.uv_group == uv_group.name:
                    obj_props.uv_group = new_name
    # Update the name of the UV group
    uv_group['name'] = new_name

def _set_uv_group_name(self: Any, value: str):
    groups = get_scene_mcblend_uv_groups(bpy.context)

    # Empty name is no allowed
    if value == '':
        return

    # Objects use '' as the UV group name when they have no UV group.
    # The '' is also the default value of the UV group (but it's instantly
    # changed to something else on creation). This prevents assigning all
    # of the object without an UV group to newly added UV group.
    update_references = 'name' in self

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
            _update_uv_group_name(other_group, other_new_name, False)
            break
        _update_uv_group_name(self, value, update_references)

def _get_uv_group_name(self):
    if 'name' not in self:
        return ''
    return self['name']

class MCBLEND_UvGroupProperties(PropertyGroup):
    '''Properties of UV group.'''
    name: StringProperty(  # type: ignore
        name="Name",
        description='The name of the UV group.',
        # The Add operator overwrites default value on creation to trigger the
        # update function
        default='',
        maxlen=1024, set=_set_uv_group_name, get=_get_uv_group_name)
    side1: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side1 of the cuboid.')
    side2: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side2 of the cuboid.')
    side3: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side3 of the cuboid.')
    side4: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side4 of the cuboid.')
    side5: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side5 of the cuboid.')
    side6: CollectionProperty(  # type: ignore
        type=MCBLEND_UvMaskProperties,
        description='Collection of the filters for side6 of the cuboid.')

    def json(self) -> Dict[str, Any]:
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
