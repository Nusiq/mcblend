# pylint: disable=invalid-name
'''
Set of various image filters used for generating textures for models.
Uses numpy arrays with colors with colors encoded with values in range 0-1.
'''
from __future__ import annotations

from itertools import cycle, accumulate
from typing import (
    Tuple, Iterable, NamedTuple, List, Optional, Sequence, TYPE_CHECKING, Any)
from abc import ABC, abstractmethod
from enum import Enum
from bpy.types import Context

import numpy as np

from .extra_types import Vector2d, Vector3d

if TYPE_CHECKING:
    from .common import NumpyTable
    from ..uv_data import MCBLEND_UvMaskProperties, MCBLEND_ColorProperties
    from .pyi_types import CollectionProperty

class UvMaskTypes(Enum):
    '''
    UvMaskTypes are used for selecting one of the avaliable masks types in
    dropdown lists.
    '''
    COLOR_PALLETTE_MASK='Color Palette Mask'
    GRADIENT_MASK='Gradient Mask'
    ELLIPSE_MASK='Ellipse Mask'
    RECTANGLE_MASK='Rectangle Mask'
    STRIPES_MASK='Stripes Mask'
    RANDOM_MASK='Random Mask'
    COLOR_MASK='Color Mask'
    MIX_MASK='Mix Mask'

def list_mask_types_as_blender_enum(self: Any, context: Context):
    '''
    Passing list itself to some operators/panels didn't work.
    This function is a workaround that uses alternative definition for
    EnumProperty.

    https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
    '''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in UvMaskTypes]

class MixMaskMode(Enum):
    '''MixMaskMode is used to define the behavior of the MixMask'''
    mean='mean'
    min='min'
    max='max'
    median='median'

def list_mix_mask_modes_as_blender_enum(self: Any, context: Context):
    '''
    Returns list of tuples for creating EnumProperties with MixMaskMode enum.
    '''
    # pylint: disable=unused-argument
    return [(i.value, i.value, i.value) for i in MixMaskMode]

class Mask(ABC):
    '''Abstract class, parent of all Filters.'''
    @abstractmethod
    def apply(self, image: NumpyTable):
        '''
        Applies the image to the image.

        :param image: The image filtered by the mask.
        '''


class Color(NamedTuple):
    '''Color palette color.'''
    r: float
    g: float
    b: float

    @staticmethod
    def create_from_hex(color: str):
        '''Creates color object from hex string e.g. "ffffff"'''
        if len(color) != 6:
            raise ValueError(
                'The color should be passed as 6 digit a hex number with '
                'format "rrggbb"'
            )
        return Color(
            int(color[:2], 16)/255.0,
            int(color[2:4], 16)/255.0,
            int(color[4:], 16)/255.0
        )

class ColorPaletteMask(Mask):
    '''
    ColorPaletteMask is a mask that maps values (0 to 1) from the image to
    colors from the color palette.
    '''
    def __init__(
            self, colors: List[Color], *,
            interpolate: bool = False,
            normalize: bool = False):
        self.colors = colors
        self.interpolate = interpolate
        self.normalize = normalize

    def apply(self, image: NumpyTable):
        # xp and fp for np.interp
        if self.interpolate:
            fp_r = [c.r for c in self.colors]
            fp_g = [c.g for c in self.colors]
            fp_b = [c.b for c in self.colors]
            xp = np.array(list(range(len(self.colors))))
            xp = xp/(len(self.colors)-1)
        else:
            def repeated_list(iterable: Iterable[Any]) -> Iterable[Any]:
                for i in iterable:
                    yield i
                    yield i
            fp_r = [c.r for c in repeated_list(self.colors)]
            fp_g = [c.g for c in repeated_list(self.colors)]
            fp_b = [c.b for c in repeated_list(self.colors)]
            xp = np.array(list(range(len(self.colors))))
            xp = xp/len(self.colors)
            unpacked_xp = [0.0]
            for xpi in repeated_list(xp[1:]):
                unpacked_xp.append(xpi)
            unpacked_xp.append(1.0)
            xp = np.array(unpacked_xp)

        # Input image must be converted to grayscale
        gray = np.mean(image, axis=2)
        if self.normalize:
            gray = np.interp(
                gray, [np.min(gray), np.max(gray)], [0, 1]
            )
        image[:,:,:] = np.stack([gray for _ in range(3)], axis=2)
        # Apply filters
        image[:,:,0] = np.interp(image[:,:,0], xp, fp_r)
        image[:,:,1] = np.interp(image[:,:,1], xp, fp_g)
        image[:,:,2] = np.interp(image[:,:,2], xp, fp_b)


