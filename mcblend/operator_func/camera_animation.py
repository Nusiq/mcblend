'''
Functions related to exporting animations.
'''
from __future__ import annotations

from typing import NamedTuple, Dict, Optional, List, Tuple, cast, Any, Iterable, TypedDict
import json
import textwrap
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
from .sqlite_bedrock_packs.better_json_tools import CompactEncoder
from .frame_range import get_frames_from_frame_ranges
from .common import (
    AnimationLoopType, MINECRAFT_SCALE_FACTOR, MCObjType, McblendObjectGroup,
    ANIMATION_TIMESTAMP_PRECISION, NumpyTable, McblendObject
)
from .animation_utils import (
    InterpolationMode, TransformationType, Timeline, pick_closest_rotation,
    frame_to_t
)
from bpy_extras import anim_utils


'''
Alias used internally in some funcitons. It's a tuple of data of a keyframe:
- timestamp
- Optionally: (bone name, transformation type, interpolation mode)
'''
TimeNameTypeInterpolation = Tuple[
    float, None | Tuple[TransformationType, InterpolationMode]]

class ObjectKeyframesInfo:
    def __init__(
            self, obj: Object | None, 
            forced_interpolation: InterpolationMode = InterpolationMode.AUTO,
            extra_frames: set[int] | None=None):
        self.keyframes: set[float] = set()
        self.extra_keyframes: set[int] = extra_frames or set()
        self.timelines: Dict[TransformationType, Timeline] = {}
        self.forced_interpolation = forced_interpolation
        if obj is None:
            return
        self._init_keyframes_and_timelines(obj)
        # The extra keyframes should also be added to the keyframes set
        for frame in self.extra_keyframes:
            self.keyframes.add(frame)

    def get_interpolation_mode(
            self, transformation_type: TransformationType,
            timestamp: float) -> InterpolationMode:
        '''
        Returns the interpolation mode at give timestamp for given
        transformation type.

        :param transformation_type: the type of the transformation.
        :param timestamp: the timestamp of the keyframe.
        :returns: the interpolation mode
        '''
        # Return forced interpolation if not AUTO
        if self.forced_interpolation != InterpolationMode.AUTO:
            return self.forced_interpolation
            
        # If key doesn't exist always use the default - LINEAR interpolation
        timelines_key = transformation_type
        if timelines_key not in self.timelines:
            return InterpolationMode.LINEAR
        
        # Additional keyframes always use the LINEAR interpolation
        # It's safe to test if float is in set[int] in Python
        if timestamp in self.extra_keyframes:
            return InterpolationMode.LINEAR
        return self.timelines[timelines_key].get_state(timestamp)

    def add_keyframe_data(
            self, keyframe: float,
            bone_state: Tuple[TransformationType, InterpolationMode] | None=None,
            prec: int=1):
        '''
        Adds a data point about about a keyframe to this keyframe info. The
        keyframe can contain just a timestamp, or additional information
        about specific bone transformation and its interpolation mode.

        :param keyframe: the keyframe number.
        :param bone_state: optional information that tells that matches a
            specific bone transformation and its interpolation mode at that
            keyframe.
        :param prec: the precision for rounding the keyframe number.
        '''
        # Add keyframe with limited precision
        rounded_keyframe = round(keyframe, prec)
        self.keyframes.add(rounded_keyframe)

        # If there is bone state, add it to the timeline
        if bone_state is None:
            return
        transformation_type, interpolation = bone_state
        timeline = self.timelines.setdefault(transformation_type, Timeline())
        timeline.add_keyframe(rounded_keyframe, interpolation)

    def _init_keyframes_and_timelines(self, obj: Object):
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
        if obj.animation_data is None:
            return
        if obj.animation_data.action is not None:  # type: ignore
            keyframes_and_bone_states = self._get_keyframes_and_interpolations(
                obj.animation_data.action, obj.animation_data.action_slot)
            for keyframe, bone_data in keyframes_and_bone_states:
                self.add_keyframe_data(keyframe, bone_data)
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
                strip_action_keyframes = self._get_keyframes_and_interpolations(
                    strip.action, strip.action_slot)
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
                        self.add_keyframe_data(transformed_keyframe, bone_state)

    def _get_keyframes_and_interpolations(
            self,
            action: Action | None,
            slot: ActionSlot | None
    ) -> List[TimeNameTypeInterpolation]:
        '''
        Helper function for _get_keyframes(). Gets set of keyframes and bone
        states from an action.
        '''
        result: List[TimeNameTypeInterpolation] = []
        channelbag = anim_utils.action_get_channelbag_for_slot(action, slot)
        if channelbag is None:
            return result
        for fcurve in channelbag.fcurves:
            if fcurve.keyframe_points is None:  # type: ignore
                continue
            transformation_type: TransformationType | None = None
            purpose = fcurve.data_path
            if purpose == 'location':
                transformation_type = TransformationType.LOCATION
            elif "rotation" in purpose: # rotation_euler, rotation_quaternion
                transformation_type = TransformationType.ROTATION
            elif purpose == 'scale':
                transformation_type = TransformationType.SCALE
            for keyframe_point in fcurve.keyframe_points:
                # keyframe_point.interpolation can be: 'LINEAR' 'BEZIER' or
                # 'CONSTANT'
                if transformation_type is not None:
                    interpolation = InterpolationMode.LINEAR
                    if keyframe_point.interpolation == 'CONSTANT':
                        interpolation = InterpolationMode.STEP
                    elif keyframe_point.interpolation == 'BEZIER':
                        interpolation = InterpolationMode.SMOOTH
                    result.append(
                        (keyframe_point.co[0], (transformation_type, interpolation)))
                else:
                    result.append((keyframe_point.co[0], None))
        return result

