'''
Common functions and objects used during exporting model and camera animations.
'''
from __future__ import annotations

from typing import NamedTuple, Dict, Optional, List, Tuple, cast, Any, Iterable
import math # pyright: ignore[reportShadowedImports]
import re
import bisect
from enum import Enum
from dataclasses import dataclass, field
from itertools import tee, islice  # pyright: ignore[reportShadowedImports]
from decimal import Decimal

import bpy
from bpy.types import Action, ActionSlot, Context, Object

import numpy as np

from .json_tools import get_vect_json
from .frame_range import get_frames_from_frame_ranges
from .common import (
    AnimationLoopType, MINECRAFT_SCALE_FACTOR, MCObjType, McblendObjectGroup,
    ANIMATION_TIMESTAMP_PRECISION, NumpyTable, McblendObject
)
from bpy_extras import anim_utils

class InterpolationMode(Enum):
    '''
    Enum with the interpolation modes of the keyframes.
    '''
    STEP = 0
    LINEAR = 1
    SMOOTH = 2
    AUTO = 3  # Use the interpolation mode detected from Blender keyframes

    # Must be comparable for bisect
    def __lt__(self, other: InterpolationMode) -> bool:
        return self.value < other.value

class TransformationType(Enum):
    '''
    Enum with the types of the transformations.
    '''
    LOCATION = 0
    ROTATION = 1
    SCALE = 2

    # Must be comparable for 'sorted' function
    def __lt__(self, other: TransformationType) -> bool:
        return self.value < other.value

class Timeline:
    '''
    Represents a timeline of a single bone, with the keyframe numbers and
    the corresponding interpolation modes - "linear" or "step".
    '''
    def __init__(self):
        self._keyframes: List[tuple[float,InterpolationMode]] = []

    def add_keyframe(self, keyframe: float, mode: InterpolationMode):
        '''
        Adds a keyframe to the timeline.

        :param keyframe: the keyframe number.
        :param mode: the interpolation mode of the keyframe.
        '''
        bisect.insort(self._keyframes, (keyframe, mode))

    def get_state(self, timestamp: float) ->InterpolationMode:
        '''
        Returns the interpolation mode of the keyframe at the given timestamp.

        :param timestamp: the timestamp of the keyframe.
        :returns: the interpolation mode of the keyframe.
        '''
        if len(self._keyframes) == 0:
            return InterpolationMode.LINEAR
        # We are using 'bisect_left' here. Note that bisect_right would give
        # the same result in this case, because we're compering:
        # (timestamp, mode) with (timestamp,). When comparing tuples in Python
        # and the first elements are equal, if one tuple is shorter, it's
        # considered smaller.
        index = bisect.bisect_left(
            self._keyframes, (timestamp,))
        # Prevent index out of bounds
        index = min(index, len(self._keyframes) - 1)
        return self._keyframes[index][1]

def pick_closest_rotation(
        base: NumpyTable, close_to: NumpyTable,
        original_rotation: Optional[NumpyTable] = None
    ) -> NumpyTable:
    '''
    Takes two arrays with euler rotations in degrees. Looks for rotations
    that result in same orientation as the base rotation. Picks the vector
    which is the closest to the :code:`close_to` using euclidean distance.

    *The :code:`original_rotation` is added specifically to fix some issues with
    bones rotated before the animation. Issue #25 on Github describes the
    problem in detail.

    :base: NumpyTable: the base rotation. Function is looking for different
        representations of this orientation.
    :param close_to: target rotation. Function returns the result as close
        as possible to this vector.
    :param original_rotation: optional - the original rotation of the object
        before the start of the animation.
    :returns: another euler angle that represents the same rotation as the base
        rotation.
    '''
    if original_rotation is None:
        original_rotation = np.array([0.0, 0.0, 0.0])

    def _pick_closest_location(
            base: NumpyTable, close_to: NumpyTable
    ) -> Tuple[float, NumpyTable]:
        choice: NumpyTable = base
        distance = np.linalg.norm(choice - close_to)

        for i in range(3):  # Adds removes 360 to all 3 axis (picks the best)
            arr = np.zeros(3)
            arr[i] = 360
            while choice[i] < close_to[i]:
                new_choice = choice + arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:  # type: ignore
                    break
                distance, choice = new_distance, new_choice
            while choice[i] > close_to[i]:
                new_choice = choice - arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:  # type: ignore
                    break
                distance, choice = new_distance, new_choice
        return cast(float, distance), choice

    distance1, choice1 = _pick_closest_location(base, close_to)
    distance2, choice2 = _pick_closest_location(  # Counterintuitive but works
        (
            base +
            np.array([180, 180 + original_rotation[1] * 2, 180])) *
            np.array([1, -1, 1]
        ),
        close_to
    )
    if distance2 < distance1:
        return choice2
    return choice1

def frame_to_t(frame: float, fps: float) -> str:
    '''
    Converts frame number to time in seconds. Assumes that the frame 1 is
    at time 0. Rounds the result to the precision set by the
    :code:`ANIMATION_TIMESTAMP_PRECISION` constant. The result is returned
    as a string with a normalized form of a decimal number.
    '''
    timestamp = Decimal((frame-1) / fps)
    return str(round(timestamp, ANIMATION_TIMESTAMP_PRECISION).normalize())