class MultiplicativeMask(Mask):
    '''
    A mask which can return a matrix which can be multiplied element-wise
    by the image matrix to get the result of applying the mask.
    '''
    def apply(self, image: NumpyTable):
        mask = self.get_mask(image)
        image[:,:,:] = image*mask

    @abstractmethod
    def get_mask(self, image: NumpyTable) -> NumpyTable:
        '''Returns 2D matrix with the filter array.'''


class DummyMask(MultiplicativeMask):
    '''
    A multiplicative mask that always return a white image.
    '''
    def get_mask(self, image: NumpyTable):
        w, h, _ = image.shape
        return np.ones((w, h))[:,:, np.newaxis]


class Stripe(NamedTuple):
    '''
    Stripes are used in StripesMask and ColorPaletteMask mask in a collection
    to define width and the value of the items that compose the mask.
    '''
    width: float
    strength: float

class TwoPointSurfaceMask(MultiplicativeMask):
    '''
    Abstract class for masks that require two points on the textures to define
    which area should be affected.
    '''
    def __init__(
            self, p1: Vector2d,
            p2: Vector2d, *,
            relative_boundaries: bool=True):
        self.p1 = p1
        self.p2 = p2
        self.relative_boundaries = relative_boundaries

    def get_surface_properties(
            self, image: NumpyTable,
            sort_points: bool=False) -> Tuple[int, int, int, int, int, int]:
        '''
        Uses points passed in the constructor and the image to return the
        coordinates of the points that define which area of the texture
        should be affected by the mask.

        :param sort_points: whether the returned points should be sorted by the
            coordinates (minx, miny), (maxx, maxy)/
        '''
        w, h, _ = image.shape
        wh = np.array([w, h])
        # Get highlighted area indices
        if self.relative_boundaries:
            # The values from relative boundaries should always be between
            # 0 and 1.

            # The result values are clipped to range 0 to size-1
            p1 = np.clip(
                np.array(np.array(self.p1)*wh, dtype=int),
                (0, 0), (max(0, w-1), max(0, h-1))
            )
            p2 = np.clip(
                np.array(np.array(self.p2)*wh, dtype=int),
                (0, 0), (max(0, w-1), max(0, h-1))
            )
        else:
            p1 = np.array(
                self.p1, dtype=int)
            p2 = np.array(
                self.p2, dtype=int)
        u1, v1 = p1%wh
        u2, v2 = p2%wh
        if sort_points:
            u1, u2 = min(u1, u2), max(u1, u2)
            v1, v2 = min(v1, v2), max(v1, v2)
        return w, h, u1, u2, v1, v2

class GradientMask(TwoPointSurfaceMask):
    '''
    Uses stripes with different widths and strenghts to create a grayscale
    gradient between two points.
    '''
    def __init__(
            self, p1: Vector2d,
            p2: Vector2d, *,
            stripes: Iterable[Stripe]=(
                Stripe(0.0, 0.0),
                Stripe(1.0, 1.0)
            ),
            relative_boundaries: bool=True,
            expotent: float=1.0):
        super().__init__(p1, p2, relative_boundaries=relative_boundaries)
        self.stripe_strength: List[float] = []
        stripe_width: list[float] = []
        for i in stripes:
            if i.width < 0:
                raise ValueError(
                    'All stripe width must be greater or equal 0')
            stripe_width.append(i.width)
            self.stripe_strength.append(i.strength)
        self.stripe_width = np.array(stripe_width)/np.sum(stripe_width)
        self.expotent=expotent

    def get_mask(self, image: NumpyTable):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(
            image, sort_points=False)
        def split_complex(c: complex):
            return (c.real, c.imag)

        a = np.array((u1, v1))
        b = np.array((u2, v2))
        # Rotate b around a 90 degrees
        b_prime = np.array(split_complex(complex(*b-a)*1j))+a
        # Get the line that connects a and b_prime
        if a[0] == b_prime[0]:
            abc = np.array([1, 0, -a[0]])
        else:
            slope = (a[1]-b_prime[1])/(a[0]-b_prime[0])
            # Point slope form: (y-b[1])=slope*(x-b[0])
            # Standard form parameters: 0 = A*x + B*y + C
            abc = np.array([slope, -1, -slope*b_prime[0] + b_prime[1]])

        crds = np.indices((w, h), dtype=float)
        # Add one more dimension for C (assign "1" for every pixel)
        crds = np.stack([crds[0], crds[1], np.ones((w, h))], axis=2)

        # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        mask: NumpyTable = np.abs(  # type: ignore
            np.sum(abc*crds, axis=2))/((np.sum(abc[:2]**2))**0.5  # type: ignore
        )
        interp_len = np.linalg.norm(b-a)

        xp = list(accumulate(self.stripe_width*interp_len))
        fp = self.stripe_strength
        mask = np.interp(mask, xp, fp)  # type: ignore
        mask=mask**self.expotent

        return mask[:, :, np.newaxis]