class CameraTransformation(NamedTuple):
    '''Properties of a pose of single bone.'''
    name: str
    location: NumpyTable
    rotation: NumpyTable
    scale: NumpyTable
    location_interpolation: InterpolationMode = InterpolationMode.LINEAR
    rotation_interpolation: InterpolationMode = InterpolationMode.LINEAR
    scale_interpolation: InterpolationMode = InterpolationMode.LINEAR

    @staticmethod
    def from_object_and_keyframe_data(
            objprop: McblendObject,
            keyframe_info: ObjectKeyframesInfo | None = None,
            keyframe: float = 0.0
    ):
        '''
        Builds :class:`Pose` object from object properties.

        :param object_properties: group of mcblend objects.
        '''
        # Scale
        local_matrix = objprop.get_local_matrix(
            objprop.parent, normalize=False)
        scale = np.array(local_matrix.to_scale())[[0, 2, 1]]
        # Location
        location = np.array(local_matrix.to_translation())
        location = location[[0, 2, 1]] * np.array([1, 1, -1])
        # Rotation
        rotation = objprop.get_mcrotation(objprop.parent) * np.array(
            [1, -1, 1]
        )
        location_interpolation_mode = InterpolationMode.LINEAR
        rotation_interpolation_mode = InterpolationMode.LINEAR
        scale_interpolation_mode = InterpolationMode.LINEAR

        # TODO: Unlock this later when you figure out howw to pass
        # interpolation modes to the export
        # if keyframe_info is not None:
        #     location_interpolation_mode = keyframe_info.get_interpolation_mode(
        #         TransformationType.LOCATION, keyframe)
        #     rotation_interpolation_mode = keyframe_info.get_interpolation_mode(
        #         TransformationType.ROTATION, keyframe)
        #     scale_interpolation_mode = keyframe_info.get_interpolation_mode(
        #         TransformationType.SCALE, keyframe)
        return CameraTransformation(
            name=objprop.obj_name, location=location, scale=scale,
            rotation=rotation,
            location_interpolation=location_interpolation_mode,
            rotation_interpolation=rotation_interpolation_mode,
            scale_interpolation=scale_interpolation_mode,
        )

class McApiVector3(TypedDict):
    x: float
    y: float
    z: float

class McApiProgressKeyFrame(TypedDict):
    timeSeconds: float
    alpha: float

class McApiRotationKeyFrame(TypedDict):
    timeSeconds: float
    rotation: McApiVector3

class McApiCameraAnimationData(TypedDict):
    totalTimeSeconds: float
    controlPoints: list[McApiVector3]
    progressKeyFrames: list[McApiProgressKeyFrame]
    rotationKeyFrames: list[McApiRotationKeyFrame]

