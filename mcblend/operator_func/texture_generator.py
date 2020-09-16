'''
Set of various image filters used for generating textures for models.
Uses numpy arrays with colors with colors encoded with values in range 0-1.
'''
from __future__ import annotations


import numpy as np
from itertools import repeat, cycle, accumulate, tee
from typing import Tuple, Iterable, NamedTuple, List, Optional, Dict, Sequence
from abc import ABC, abstractmethod
from enum import Enum


class UvMaskTypes(Enum):
    COLOR_PALLETTE_MASK='Color Pallette Mask'
    GRADIENT_MASK='Gradient Mask'
    ELIPSE_MASK='Elipse Mask'
    RECTANGLE_MASK='Rectangle Mask'
    STRIPES_MASK='Stripes Mask'
    RANDOM_MASK='Random Mask'
    COLOR_MASK='Color Mask'
    MIX_MASK='Mix Mask'

def list_mask_types_as_blender_enum(self, context):
    '''
    Passing list itself to some operators/panels didn't work.
    This function is a workaround that uses alternative definition for
    EnumProperty.

    https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
    '''
    return [(i.value, i.value, i.value) for i in UvMaskTypes]

class MixMaskMode(Enum):
    mean='mean'
    min='min'
    max='max'
    median='median'

def list_mix_mask_modes_as_blender_enum(self, context):
    '''
    Returns list of tuples for creating EnumProperties with MixMaskMode enum.
    '''
    return [(i.value, i.value, i.value) for i in MixMaskMode]

class Mask(ABC):
    '''
    Abstract class parent of all Filters.
    '''
    @abstractmethod
    def apply(self, image: np.ndarray):
        '''
        Applies the image to the image.
        '''
        pass


class Color(NamedTuple):
    '''
    Color palette color.
    '''
    r: float
    g: float
    b: float

    @staticmethod
    def FromHex(color: str):
        if len(color) != 6:
            raise Exception(
                'The color should be passed as 6 digit a hex number with '
                'format "rrggbb"'
            )
        return Color(
            int(color[:2], 16)/255.0,
            int(color[2:4], 16)/255.0,
            int(color[4:], 16)/255.0
        )