class EllipseMask(TwoPointSurfaceMask):
    '''
    Creates ellipse in-between two points.
    '''
    def __init__(
            self, p1: Vector2d,
            p2: Vector2d, *,
            strength: Vector2d=(0.0, 1.0),
            relative_boundaries: bool=True, hard_edge: bool=False,
            expotent: float=1.0):
        super().__init__(
            p1, p2, relative_boundaries=relative_boundaries)
        self.strength = strength
        self.hard_edge = hard_edge
        self.expotent=expotent

    def get_mask(self, image: NumpyTable):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(image)
        # img = np.ones((w, h, 3), dtype=np.float)
        a = (u2-u1)/2
        b = (v2-v1)/2
        a = a if a >= 1 else 1
        b = b if b >= 1 else 1
        offset_x = np.mean([u1, u2])
        offset_y = np.mean([v1, v2])
        crds = np.indices((w, h), dtype=float)+0.5
        crds[0] -= offset_x
        crds[1] -= offset_y
        mask = crds[0]**2/a**2 + crds[1]**2/b**2
        inside = mask <= 1
        outside = mask > 1


        if self.hard_edge:
            mask[outside] = self.strength[1]
            mask[inside] = self.strength[0]
        else:
            mask[inside] = self.strength[1]
            try:
                mask = np.interp(mask,
                    [np.min(mask[outside]), np.max(mask[outside])],
                    self.strength
                )
            except ValueError:  # when mask[outside] or is empty
                pass
        mask=mask**self.expotent
        return mask[:, :, np.newaxis]

class RectangleMask(TwoPointSurfaceMask):
    '''
    Creates a rectangle in-between two points.
    '''
    def __init__(
            self, p1: Vector2d,
            p2: Vector2d, *,
            strength: Vector2d=(0.0, 1.0),
            relative_boundaries: bool=True,
            hard_edge: bool=False,
            expotent: float=1.0):
        super().__init__(
            p1, p2, relative_boundaries=relative_boundaries)
        self.strength = strength
        self.expotent = expotent
        self.hard_edge = hard_edge

    def get_mask(self, image: NumpyTable):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(image)

        # Create basic mask array
        mask = np.zeros((w, h))

        if self.hard_edge or (u1 == 0 and v1 == 0 and w == u2+1 and h == v2+1):
            mask[:,:] = self.strength[1]
            mask[u1:u2+1, v1:v2+1] = self.strength[0]
            return mask[:, :, np.newaxis]
        # Else:
        # Set values of 9 segments
        # Left top
        segment_shape = mask[:u1+1,:v1+1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), np.fliplr(idx2)])
        mask[:u1+1,:v1+1] = np.linalg.norm(dist, axis=0)
        # Top
        segment_shape = mask[:u1+1,v1:v2+1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), np.zeros(segment_shape)])
        mask[:u1+1,v1:v2+1] = np.linalg.norm(dist, axis=0)
        # Right top
        segment_shape = mask[:u1+1,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), idx2])
        mask[:u1+1,v2:] = np.linalg.norm(dist, axis=0)
        # # Left mid
        segment_shape = mask[u1:u2+1,:v1+1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.zeros(segment_shape), np.fliplr(idx2)])
        mask[u1:u2+1,:v1+1] = np.linalg.norm(dist, axis=0)
        # # Mid
        # # Already filled with zeros
        # Right mid
        segment_shape = mask[u1:u2+1,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.zeros(segment_shape), idx2])
        mask[u1:u2+1,v2:] = np.linalg.norm(dist, axis=0)
        # Left bottom
        segment_shape = mask[u2:,:v1+1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, np.fliplr(idx2)])
        mask[u2:,:v1+1] = np.linalg.norm(dist, axis=0)
        # Bottom
        segment_shape = mask[u2:,v1:v2+1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, np.zeros(segment_shape)])
        mask[u2:,v1:v2+1] = np.linalg.norm(dist, axis=0)
        # Right bottom
        segment_shape = mask[u2:,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, idx2])
        mask[u2:,v2:] = np.linalg.norm(dist, axis=0)

        mask = np.interp(mask, (mask.min(), mask.max()), self.strength)
        mask = mask**self.expotent
        return mask[:, :, np.newaxis]

