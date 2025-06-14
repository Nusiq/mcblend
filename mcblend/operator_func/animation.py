'''
Functions related to exporting animations.
'''
from __future__ import annotations

from typing import NamedTuple, Dict, Optional, List, Tuple, Set, cast, Any, Literal
import math # pyright: ignore[reportShadowedImports]
import re
import bisect
from enum import Enum
from dataclasses import dataclass, field
from itertools import tee, islice  # pyright: ignore[reportShadowedImports]
from decimal import Decimal

import bpy
from bpy.types import Action, Context, Object

import numpy as np

from .json_tools import get_vect_json
from .common import (
    AnimationLoopType, MINECRAFT_SCALE_FACTOR, MCObjType, McblendObjectGroup,
    ANIMATION_TIMESTAMP_PRECISION, NumpyTable
)

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

def _pick_closest_rotation(
        base: NumpyTable, close_to: NumpyTable,
        original_rotation: Optional[NumpyTable] = None
    ) -> NumpyTable:
    '''
    Takes two arrays with euler rotations in degrees. Looks for rotations
    that result in same orientation ad the base rotation. Picks the vector
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


'''
Alias used internally in some funcitons. It's a tuple of data of a keyframe:
- timestamp
- Optionally: (bone name, transformation type, interpolation mode)
'''
TimeNameTypeInterpolation = Tuple[
    float, None | Tuple[str, TransformationType, InterpolationMode]]

class ObjectKeyframesInfo:
    def __init__(
            self, obj: Object | None, 
            forced_interpolation: InterpolationMode = InterpolationMode.AUTO):
        self.keyframes: set[float] = set()
        self.timelines: Dict[tuple[str, TransformationType], Timeline] = {}
        self.forced_interpolation = forced_interpolation
        if obj is None:
            return
        self._init_keyframes_and_timelines(obj)

    def get_bone_state(
            self, bone_name: str, transformation_type: TransformationType,
            timestamp: float) -> InterpolationMode:
        '''
        Returns the interpolation mode of the bone state at the given timestamp.

        :param bone_name: the name of the bone.
        :param transformation_type: the type of the transformation.
        :param timestamp: the timestamp of the keyframe.
        :returns: the interpolation mode of the bone state.
        '''
        # Return forced interpolation if not AUTO
        if self.forced_interpolation != InterpolationMode.AUTO:
            return self.forced_interpolation
            
        timelines_key = (bone_name, transformation_type)
        if timelines_key not in self.timelines:
            return InterpolationMode.LINEAR
        return self.timelines[timelines_key].get_state(timestamp)

    def _init_keyframes_and_timelines(self, obj: Object, prec: int=1):
        '''
        Lists keyframe numbers of the animation from keyframes of NLA tracks and
        actions of the active object. The results are returned as float (allowing
        use of the subframes). The precision of the results is limited to the value
        specified by the prec argument.

        !!! Important note

        The precision limitation is applied to avoid very small differences in the
        keyframe numbers. In most cases the values are aligned with the actual
        frames in blender (which already are a fraction of a second). The default
        value of 1 allows dividing the frames into 10 parts. Later in the code
        (outside of the scope of this function) when the values are converted to
        seconds, the precision limit is defined by ANIMATION_TIMESTAMP_PRECISION
        constant.

        :param obj: the object to get the keyframes from.
        :returns: the list of the keyframes for the animation.
        '''
        # pylint: disable=too-many-nested-blocks
        def _add_keyframe_data(
                keyframe: float,
                bone_state:
                    None | Tuple[str, TransformationType, InterpolationMode]):
            # Add keyframe with limited precision
            rounded_keyframe = round(keyframe, prec)
            self.keyframes.add(rounded_keyframe)

            # If there is bone state, add it to the timeline
            if bone_state is None:
                return
            bone_name, transformation_type, interpolation = bone_state
            timelines_key = (bone_name, transformation_type)
            timeline = self.timelines.setdefault(timelines_key, Timeline())
            timeline.add_keyframe(rounded_keyframe, interpolation)

        if obj.animation_data is None:  # type: ignore
            return
        if obj.animation_data.action is not None:  # type: ignore
            keyframes_and_bone_states = self._get_keyframes_and_bone_states(
                obj.animation_data.action)
            for keyframe, bone_data in keyframes_and_bone_states:
                _add_keyframe_data(keyframe, bone_data)
        if obj.animation_data.nla_tracks is None:  # type: ignore
            return
        for nla_track in obj.animation_data.nla_tracks:
            if nla_track.mute:
                continue
            for strip in nla_track.strips:
                if strip.type != 'CLIP':
                    continue
                if strip.action is None:
                    continue
                strip_action_keyframes = self._get_keyframes_and_bone_states(
                    strip.action)
                # Scale/strip the action data with the strip
                # transformations
                offset =  strip.frame_start
                limit_down =  strip.action_frame_start
                limit_up =  strip.action_frame_end
                scale =  strip.scale
                cycle_length = limit_up - limit_down
                scaled_cycle_length = cycle_length * scale
                repeat =  strip.repeat
                for (keyframe, bone_state) in sorted(
                        strip_action_keyframes, key=lambda x: x[0]):
                    if keyframe < limit_down or keyframe > limit_up:
                        continue
                    transformed_keyframe_base = keyframe * scale
                    for i in range(math.ceil(repeat)):
                        transformed_keyframe = (
                            (i * scaled_cycle_length) +
                            transformed_keyframe_base
                        )
                        if transformed_keyframe/scaled_cycle_length > repeat:
                            # Can happen when we've got for example 4th
                            # repeat but we only need 3.5
                            break
                        transformed_keyframe = min(
                            transformed_keyframe + offset, strip.frame_end)
                        _add_keyframe_data(transformed_keyframe, bone_state)

    def _get_keyframes_and_bone_states(
            self, action: Action) -> List[TimeNameTypeInterpolation]:
        '''
        Helper function for _get_keyframes(). Gets set of keyframes and bone
        states from an action.

        The result is a dictionary with keyframes (floats) as keys and lists
        of tuples with bone name, transformation type and interpolation mode
        as values.

        The floats used as keys are rounded so there shouldn't be any
        issues with keys that are very close to each other.
        '''
        pattern = re.compile(
            r'pose\.bones\[(?:\'|")([^\]]+)(?:\'|")\]\.([a-zA-Z0-9_]+)')
        if action.fcurves is None:  # type: ignore
            return []
        result: List[TimeNameTypeInterpolation] = []
        for fcurve in action.fcurves:
            if fcurve.keyframe_points is None:  # type: ignore
                continue
            keyframe_owner_bone: tuple[str, TransformationType] | None = None
            match = re.match(pattern, fcurve.data_path)
            if match is not None:
                bone_name = match.group(1)
                purpose = match.group(2)
                if purpose == 'location':
                    keyframe_owner_bone = (bone_name, TransformationType.LOCATION)
                elif "rotation" in purpose: # rotation_euler, rotation_quaternion
                    keyframe_owner_bone = (bone_name, TransformationType.ROTATION)
                elif purpose == 'scale':
                    keyframe_owner_bone = (bone_name, TransformationType.SCALE)
            for keyframe_point in fcurve.keyframe_points:
                # keyframe_point.interpolation can be: 'LINEAR' 'BEZIER' or
                # 'CONSTANT'
                if keyframe_owner_bone is not None:
                    interpolation = InterpolationMode.LINEAR
                    if keyframe_point.interpolation == 'CONSTANT':
                        interpolation = InterpolationMode.STEP
                    elif keyframe_point.interpolation == 'BEZIER':
                        interpolation = InterpolationMode.SMOOTH
                    # Create a properly structured tuple that matches TimeNameTypeInterpolation
                    bone_name, transform_type = keyframe_owner_bone
                    result.append(
                        (keyframe_point.co[0], (bone_name, transform_type, interpolation)))
                else:
                    result.append((keyframe_point.co[0], None))
        return result



class PoseBone(NamedTuple):
    '''Properties of a pose of single bone.'''
    name: str
    location: NumpyTable
    rotation: NumpyTable
    scale: NumpyTable
    parent_name: Optional[str] = None
    location_interpolation: InterpolationMode = InterpolationMode.LINEAR
    rotation_interpolation: InterpolationMode = InterpolationMode.LINEAR
    scale_interpolation: InterpolationMode = InterpolationMode.LINEAR

class Pose:
    '''A pose in a frame of animation.'''
    def __init__(self) -> None:
        self.pose_bones: Dict[str, PoseBone] = {}
        '''dict of bones in a pose keyed by the name of the bones'''

    def load_poses(
            self, object_properties: McblendObjectGroup,
            bone_states: ObjectKeyframesInfo | None = None,
            keyframe: float = 0.0):
        '''
        Builds :class:`Pose` object from object properties.

        :param object_properties: group of mcblend objects.
        '''
        for objprop in object_properties.values():
            if objprop.mctype == MCObjType.BONE:
                # Scale
                local_matrix = objprop.get_local_matrix(
                    objprop.parent, normalize=False)
                scale = np.array(local_matrix.to_scale())[[0, 2, 1]]
                # Location
                location = np.array(local_matrix.to_translation())
                location = location[[0, 2, 1]] * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = objprop.get_mcrotation(objprop.parent)
                if objprop.parent is not None:
                    parent_name=objprop.parent.obj_name
                else:
                    parent_name=None
                location_interpolation_mode = InterpolationMode.LINEAR
                rotation_interpolation_mode = InterpolationMode.LINEAR
                scale_interpolation_mode = InterpolationMode.LINEAR
                if bone_states is not None:
                    location_interpolation_mode = bone_states.get_bone_state(
                        objprop.obj_name, TransformationType.LOCATION, keyframe)
                    rotation_interpolation_mode = bone_states.get_bone_state(
                        objprop.obj_name, TransformationType.ROTATION, keyframe)
                    scale_interpolation_mode = bone_states.get_bone_state(
                        objprop.obj_name, TransformationType.SCALE, keyframe)
                self.pose_bones[objprop.obj_name] = PoseBone(
                    name=objprop.obj_name, location=location, scale=scale,
                    rotation=rotation, parent_name=parent_name,
                    location_interpolation=location_interpolation_mode,
                    rotation_interpolation=rotation_interpolation_mode,
                    scale_interpolation=scale_interpolation_mode,
                )

@dataclass
class AnimationExport:
    '''
    Object that represents animation during export.

    :param name: Name of the animation.
    :param length: Length of animation in seconds.
    :param loop_animation: Whether the Minecraft animation should be exported
        with loop property set to true.
    :param anim_time_update: Value of anim_time_update property of Minecraft
        animation.
    :param fps: The FPS setting of the scene.
    :param effect_events: The events of the animation from
        MCBLEND_EventProperties.
    :param original_pose: Optional - the base pose of the animated object.
        The pose is empty by default after object creation until it's loaded.
    :param single_frame: Optional - whether the animation should be exported as
        a single frame pose (True) or as whole animation. False by default.
    :param poses: Optional - poses of the animation (keyframes) keyed by the
        number of the frame. This dictionary is empty by default after the
        creation and it gets populated on loading the poses.
    :param forced_interpolation: Optional - force all keyframes to use a specific
        interpolation mode: InterpolationMode.LINEAR, InterpolationMode.SMOOTH,
        InterpolationMode.STEP, or InterpolationMode.AUTO (default).
    '''
    name: str
    length: float
    loop_animation: str
    anim_time_update: str
    override_previous_animation: bool
    fps: float
    effect_events: Dict[str, Tuple[List[Dict[Any, Any]], List[Dict[Any, Any]]]]
    original_pose: Pose = field(default_factory=Pose)
    single_frame: bool = field(default_factory=bool)  # bool() = False
    poses: Dict[float, Pose] = field(default_factory=dict)
    sound_effects: Dict[int, List[Dict[Any, Any]]] = field(default_factory=dict)
    particle_effects: Dict[int, List[Dict[Any, Any]]] = field(default_factory=dict)
    forced_interpolation: InterpolationMode = field(
        default=InterpolationMode.AUTO)

    def load_poses_and_bone_states(
            self, object_properties: McblendObjectGroup,
            context: Context
        ):
        '''
        Populates the poses dictionary of this object.

        :param object_properties: group of mcblend objects.
        :param context: the context of running the operator.
        '''
        original_frame = context.scene.frame_current
        bpy.ops.screen.animation_cancel()  # pyright: ignore[reportUnknownMemberType]
        try:
            context.scene.frame_set(0)
            self.original_pose.load_poses(object_properties)
            if self.single_frame:
                context.scene.frame_set(original_frame)
                pose = Pose()
                keyframe = float(original_frame)
                pose.load_poses(object_properties)

                # The frame value in the dictionary key doesn't really matter
                self.poses[keyframe] = pose
            else:
                bone_states = ObjectKeyframesInfo(
                    context.object, forced_interpolation=self.forced_interpolation
                )
                for keyframe in sorted(bone_states.keyframes):
                    if (
                        keyframe < context.scene.frame_start or
                        keyframe > context.scene.frame_end
                    ):
                        continue  # skip frames out of range

                    # Converting to float before divmod() operation is because
                    # divmod() behaves differently for Decimal and float for
                    # negative numbers:
                    # divmod(Decimal(-4.5), 1) -> (Decimal(-4), Decimal(-0.5))
                    # divmod(-4.5, 1) -> (5, -0.5)
                    float_keyframe = float(keyframe)
                    frame, subframe = divmod(float_keyframe, 1)
                    context.scene.frame_set(int(frame), subframe=subframe)
                    curr_pose = Pose()

                    curr_pose.load_poses(
                        object_properties, bone_states, keyframe)
                    self.poses[keyframe] = curr_pose
                # Load sound effects and particle effects
                for timeline_marker in context.scene.timeline_markers:
                    if timeline_marker.name not in self.effect_events:
                        continue
                    sound, particle = self.effect_events[timeline_marker.name]
                    if len(sound) > 0:
                        self.sound_effects[timeline_marker.frame] = sound
                    if len(particle) > 0:
                        self.particle_effects[timeline_marker.frame] = particle
        finally:
            context.scene.frame_set(original_frame)

    def json(
            self, old_json: Optional[Dict[str, Any]]=None,
            skip_rest_poses: bool=True) -> Dict[str, Any]:
        '''
        Returns the JSON dict with Minecraft animation. If JSON dict with
        valid animation file is passed to the function the function
        modifies it's content.

        :param old_json: The original animation file to write into.
        :param skip_rest_poses: If true the exported animation won't contain
            information about bones that remain in the rest pose.
        :returns: JSON dict with Minecraft animation.
        '''
        # Create result dict
        result: Dict[str, Any] = {"format_version": "1.8.0", "animations": {}}
        try:
            if isinstance(old_json['animations'], dict):  # type: ignore
                result = old_json  # type: ignore
        except (TypeError, LookupError):
            pass

        bones: Dict[str, Dict[str, Any]] = {}
        for bone_name in self.original_pose.pose_bones:
            bone = self._json_bone(bone_name, skip_rest_poses)
            if bone != {}:  # Nothing to export
                bones[bone_name] = bone

        if self.single_frame:
            # Other properties don't apply
            result["animations"][f"animation.{self.name}"] = {
                "bones": bones,
                "loop": True
            }
            data: Any = result["animations"][f"animation.{self.name}"]
            if self.override_previous_animation:
                data['override_previous_animation'] = True
        else:
            result["animations"][f"animation.{self.name}"] = {
                "animation_length": self.length,
                "bones": bones
            }
            if len(self.particle_effects) > 0:
                particle_effects = {}
                for key_frame, value in self.particle_effects.items():
                    particle_effects[frame_to_t(key_frame, self.fps)] = value
                result["animations"][f"animation.{self.name}"][
                    'particle_effects'] = particle_effects

            if len(self.sound_effects) > 0:
                sound_effects = {}
                for key_frame, value in self.sound_effects.items():
                    sound_effects[frame_to_t(key_frame, self.fps)] = value
                result["animations"][f"animation.{self.name}"][
                    'sound_effects'] = sound_effects

            data = result["animations"][f"animation.{self.name}"]
            if self.loop_animation == AnimationLoopType.TRUE.value:
                data['loop'] = True
            elif (
                    self.loop_animation ==
                    AnimationLoopType.HOLD_ON_LAST_FRAME.value):
                data['loop'] = AnimationLoopType.HOLD_ON_LAST_FRAME.value
            if self.anim_time_update != "":
                data['anim_time_update'] = self.anim_time_update
            if self.override_previous_animation:
                data['override_previous_animation'] = True
        return result

    def _json_bone(
            self, bone_name: str, skip_rest_pose: bool) -> Dict[str, Any]:
        '''
        Returns optimized JSON dict with an animation of single bone.

        :param bone_name: the name of the bone.
        :param skip_rest_pose: whether the properties of the bone being in
            its rest pose should be skipped.
        :returns: the part of animation with animation of a single bone.
        '''
        # Slightly modified PoseBone useful in this context.
        class _PoseData(NamedTuple):
            time: str
            location: List[float]
            scale: List[float]
            rotation: List[float]
            location_interpolation: InterpolationMode
            rotation_interpolation: InterpolationMode
            scale_interpolation: InterpolationMode

        poses: List[_PoseData] = []
        prev_bone_rotation = np.zeros(3)

        # Get relative PoseBone with minimized rotation
        original_pose_bone = self.original_pose.pose_bones[bone_name]
        parent_name = original_pose_bone.parent_name
        # Get original parent scale. Scaling the location with original
        # parent scale allows to have issue #71 fixed and also being able
        # to use scale in animations (issue #76) which was impossible to do
        # after commit 19ef865943da7fde039bba7b7f50d1fa69a140b6 (the one
        # which closed issue #71).
        if parent_name in self.original_pose.pose_bones:
            original_parent_pose_bone = self.original_pose.pose_bones[
                parent_name]
            original_parent_pose_bone_scale = original_parent_pose_bone.scale
        else:
            original_parent_pose_bone_scale = np.ones(3)
    
        for key_frame, pose in self.poses.items():
            pose_bone = pose.pose_bones[bone_name]
            # Relative transformations to the original pose
            location = pose_bone.location - original_pose_bone.location
            rotation = pose_bone.rotation - original_pose_bone.rotation
            scale = pose_bone.scale / original_pose_bone.scale

            # Magic
            location = location * original_parent_pose_bone_scale
            rotation=_pick_closest_rotation(
                rotation, prev_bone_rotation, original_pose_bone.rotation)
            poses.append(
                _PoseData(
                    time=frame_to_t(key_frame, self.fps),
                    location=get_vect_json(location),
                    scale=get_vect_json(scale),
                    rotation=get_vect_json(rotation),
                    location_interpolation=pose_bone.location_interpolation,
                    rotation_interpolation=pose_bone.rotation_interpolation,
                    scale_interpolation=pose_bone.scale_interpolation,
                )
            )
            # Update prev pose
            prev_bone_rotation = rotation

        # No data export
        if not poses:  # If empty return empty animation
            return {'position': {}, 'rotation': {}, 'scale': {}}
        
        # Single frame pose export
        if self.single_frame:  # Returning single frame pose is easier
            result: Dict[str, Any] = {}
            loc, rot, scl = poses[0].location, poses[0].rotation, poses[0].scale
            # Filter rest pose positions
            if loc != [0, 0, 0] or not skip_rest_pose:
                result['position'] = poses[0].location
            if rot != [0, 0, 0] or not skip_rest_pose:
                result['rotation'] = poses[0].rotation
            if scl != [1, 1, 1] or not skip_rest_pose:
                result['scale'] = poses[0].scale
            return result
        bone: Dict[str, Any] = {  # dictionary populated with 0 timestamp frame
            'position': {poses[0].time: poses[0].location},
            'rotation': {poses[0].time: poses[0].rotation},
            'scale': {poses[0].time: poses[0].scale},
        }

        # Iterate in threes (previous, current , next) remove unnecessary items
        prev_iter, curr_iter, next_iter = tee(poses, 3)
        iterator = zip(
            prev_iter, islice(curr_iter, 1, None), islice(next_iter, 2, None))
        for p, c, n in iterator:  # previous, current, next
            if not (p.scale == c.scale == n.scale):
                bone['scale'][c.time] = self._get_keyframe_json(
                    p.scale, c.scale, n.scale,
                    p.scale_interpolation,
                    c.scale_interpolation)
            if not (p.location == c.location == n.location):
                bone['position'][c.time] = self._get_keyframe_json(
                    p.location, c.location, n.location,
                    p.location_interpolation,
                    c.location_interpolation)
            if not (p.rotation == c.rotation == n.rotation):
                bone['rotation'][c.time] = self._get_keyframe_json(
                    p.rotation, c.rotation, n.rotation,
                    p.rotation_interpolation,
                    c.rotation_interpolation)

        # Add last element unless there is only one (in which case it's already
        # added)
        if len(poses) > 1:
            bone['rotation'][poses[-1].time] = poses[-1].rotation
            bone['position'][poses[-1].time] = poses[-1].location
            bone['scale'][poses[-1].time] = poses[-1].scale
        # Filter rest pose positions
        if skip_rest_pose:
            for v in bone['position'].values():
                if v != [0, 0, 0]:
                    break  # found non-rest pose item
            else:  # this is rest pose
                del bone['position']

            for v in bone['rotation'].values():
                if v != [0, 0, 0]:
                    break  # found non-rest pose item
            else:  # this is rest pose
                del bone['rotation']

            for v in bone['scale'].values():
                if v != [1, 1, 1]:
                    break  # found non-rest pose item
            else:  # this is rest pose
                del bone['scale']
        return bone

    def _get_keyframe_json(
            self,
            previous_value: list[float],
            current_value: list[float],
            next_value: list[float],
            previous_interpolation: InterpolationMode,
            current_interpolation: InterpolationMode) -> Any:
        '''
        Returns the JSON representation of the keyframe.
        '''
        if previous_value != current_value or current_value != next_value:
            if previous_interpolation == InterpolationMode.STEP:
                return {
                    "pre": previous_value,
                    "post": current_value,
                }
            elif current_interpolation == InterpolationMode.SMOOTH:
                if previous_interpolation == InterpolationMode.SMOOTH:
                    return {
                        "post": current_value,
                        "lerp_mode": "catmullrom"
                    }
                else:
                    return {
                        "pre": current_value,
                        "post": current_value,
                        "lerp_mode": "catmullrom"
                    }
            return current_value