class CameraAnimationExport:
    '''
    Object that represents camera animation during export.

    :param length: Length of animation in seconds.
    :param fps: The FPS setting of the scene.
    :param original_transformation: Optional - the base transformation of the
        animated object.
    :param transformations: Optional - transformations of the animation
        (keyframes) keyed by the number of the frame.
    '''
    length: float
    fps: float
    original_transformation: CameraTransformation
    transformations: Dict[float, CameraTransformation] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def __init__(
            self,
            length: float,
            fps: float,
            object_properties: McblendObject,
            context: Context
    ):
        self.length = length
        self.fps = fps
        self.transformations = {}
        self.warnings = []
        self._load_camera_transformations(object_properties, context)

    def _load_camera_transformations(
            self, object_properties: McblendObject,
            context: Context
        ):
        '''
        Used in __init__ to populate calculate some initial values.

        :param object_properties: group of mcblend objects.
        :param context: the context of running the operator.
        '''
        original_frame = context.scene.frame_current
        bpy.ops.screen.animation_cancel()  # pyright: ignore[reportUnknownMemberType]
        try:
            context.scene.frame_set(0)
            self.original_transformation = CameraTransformation.from_object_and_keyframe_data(
                object_properties)
            # Add frames from frame slice pattern
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end

            # TODO: Add option to add extra keyframes
            extra_frames: set[int] = set()
            bone_states = ObjectKeyframesInfo(
                context.object,
                # TODO: Add option to choose forced interpolation
                forced_interpolation=InterpolationMode.AUTO,
                extra_frames=extra_frames
            )
            for keyframe in sorted(bone_states.keyframes):
                if (
                    keyframe < frame_start or
                    keyframe > frame_end
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
                self.transformations[keyframe] = (
                    CameraTransformation.from_object_and_keyframe_data(
                        object_properties, bone_states, keyframe)
                )
        finally:
            context.scene.frame_set(original_frame)

    def _get_mc_api_data(self) -> McApiCameraAnimationData:
        '''
        Returns optimized JSON dict with an animation of single bone.

        :param bone_name: the name of the bone.
        :returns: the part of animation with animation of a single bone.
        '''
        # Slightly modified CameraTransformation useful in this context.
        class _TransformData(NamedTuple):
            time: float
            location: List[float]
            scale: List[float]
            rotation: List[float]
            location_interpolation: InterpolationMode
            rotation_interpolation: InterpolationMode
            scale_interpolation: InterpolationMode

        transforms: List[_TransformData] = []
        prev_transform_rotation = np.zeros(3)

        # Get relative CameraTransformation with minimized rotation
        original_transform = self.original_transformation
        original_parent_transform_scale = np.ones(3)
    
        for key_frame, transform in self.transformations.items():
            # Relative transformations to the original transform
            location = transform.location - original_transform.location
            rotation = transform.rotation - original_transform.rotation
            scale = transform.scale / original_transform.scale

            # Magic
            location = location * original_parent_transform_scale
            rotation=pick_closest_rotation(
                rotation, prev_transform_rotation, original_transform.rotation)
            transforms.append(
                _TransformData(
                    time=round((key_frame-1) / self.fps, 2),
                    location=get_vect_json(location),
                    scale=get_vect_json(scale),
                    rotation=get_vect_json(rotation),
                    location_interpolation=transform.location_interpolation,
                    rotation_interpolation=transform.rotation_interpolation,
                    scale_interpolation=transform.scale_interpolation,
                )
            )
            # Update prev pose
            prev_transform_rotation = rotation

        result: McApiCameraAnimationData = {  # dictionary populated with 0 timestamp frame
            'totalTimeSeconds': 0,
            'controlPoints': [],
            'progressKeyFrames': [],
            'rotationKeyFrames': [],
        }
        # No data export
        if len(transforms) == 0:  # If empty return empty animation
            return result
        time = 0
        prev_location = transforms[0].location
        spline_distance = 0
        for i, t in enumerate(transforms):
            time = t.time
            delta_spline_distance = math.sqrt(
                (prev_location[0]-t.location[0])**2 +
                (prev_location[1]-t.location[1])**2 +
                (prev_location[2]-t.location[2])**2
            )
            spline_distance += delta_spline_distance
            prev_location=t.location
            if i == 0 or delta_spline_distance > 0.0001:
                # Minecraft sucks and there is a bug that breaks everything if
                # you put multiple "progressKeyFrames" entries with the same
                # values following each other
                result['controlPoints'].append({
                    "x": t.location[0],
                    "y": t.location[1],
                    "z": t.location[2],
                })
            result['progressKeyFrames'].append(
                {"timeSeconds": time, "alpha": spline_distance})
            result['rotationKeyFrames'].append({
                'timeSeconds': time,
                'rotation': {
                    "x": t.rotation[0],
                    "y": t.rotation[1],
                    "z": t.rotation[2],
                }
            })
        for p in result['progressKeyFrames']:
            if spline_distance > 0.0001:
                p['alpha'] /= spline_distance
            else:
                p['alpha'] = 0.0

        result['totalTimeSeconds'] = time
        return result

    def get_script_text(self) -> str:
        animation_data = self._get_mc_api_data()
        script = f"export default {json.dumps(animation_data)};\n"
        return script

    def yield_warnings(self) -> Iterable[str]:
        '''
        Yields warnings collected during the animation export process.
        '''
        yield from self.warnings