class StripesMask(MultiplicativeMask):
    '''
    Creates horizontal or vertical grayscale stripes.
    '''
    def __init__(
            self, stripes: List[Stripe], *,
            horizontal: bool=True,
            relative_boundaries: bool=True):
        self.stripe_width: List[float] = []
        self.stripe_strength: List[float] = []

        for i in stripes:
            if i.width <= 0:
                raise ValueError('All stripe widths must be greater than 0')
            self.stripe_width.append(i.width)
            self.stripe_strength.append(i.strength)
        self.horizontal = horizontal
        self.relative_boundaries = relative_boundaries

    def get_mask(self, image: NumpyTable) -> NumpyTable:
        w, h, _ = image.shape
        mask = np.ones((w, h))

        stripe_width = np.array(self.stripe_width)
        if self.relative_boundaries:
            stripe_width *= w if self.horizontal else h

        # One pixel is minimal stripe width
        stripe_width[stripe_width < 1] = 1

        stripes_limit = w if self.horizontal else h
        prev_index = 0
        # infinite loop
        for i, strength in zip(
            accumulate(cycle(stripe_width)),
            cycle(self.stripe_strength)
        ):
            curr_index = int(i)
            if self.horizontal:
                mask[prev_index:curr_index,:] = strength
            else:
                mask[:, prev_index:curr_index] = strength
            prev_index = curr_index
            if curr_index >= stripes_limit:
                break
        return mask[:, :, np.newaxis]

class RandomMask(MultiplicativeMask):
    '''
    Creates randomly colored grayscale pixels.
    '''
    def __init__(
            self, *, strength: Vector2d=(0.0, 1.0),
            expotent: float=1.0, seed: Optional[int]=None):
        self.strength = strength
        self.expotent = expotent
        self.seed = seed

    def get_mask(self, image: NumpyTable):
        # Get the shape of the image
        w, h, _ = image.shape
        np.random.seed(self.seed)
        mask = np.random.rand(w, h)
        mask = np.interp(mask, (0.0, 1.0), self.strength)
        mask = mask**self.expotent
        return mask[:,:,np.newaxis]

class ColorMask(MultiplicativeMask):
    '''
    Fileters the image with a color.
    '''
    def __init__(self, color: Vector3d):
        self.r, self.g, self.b = color

    def get_mask(self, image: NumpyTable):
        # Get the shape of the image
        w, h, _ = image.shape
        mask = np.zeros((w, h, 3))
        mask[:,:,0] = self.r
        mask[:,:,1] = self.g
        mask[:,:,2] = self.b
        return mask[:,:,:]

class MixMask(MultiplicativeMask):
    '''
    Mixes multiple masks by calculating their pixelwise mean
    min, max or median values.
    '''
    def __init__(
            self, masks: list[MultiplicativeMask], *,
            strength: Vector2d=(0.0, 1.0),
            expotent: float=1.0,
            mode: str='mean'):
        self.strength = strength
        self.expotent = expotent
        self.masks = masks
        self.mode = mode

    def get_mask(self, image: NumpyTable):
        # Get the shape of the image
        w, h, _ = image.shape

        # If there is no masks on the list than return blank mask
        if len(self.masks) == 0:
            mask = np.ones((w, h))
            return mask[:,:,np.newaxis]

        is_rgb = False
        for m in self.masks:
            if len(m.get_mask(image).shape) == 3:
                is_rgb = True
                break
        mask_arrays: List[NumpyTable] = []
        for m in self.masks:
            mask_array = m.get_mask(image)
            if is_rgb:
                if len(mask_array.shape) == 2:  # Convert grayscale to RGB
                    mask_array = np.stack(
                        [mask_array for _ in range(3)], axis=2)
            mask_arrays.append(mask_array)

        if self.mode == 'mean':
            mask = np.mean(mask_arrays, axis=0)
        elif self.mode == 'min':
            mask = np.min(mask_arrays, axis=0)
        elif self.mode == 'max':
            mask = np.max(mask_arrays, axis=0)
        elif self.mode == 'median':
            mask = np.median(mask_arrays, axis=0)
        else:
            raise ValueError(f"Unknown mix mode! {self.mode}")

        mask = np.interp(mask, (0.0, 1.0), self.strength)
        mask = mask**self.expotent
        return mask