class ColorPalletteMask(Mask):
    def __init__(
            self, colors: List[Color], *,
            interpolate: bool = False,
            normalize: bool = False):
        self.colors = colors
        self.interpolate = interpolate
        self.normalize = normalize

    def apply(self, image: np.ndarray):
        '''
        Applies the image to the image.
        '''
        
        # xp and fp for np.interp
        if self.interpolate:
            fp_r = [c.r for c in self.colors]
            fp_g = [c.g for c in self.colors]
            fp_b = [c.b for c in self.colors]
            xp = np.array([i for i in range(len(self.colors))])
            xp = xp/(len(self.colors)-1)
        else:
            def repeated_list(iterable):
                for i in iterable:
                    yield i
                    yield i
            fp_r = [c.r for c in repeated_list(self.colors)]
            fp_g = [c.g for c in repeated_list(self.colors)]
            fp_b = [c.b for c in repeated_list(self.colors)]
            xp = np.array([i for i in range(len(self.colors))])
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
    A mask which can return a matrix which can be multiplied
    by the image to get the result of applying the maks.
    '''
    def apply(self, image: np.ndarray):
        mask = self.get_mask(image)
        image[:,:,:] = image*mask

    @abstractmethod
    def get_mask(self, image: np.array) -> np.array:
        '''
        Returns 2D matrix with the filter array
        '''
        pass

class Stripe(NamedTuple):
    width: float
    strength: float

class TwoPointSurfaceMask(MultiplicativeMask):
    def __init__(
            self, p1: Tuple[float, float],
            p2: Tuple[float, float], *,
            relative_boundries: bool=True):
        self.p1 = p1
        self.p2 = p2
        self.relative_boundries = relative_boundries

    def get_surface_properties(
            self, image: np.ndarray) -> Tuple[int, int, int, int, int, int]:
        w, h, _ = image.shape
        wh = np.array([w, h])

        # Get highlighted area indices
        if self.relative_boundries:
            p1 = np.array(
                np.array(self.p1)*wh, dtype=int)
            p2 = np.array(
                np.array(self.p2)*wh, dtype=int)
        else:
            p1 = np.array(
                self.p1, dtype=int)
            p2 = np.array(
                self.p2, dtype=int)
        u1, v1 = np.sort(p1%wh)
        u2, v2 = np.sort(p2%wh)
        u1, u2 = min(u1, u2), max(u1, u2)
        v1, v2 = min(v1, v2), max(v1, v2)
        return w, h, u1, u2, v1, v2

class GradientMask(TwoPointSurfaceMask):
    def __init__(
            self, p1: Tuple[float, float],
            p2: Tuple[float, float], *,
            stripes: Iterable[Stripe]=(
                Stripe(0.0, 0.0),
                Stripe(1.0, 1.0)
            ),
            relative_boundries: bool=True,
            expotent: float=1.0):
        super().__init__(
            p1, p2, relative_boundries=relative_boundries)
        
        self.stripe_strength: List[float] = []
        stripe_width = []
        for i in stripes:
            if i.width < 0:
                raise Exception(
                    'All stripe width must be greater or equal 0')
            stripe_width.append(i.width)
            self.stripe_strength.append(i.strength)
        self.stripe_width = np.array(stripe_width)/np.sum(stripe_width)
        self.expotent=expotent

    def get_mask(self, image):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(image)
        def split_complex(c):
            return (c.real, c.imag)
        a = np.array((u1, v1))
        b = np.array((u2, v2))
        # Rotate b around a 90 degrees
        b_prime = np.array(split_complex(complex(*b-a)*1j))+a

        # Get the line that connects a and b_prime
        if a[0] == b[0]:
            abc = np.array([1, 0, -a[0]])
        else:
            slope = (a[1]-b_prime[1])/(a[0]-b_prime[0])
            # Point slope form: (y-b[1])=slope*(x-b[0])
            # Standard form parameters: 0 = A*x + B*y + C
            abc = np.array([slope, -1, -slope*b_prime[0] + b_prime[1]])

        crds = np.indices((w, h), dtype=float)
        # Add one more dimesnion for C (assign "1" for every pixel)
        crds = np.stack([crds[0], crds[1], np.ones((w, h))], axis=2)

        # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
        mask = np.abs(
            np.sum(abc*crds, axis=2))/((np.sum(abc[:2]**2))**0.5
        )
        interp_len = np.linalg.norm(b-a)

        xp = list(accumulate(self.stripe_width*interp_len))
        fp = self.stripe_strength
        mask = np.interp(
            mask, xp, fp)
        mask=mask**self.expotent

        return mask[:, :, np.newaxis]

class ElipseMask(TwoPointSurfaceMask):
    def __init__(
            self, p1: Tuple[float, float],
            p2: Tuple[float, float], *,
            strength: Tuple[float, float]=(0.0, 1.0),
            relative_boundries: bool=True, hard_edge: bool=False,
            expotent: float=1.0):
        super().__init__(
            p1, p2, relative_boundries=relative_boundries)
        self.strength = strength
        self.hard_edge = hard_edge
        self.expotent=expotent

    def get_mask(self, image):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(image)

        img = np.ones((w, h, 3), dtype=np.float)
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

        mask[inside] = self.strength[1]

        if self.hard_edge:
            mask[outside] = self.strength[0]
        else:
            mask = np.interp(mask,
                [np.min(mask[outside]), np.max(mask[outside])],
                self.strength
            )
        mask=mask**self.expotent
        return mask[:, :, np.newaxis]

class RectangleMask(TwoPointSurfaceMask):
    def __init__(
            self, p1: Tuple[float, float],
            p2: Tuple[float, float], *,
            strength: Tuple[float, float]=(0.0, 1.0),
            relative_boundries: bool=True,
            hard_edge: bool=False,
            expotent: float=1.0):
        super().__init__(
            p1, p2, relative_boundries=relative_boundries)
        self.strength = strength
        self.expotent = expotent
        self.hard_edge = hard_edge

    def get_mask(self, image: np.array):
        w, h, u1, u2, v1, v2 = self.get_surface_properties(image)

        # Create basic mask array
        mask = np.zeros((w, h))

        if self.hard_edge:
            mask[:,:] = self.strength[0]
            mask[u1:u2, v1:v2] = self.strength[1]
            return mask[:, :, np.newaxis]
        # Else:
        # Set values of 9 segments
        # Left top
        segment_shape = mask[:u1,:v1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), np.fliplr(idx2)])
        mask[:u1,:v1] = np.linalg.norm(dist, axis=0)
        # Top
        segment_shape = mask[:u1,v1:v2].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), np.zeros(segment_shape)])
        mask[:u1,v1:v2] = np.linalg.norm(dist, axis=0)
        # Right top
        segment_shape = mask[:u1,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.flipud(idx1), idx2])
        mask[:u1,v2:] = np.linalg.norm(dist, axis=0)
        # # Left mid
        segment_shape = mask[u1:u2,:v1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.zeros(segment_shape), np.fliplr(idx2)])
        mask[u1:u2,:v1] = np.linalg.norm(dist, axis=0)
        # # Mid
        # # Alread filled with zeros
        # Right mid
        segment_shape = mask[u1:u2,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([np.zeros(segment_shape), idx2])
        mask[u1:u2,v2:] = np.linalg.norm(dist, axis=0)
        # Left bottom
        segment_shape = mask[u2:,:v1].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, np.fliplr(idx2)])
        mask[u2:,:v1] = np.linalg.norm(dist, axis=0)
        # Bottom
        segment_shape = mask[u2:,v1:v2].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, np.zeros(segment_shape)])
        mask[u2:,v1:v2] = np.linalg.norm(dist, axis=0)
        # Right bottom
        segment_shape = mask[u2:,v2:].shape
        idx1, idx2 = np.indices(segment_shape)
        dist = np.array([idx1, idx2])
        mask[u2:,v2:] = np.linalg.norm(dist, axis=0)

        mask = np.interp(mask, (mask.min(), mask.max()), self.strength)
        mask = mask**self.expotent
        return mask[:, :, np.newaxis]

class StripesMask(MultiplicativeMask):
    def __init__(
            self, stripes: List[Stripe], *,
            horizontal: bool=True,
            relative_boundries: bool=True):
        self.stripe_width: List[float] = []
        self.stripe_strength: List[float] = []

        for i in stripes:
            if i.width <= 0:
                raise Exception('All stripe widths must be greater than 0')
            self.stripe_width.append(i.width)
            self.stripe_strength.append(i.strength)
        self.horizontal = horizontal
        self.relative_boundries = relative_boundries
    
    def get_mask(self, image: np.array) -> np.array:
        w, h, _ = image.shape
        mask = np.ones((w, h))

        stripe_width = np.array(self.stripe_width)
        if self.relative_boundries:
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
    def __init__(
            self, *, strength: Tuple[float, float]=(0.0, 1.0),
            expotent: float=1.0, seed: Optional[int]=None):
        self.strength = strength
        self.expotent = expotent
        self.seed = seed

    def get_mask(self, image):
        # Get the shape of the image
        w, h, _ = image.shape
        np.random.seed(self.seed)
        mask = np.random.rand(w, h)
        mask = np.interp(mask, (0.0, 1.0), self.strength)
        mask = mask**self.expotent
        return mask[:,:,np.newaxis]

class ColorMask(MultiplicativeMask):
    def __init__(self, color: Tuple[float, float, float]):
        self.r, self.g, self.b = color

    def get_mask(self, image):
        # Get the shape of the image
        w, h, _ = image.shape
        mask = np.zeros((w, h, 3))
        mask[:,:,0] = self.r
        mask[:,:,1] = self.g
        mask[:,:,2] = self.b
        return mask[:,:,:]

class MixMask(MultiplicativeMask):
    def __init__(
            self, masks: Iterable[MultiplicativeMask], *,
            strength: Tuple[float, float]=(0.0, 1.0),
            expotent: float=1.0, mode='mean'):
        self.strength = strength
        self.expotent = expotent
        self.masks = masks
        self.mode = mode

    def get_mask(self, image):
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
        mask_arrays = []
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
            raise Exception(f"Unknown mix mode! {self.mode}")

        mask = np.interp(mask, (0.0, 1.0), self.strength)
        mask = mask**self.expotent
        return mask


def _get_stripe_from_gui(stripe) -> Stripe:
    '''
    Returns Stripe object from definition created with the GUI.
    (OBJECT_NusiqMcblendStripeProperties)
    '''
    return Stripe(stripe.width, stripe.strength)

def _get_color_from_gui_color(color) -> Color:
    '''
    Returns Color object from definition created with the GUI.
    (OBJECT_NusiqMcblendColorProperties)
    '''
    # convert linear rgb to srgb
    rgb = np.array(color.color)
    selector = rgb < 0.0031308
    rgb[selector] *= 12.92
    rgb[selector == False] = 1.055 * rgb[selector == False]**(1/2.4) - 0.055
    return Color(*rgb)

def get_masks_from_side(side) -> Sequence[Mask]:
    '''
    Returns tuple of Masks from one masks side definition creater in GUI.
    '''

    def _get_masks_from_side(side: Iterable, n_steps: int) -> Sequence[Mask]:
        result: List[Mask] = []
        mask: Mask
        # n_steps limits maximal number of consumed items
        # side is an iterator shared by all nested iterations
        for _, s_props in zip(range(n_steps), side):
            if s_props.mask_type == UvMaskTypes.COLOR_PALLETTE_MASK.value:
                mask = ColorPalletteMask(
                    [_get_color_from_gui_color(c) for c in s_props.colors],
                    interpolate=s_props.interpolate, normalize=s_props.normalize)
            if s_props.mask_type == UvMaskTypes.GRADIENT_MASK.value:
                mask = GradientMask(
                    tuple(s_props.p1), tuple(s_props.p2),  # type: ignore
                    stripes=[Stripe(s.width, s.strength) for s in s_props.stripes],
                    relative_boundries=s_props.relative_boundries,
                    expotent=s_props.expotent)
            if s_props.mask_type == UvMaskTypes.ELIPSE_MASK.value:
                mask = ElipseMask(
                    tuple(s_props.p1), tuple(s_props.p2),  # type: ignore
                    strength=tuple(s_props.strength),  #type: ignore
                    relative_boundries=s_props.relative_boundries,
                    hard_edge=s_props.hard_edge, expotent=s_props.expotent)
            if s_props.mask_type == UvMaskTypes.RECTANGLE_MASK.value:
                mask = RectangleMask(
                    tuple(s_props.p1), tuple(s_props.p2),  # type: ignore
                    strength=tuple(s_props.strength),  #type: ignore
                    relative_boundries=s_props.relative_boundries,
                    hard_edge=s_props.hard_edge, expotent=s_props.expotent)
            if s_props.mask_type == UvMaskTypes.STRIPES_MASK.value:
                mask = StripesMask(
                    [Stripe(s.width, s.strength) for s in s_props.stripes],
                    horizontal=s_props.horizontal,
                    relative_boundries=s_props.relative_boundries)
            if s_props.mask_type == UvMaskTypes.RANDOM_MASK.value:
                seed: Optional[int] = None
                if s_props.use_seed:
                    seed = s_props.seed
                mask = RandomMask(
                    strength=tuple(s_props.strength),  # type: ignore
                    expotent=s_props.expotent, seed=seed)
            if s_props.mask_type == UvMaskTypes.COLOR_MASK.value:
                mask = ColorMask(_get_color_from_gui_color(s_props.color))
            if s_props.mask_type == UvMaskTypes.MIX_MASK.value:
                mask = MixMask(
                    masks=[  # Non multiplicative masks are ignored
                        submask for submask in
                        _get_masks_from_side(side, n_steps=s_props.children)
                        if isinstance(submask, MultiplicativeMask)
                    ], strength=s_props.strength, expotent=s_props.expotent,
                    mode=s_props.mode)
            result.append(mask)
        return tuple(result)

    return  _get_masks_from_side(iter(side), n_steps=len(side))
