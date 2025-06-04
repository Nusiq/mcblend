'''
Functions related to optimizing animations.
'''
from __future__ import annotations

from typing import Any, Generator, TypeGuard, Literal, Dict, Optional, List

timeline_type = Literal["rotation", "position", "scale"]


def walk_bone_timelines(animation_data: Dict[str, Any]) -> Generator[tuple[timeline_type, dict[str, Any]], None, None]:
    """
    Walk through all timelines in a single animation.

    :param animation_data: The animation data dictionary.
    :returns: Generator yielding tuples of (timeline_type, timeline).
    """
    if "bones" not in animation_data:
        return

    for bone in animation_data["bones"].values():
        if "rotation" in bone and isinstance(bone["rotation"], dict):
            yield "rotation", bone["rotation"]
        if "position" in bone and isinstance(bone["position"], dict):
            yield "position", bone["position"]
        if "scale" in bone and isinstance(bone["scale"], dict):
            yield "scale", bone["scale"]


def walk_timeline_keys(timeline: dict[str, Any]) -> Generator[str, None, None]:
    """
    Walk through all keys in a timeline, sorted by time.

    :param timeline: The timeline dictionary.
    :returns: Generator yielding keys sorted by time.
    """
    for k in sorted(timeline.keys(), key=lambda k: float(k)):
        yield k


def is_vector(v: Any) -> TypeGuard[list[int | float]]:
    """
    Check if a value is a vector (list of 3 numbers).

    :param v: The value to check.
    :returns: True if the value is a vector, False otherwise.
    """
    if not isinstance(v, list) or len(v) != 3:
        return False
    for i in v:
        if not isinstance(i, (int, float)):
            return False
    return True


def is_interpolation(
        prev_time: str, prev: Any,
        curr_time: str, curr: Any,
        next_time: str, next: Any,
        error_margin=0.05) -> bool:
    """
    Check if a keyframe can be interpolated from its neighbors within an error margin.

    :param prev_time: The time of the previous keyframe.
    :param prev: The value of the previous keyframe.
    :param curr_time: The time of the current keyframe.
    :param curr: The value of the current keyframe.
    :param next_time: The time of the next keyframe.
    :param next: The value of the next keyframe.
    :param error_margin: The maximum allowed error as a ratio of movement distance.
    :returns: True if the keyframe can be interpolated, False otherwise.
    """
    try:
        prev_time_number = float(prev_time)
        curr_time_number = float(curr_time)
        next_time_number = float(next_time)
    except:
        return False

    if not is_vector(prev) or not is_vector(curr) or not is_vector(next):
        return False

    prev_curr_duration = curr_time_number - prev_time_number
    prev_next_duration = next_time_number - prev_time_number

    # Calculate interpolation ratio based on time
    t_ratio = prev_curr_duration / prev_next_duration

    # Calculate alternative position at curr_time by interpolating between
    # prev and next with t_ratio
    alternative_curr = [
        prev[i] + t_ratio * (next[i] - prev[i])
        for i in range(3)
    ]

    # Calculate distance between actual and expected positions
    alternative_real_curr_distance = sum(
        (curr[i] - alternative_curr[i]) ** 2
        for i in range(3)
    ) ** 0.5

    # The distance from prev to next is used for scaling the error. We accept
    # more error if the overall movement is really big.
    prev_next_distance = sum((next[i] - prev[i]) ** 2 for i in range(3)) ** 0.5

    # Avoid division by zero
    if prev_next_distance < 0.00001:
        prev_next_distance = 0.00001

    # Normalized error
    deviation = alternative_real_curr_distance / prev_next_distance

    return deviation < error_margin


class AnimationOptimizer:
    """
    Class for optimizing animations by removing redundant keyframes.
    """
    def __init__(self, error_margin: float = 0.05, animation_name: Optional[str] = None):
        """
        Initialize the AnimationOptimizer with a specified error margin.

        :param error_margin: The maximum allowed error as a ratio (0-1).
        :param animation_name: If provided, only the specified animation will be optimized.
                              If None, all animations in the file will be optimized.
        """
        self.error_margin = error_margin
        self.animation_name = animation_name
        self.total_removed = {
            "rotation": 0,
            "position": 0,
            "scale": 0
        }

    def optimize_animation(self, animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize an animation by removing redundant keyframes.

        :param animation_data: The animation data dictionary (full animation file).
        :returns: The optimized animation data dictionary.
        """
        self.total_removed = {
            "rotation": 0,
            "position": 0,
            "scale": 0
        }

        # Create a copy to avoid modifying the original data
        result = animation_data.copy()

        # If no animations key or it's not a dictionary, return unmodified
        if "animations" not in result or not isinstance(result["animations"], dict):
            return result

        # Target specific animation if name is provided, otherwise optimize all
        if self.animation_name:
            anim_key = f"animation.{self.animation_name}"
            if anim_key in result["animations"]:
                anim_data = result["animations"][anim_key]
                self._optimize_single_animation(anim_data)
        else:
            # Optimize all animations
            for anim_key, anim_data in result["animations"].items():
                self._optimize_single_animation(anim_data)

        return result

    def _optimize_single_animation(self, animation_data: Dict[str, Any]):
        """
        Optimize a single animation's data by removing redundant keyframes.

        :param animation_data: Dictionary containing a single animation's data.
        """

        for timeline_type, timeline in walk_bone_timelines(animation_data):
            reduced = True
            while reduced:
                reduced = False
                timeline_keys = list(walk_timeline_keys(timeline))
                if len(timeline_keys) < 3:
                    continue
                to_remove = []
                skip = False  # Used for skipping when the predecessor was removed
                for i in range(1, len(timeline_keys) - 1):
                    if skip:
                        skip = False
                        continue
                    prev_key = timeline_keys[i-1]
                    curr_key = timeline_keys[i]
                    next_key = timeline_keys[i+1]
                    if is_interpolation(
                            prev_key, timeline[prev_key],
                            curr_key, timeline[curr_key],
                            next_key, timeline[next_key],
                            self.error_margin):
                        to_remove.append(curr_key)
                        skip = True
                for key in to_remove:
                    del timeline[key]
                self.total_removed[timeline_type] += len(to_remove)
                if len(to_remove) > 0:
                    reduced = True
        return animation_data