def _get_color_from_gui_color(color: MCBLEND_ColorProperties) -> Color:
    '''
    Returns Color object from definition created with the GUI.
    (MCBLEND_ColorProperties)
    '''
    #pylint: disable=singleton-comparison
    # convert linear rgb to srgb
    rgb: NumpyTable = np.array(color.color)
    selector = rgb < 0.0031308
    rgb[selector] *= 12.92
    rgb[selector == False] = 1.055 * rgb[selector == False]**(1/2.4) - 0.055
    return Color(*rgb)

def get_masks_from_side(side: CollectionProperty[MCBLEND_UvMaskProperties]) -> Sequence[Mask]:
    '''
    Returns tuple of Masks from one masks side definition created in GUI.
    '''

    def _get_masks_from_side(
            side: Iterable[MCBLEND_UvMaskProperties],
            n_steps: int) -> Sequence[Mask]:
        result: List[Mask] = []
        mask: Mask
        # n_steps limits maximal number of consumed items
        # side is an iterator shared by all nested iterations
        for _, s_props in zip(range(n_steps), side):
            if s_props.mask_type == UvMaskTypes.COLOR_PALLETTE_MASK.value:
                mask = ColorPaletteMask(
                    [_get_color_from_gui_color(c) for c in s_props.colors],
                    interpolate=s_props.interpolate, normalize=s_props.normalize)
            elif s_props.mask_type == UvMaskTypes.GRADIENT_MASK.value:
                if s_props.relative_boundaries:
                    p1 = tuple(s_props.p1_relative)
                    p2 = tuple(s_props.p2_relative)
                else:
                    p1 = tuple(s_props.p1)
                    p2 = tuple(s_props.p2)
                mask = GradientMask(
                    p1, p2,  # type: ignore
                    # Gradient mask never uses relative with for stripes
                    stripes=[Stripe(s.width, s.strength) for s in s_props.stripes],
                    relative_boundaries=s_props.relative_boundaries,
                    expotent=s_props.expotent)
            elif s_props.mask_type == UvMaskTypes.ELLIPSE_MASK.value:
                if s_props.relative_boundaries:
                    p1 = tuple(s_props.p1_relative)
                    p2 = tuple(s_props.p2_relative)
                else:
                    p1 = tuple(s_props.p1)
                    p2 = tuple(s_props.p2)
                mask = EllipseMask(
                    p1, p2,  # type: ignore
                    strength=tuple(s_props.strength),  #type: ignore
                    relative_boundaries=s_props.relative_boundaries,
                    hard_edge=s_props.hard_edge, expotent=s_props.expotent)
            elif s_props.mask_type == UvMaskTypes.RECTANGLE_MASK.value:
                if s_props.relative_boundaries:
                    p1 = tuple(s_props.p1_relative)
                    p2 = tuple(s_props.p2_relative)
                else:
                    p1 = tuple(s_props.p1)
                    p2 = tuple(s_props.p2)
                mask = RectangleMask(
                    p1, p2,  # type: ignore
                    strength=tuple(s_props.strength),  #type: ignore
                    relative_boundaries=s_props.relative_boundaries,
                    hard_edge=s_props.hard_edge, expotent=s_props.expotent)
            elif s_props.mask_type == UvMaskTypes.STRIPES_MASK.value:
                if s_props.relative_boundaries:
                    stripes = [
                        Stripe(s.width_relative, s.strength)
                        for s in s_props.stripes]
                else:
                    stripes = [
                        Stripe(s.width, s.strength)
                        for s in s_props.stripes]
                mask = StripesMask(
                    stripes, horizontal=s_props.horizontal,
                    relative_boundaries=s_props.relative_boundaries)
            elif s_props.mask_type == UvMaskTypes.RANDOM_MASK.value:
                seed: Optional[int] = None
                if s_props.use_seed:
                    seed = s_props.seed
                mask = RandomMask(
                    strength=tuple(s_props.strength),  # type: ignore
                    expotent=s_props.expotent, seed=seed)
            elif s_props.mask_type == UvMaskTypes.COLOR_MASK.value:
                mask = ColorMask(_get_color_from_gui_color(s_props.color))
            elif s_props.mask_type == UvMaskTypes.MIX_MASK.value:
                mask = MixMask(
                    masks=[  # Non multiplicative masks are ignored
                        submask for submask in
                        _get_masks_from_side(side, n_steps=s_props.children)
                        if isinstance(submask, MultiplicativeMask)
                    ], strength=s_props.strength, expotent=s_props.expotent,
                    mode=s_props.mode)
            else:
                raise ValueError('Unknown mask type')
            if s_props.ui_hidden:
                result.append(DummyMask())
            else:
                result.append(mask)
        return tuple(result)

    return  _get_masks_from_side(iter(side), n_steps=len(side))
