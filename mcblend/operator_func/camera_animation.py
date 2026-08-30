'''
Functions related to exporting animations.
'''
from __future__ import annotations

from typing import (
    NamedTuple, Dict, Iterator, List, Tuple, cast, Iterable, TypedDict,
    Literal)
import json
import math # pyright: ignore[reportShadowedImports]
from itertools import product
import bpy
from bpy.types import Action, ActionSlot, Context, Object, Camera

import numpy as np

from .json_tools import get_vect_json
from .common import NumpyTable, McblendObject
from .animation_utils import (
    InterpolationMode, TransformationType, Timeline, pick_closest_rotation,
)
from bpy_extras import anim_utils
from mathutils import Euler, Quaternion
from .sqlite_bedrock_packs.better_json_tools import CompactEncoder

'''
Alias used internally in some funcitons. It's a tuple of data of a keyframe:
- timestamp
- Optionally: (bone name, transformation type, interpolation mode)
'''
TimeNameTypeInterpolation = Tuple[
    float, None | Tuple[TransformationType, InterpolationMode]]

class ObjectKeyframesInfo:
    def __init__(self, obj: Object | None):
        self.keyframes: set[float] = set()
        self.fov_keyframes: set[float] = set()
        self.timelines: Dict[TransformationType, Timeline] = {}
        if obj is None:
            return
        self._init_keyframes_and_timelines(obj)
        self._init_fov_keyframes(obj)

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
        # If key doesn't exist always use the default - LINEAR interpolation
        timelines_key = transformation_type
        if timelines_key not in self.timelines:
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

    def add_fov_keyframe_data(
            self, keyframe: float, interpolation: InterpolationMode,
            prec: int = 1):
        '''
        Analogous to add_keyframe_data() but for FOV change keyframes.
        '''
        rounded_keyframe = round(keyframe, prec)
        self.fov_keyframes.add(rounded_keyframe)
        timeline = self.timelines.setdefault(TransformationType.FOV, Timeline())
        timeline.add_keyframe(rounded_keyframe, interpolation)

    def _init_fov_keyframes(self, obj: Object):
        '''
        Analogous to _init_keyframes_and_timelines() but for FOV keyframes.
        '''
        camera_data = cast(Camera, obj.data)
        if camera_data.animation_data is None:
            return
        animation_data = camera_data.animation_data
        if animation_data.action is not None:
            for keyframe, fov_state in self._get_keyframes_and_interpolations(
                    animation_data.action, animation_data.action_slot):
                if fov_state is None or fov_state[0] != TransformationType.FOV:
                    continue
                self.add_fov_keyframe_data(keyframe, fov_state[1])
        if animation_data.nla_tracks is None:
            return
        for nla_track in animation_data.nla_tracks:
            if nla_track.mute:
                continue
            for strip in nla_track.strips:
                if strip.type != 'CLIP':
                    continue
                if strip.action is None:
                    continue
                strip_action_keyframes = self._get_keyframes_and_interpolations(
                    strip.action, strip.action_slot)
                offset = strip.frame_start
                limit_down = strip.action_frame_start
                limit_up = strip.action_frame_end
                scale = strip.scale
                cycle_length = limit_up - limit_down
                scaled_cycle_length = cycle_length * scale
                repeat = strip.repeat
                for keyframe, fov_state in sorted(
                        strip_action_keyframes, key=lambda item: item[0]):
                    if fov_state is None or fov_state[0] != TransformationType.FOV:
                        continue
                    if keyframe < limit_down or keyframe > limit_up:
                        continue
                    transformed_keyframe_base = keyframe * scale
                    for repeat_index in range(math.ceil(repeat)):
                        transformed_keyframe = (
                            (repeat_index * scaled_cycle_length) +
                            transformed_keyframe_base
                        )
                        if transformed_keyframe / scaled_cycle_length > repeat:
                            break
                        transformed_keyframe = min(
                            transformed_keyframe + offset, strip.frame_end)
                        self.add_fov_keyframe_data(
                            transformed_keyframe, fov_state[1])

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
            elif purpose == 'lens':
                transformation_type = TransformationType.FOV
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
    orientation: Quaternion
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
        scale = np.array(
            local_matrix.to_scale(), dtype=np.float64)[[0, 2, 1]]
        # Location
        location = np.array(
            local_matrix.to_translation(), dtype=np.float64)
        location = location[[0, 2, 1]] * np.array([1, 1, -1])
        orientation = local_matrix.to_quaternion()

        location_interpolation_mode = InterpolationMode.LINEAR
        rotation_interpolation_mode = InterpolationMode.LINEAR
        scale_interpolation_mode = InterpolationMode.LINEAR

        if keyframe_info is not None:
            location_interpolation_mode = keyframe_info.get_interpolation_mode(
                TransformationType.LOCATION, keyframe)
            rotation_interpolation_mode = keyframe_info.get_interpolation_mode(
                TransformationType.ROTATION, keyframe)
            scale_interpolation_mode = keyframe_info.get_interpolation_mode(
                TransformationType.SCALE, keyframe)
        return CameraTransformation(
            name=objprop.obj_name, location=location, scale=scale,
            orientation=orientation,
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

SegmentInterpolation = Literal["smooth", "linear"]

class McApiCameraAnimationData(TypedDict):
    totalTimeSeconds: float
    interpolation: SegmentInterpolation
    controlPoints: list[McApiVector3]
    progressKeyFrames: list[McApiProgressKeyFrame]
    rotationKeyFrames: list[McApiRotationKeyFrame]

class McApiFovKeyFrame(TypedDict):
    timeSeconds: float
    fov: float
    interpolation: Literal["smooth", "step", "linear"]

class McApiCameraAnimationExport(TypedDict):
    totalTimeSeconds: float
    fov: list[McApiFovKeyFrame]
    movement: list[McApiCameraAnimationData]

class _TransformData(NamedTuple):
    time: float
    location: List[float]
    rotation: List[float]
    location_interpolation: InterpolationMode
    rotation_interpolation: InterpolationMode

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
    transformations: Dict[float, CameraTransformation]
    fov_keyframes: Dict[float, Tuple[float, InterpolationMode]]
    warnings: List[str]

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
        self.fov_keyframes = {}
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
            # LOAD MOVEMENT ANIMATION
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
            obj = context.object

            bone_states = ObjectKeyframesInfo(obj)
            self.original_transformation = CameraTransformation(
                name=object_properties.obj_name,
                location=np.zeros(3),
                orientation=Quaternion((1.0, 0.0, 0.0, 0.0)),
                scale=np.ones(3),
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
            # LOAD FOV ANIMATION
            fov_frames = sorted(bone_states.fov_keyframes)
            if obj == None:
                return  # Shouldn't happen
            camera_data = cast(Camera, obj.data)

            for keyframe in fov_frames:
                if keyframe < frame_start or keyframe > frame_end:
                    continue
                float_keyframe = float(keyframe)
                frame, subframe = divmod(float_keyframe, 1)
                context.scene.frame_set(int(frame), subframe=subframe)
                fov_degrees = math.degrees(camera_data.angle)
                # Clamp the fov to the limits allowed in Minecraft
                if fov_degrees < 30:
                    fov_degrees = 30
                    self.warnings.append(
                        f"The FOV at frame {keyframe} is below the minimum "
                        "value (30 degrees) and has been changed to be "
                        "within the limit."
                    )
                elif fov_degrees > 110:
                    fov_degrees = 110
                    self.warnings.append(
                        f"The FOV at frame {keyframe} is above the maximum "
                        "value (110 degrees) and has been changed to be "
                        "within the limit."
                    )
                fov_degrees = round(fov_degrees, 2)
                self.fov_keyframes[keyframe] = (
                    fov_degrees,
                    bone_states.get_interpolation_mode(
                        TransformationType.FOV, keyframe)
                )
        finally:
            context.scene.frame_set(original_frame)

    def yield_equivalent_rotations(
            self, orientation: Quaternion,
            previous_blender_rotation: Euler | None,
    ) -> Iterator[Euler]:
        '''
        Yields blender XYZ Euler branches for the orientation defined
        by "quaternion" tries starting from previous_blender_euler angle.
        '''
        if previous_blender_rotation is None:
            euler = orientation.to_euler('XYZ')
        else:
            euler = orientation.to_euler('XYZ', previous_blender_rotation)
        half_pi = math.pi / 2.0

        # If no gimbal lock, just yield the result
        if abs(abs(euler.y) - half_pi) >= 0.01:
            yield euler
            return

        # Else (gimbal lock), yield multiple alternate numeric branches.
        # Brute-force check vrious combinations with +-90 or +-180 degrees.
        # These can be valid during gimbal lock.
        neg_orientation = orientation.copy()
        neg_orientation.negate()
        offsets = (-math.pi, -half_pi, 0.0, half_pi, math.pi)
        for x_offset, z_offset in product(offsets, repeat=2):
            partner = Euler((
                euler.x + x_offset,
                euler.y,
                euler.z + z_offset,
            ), 'XYZ')
            partner_quat = partner.to_quaternion()
            angle_dist = min(
                partner_quat.rotation_difference(orientation).angle,
                partner_quat.rotation_difference(neg_orientation).angle,
            )
            # Make sure taht yielded result is actually equivalent to the
            # original orientation
            if angle_dist >= 1e-4:
                continue
            yield partner

    def _get_transform_data(self) -> List[_TransformData]:
        '''
        Returns keyframe transforms relative to the base pose, with interpolation
        modes preserved for detecting stepped (non-continuous) segments.

        Keyframe locations are relative to ``original_transformation``.
        '''
        transforms: List[_TransformData] = []
        prev_mc_rotation = np.zeros(3)
        prev_rotation: Euler | None = None  # Blender rotation (not minecraft)

        # Populate transforms in order
        for key_frame in sorted(self.transformations):
            transform = self.transformations[key_frame]
            location = (
                transform.location -
                self.original_transformation.location)

            # Pick the Blender Euler branch closest to the previous keyframe.
            best_rotation_distance = math.inf
            best_rotation = transform.orientation.to_euler('XYZ')
            best_mc_rotation = np.zeros(3)
            for candidate in self.yield_equivalent_rotations(
                    transform.orientation, prev_rotation):
                rotation_distance = 0.0
                if prev_rotation is not None:
                    rotation_distance = float(
                        np.linalg.norm(
                            np.array(candidate) -
                            np.array(prev_rotation)
                        )
                    )
                if rotation_distance >= best_rotation_distance:
                    continue
                best_rotation_distance = rotation_distance
                best_rotation = candidate
                # I'm not sure if pick_closest_rotation() is needed here
                # since the code above already tries to pick a close result
                # in very similar way.
                best_mc_rotation = pick_closest_rotation(
                    np.array(
                        [candidate.x-math.pi/2, candidate.z, -candidate.y],
                        dtype=float) * 180.0/math.pi,
                    prev_mc_rotation
                )
            prev_rotation = best_rotation
            transforms.append(
                _TransformData(
                    time=round((key_frame-1) / self.fps, 2),
                    location=get_vect_json(location),
                    rotation=get_vect_json(best_mc_rotation),
                    location_interpolation=transform.location_interpolation,
                    rotation_interpolation=transform.rotation_interpolation,
                )
            )
            # Update prev pose
            prev_mc_rotation = best_mc_rotation
        return transforms

    def _split_transforms_at_steps(
            self, transforms: List[_TransformData],
    ) -> List[List[_TransformData]]:
        '''
        Splits transforms into continuous segments. A new segment starts at a
        keyframe that follows a stepped hold on location or rotation (same rule
        as animation.py _get_keyframe_json when previous_interpolation is STEP).
        '''
        if len(transforms) == 0:
            return []
        # [index, whether it's a step or not]
        segment_starts: List[Tuple[int, bool]] = [(0, True)]
        prev_prev_loc_interp = None
        for index in range(1, len(transforms)):
            prev = transforms[index - 1]
            if (
                prev.location_interpolation == InterpolationMode.STEP or
                prev.rotation_interpolation == InterpolationMode.STEP
            ):
                segment_starts.append((index, True))
            elif (
                    prev_prev_loc_interp != None and
                    prev_prev_loc_interp != InterpolationMode.STEP and
                    prev_prev_loc_interp != prev.location_interpolation):
                segment_starts.append((index, False))
            prev_prev_loc_interp = prev.location_interpolation

        segments: List[List[_TransformData]] = []
        for segment_index, (start, _) in enumerate(segment_starts):
            end = len(transforms)
            next_segment_is_step = False
            if segment_index + 1 < len(segment_starts):
                next_segment = segment_starts[segment_index + 1]
                end = next_segment[0]
                next_segment_is_step = next_segment[1]
            # If it's not a sudden STEP, then the ending of this segment must
            # overlap with the start of the next segment.
            if not next_segment_is_step:
                end += 1
            segments.append(transforms[start:end])
        return segments

    def _fix_control_points(
            self, control_points: list[McApiVector3],
    ) -> list[McApiVector3]:
        '''
        Minecraft's API xrequires at least three control points for
        LinearSpline. This methods adds additional control points without
        significantly changing the spline to make the Minecraft API happy.
        '''
        if len(control_points) == 0:
            # Hopefully shouldn't happen in normal animations
            return control_points
        if len(control_points) == 2:
            first, second = control_points
            return [
                first,
                {
                    'x': (first['x'] + second['x']) / 2,
                    'y': (first['y'] + second['y']) / 2,
                    'z': (first['z'] + second['z']) / 2,
                },
                second,
            ]
        if len(control_points) >= 3:
            # Normal case
            return control_points

        # control_points == 1 add middle frame with small offset
        point = control_points[0]
        return [
            point, {
                'x': point['x'],
                'y': point['y'] + 0.0001,
                'z': point['z'],
            },
            point
        ]

    def _transforms_to_mc_api_data(
            self, transforms: List[_TransformData], end_time: float
    ) -> McApiCameraAnimationData:
        '''
        Builds a single CameraAnimationData dict from a continuous segment of
        transforms. Times are relative to the first keyframe in the segment.
        '''
        result: McApiCameraAnimationData = {
            'totalTimeSeconds': 0,
            'interpolation': 'linear',
            'controlPoints': [],
            'progressKeyFrames': [],
            'rotationKeyFrames': [],
        }
        # No data export
        if len(transforms) == 0:  # If empty return empty animation
            return result
        time_offset = transforms[0].time
        prev_location = transforms[0].location
        spline_distance = 0.0
        time = 0.0
        for i, t in enumerate(transforms):
            time = t.time - time_offset
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
            rotation = np.array(t.rotation, dtype=float)

            # Minecraft behaves in a weird ways when the camera is upside down
            # this hack below, fixes it.
            if rotation[2] > 90.0 or rotation[2] < -90.0:
                rotation = rotation * np.array([-1.0, 1.0, 1.0])
            result['rotationKeyFrames'].append({
                'timeSeconds': time,
                'rotation': {
                    "x": float(rotation[0]),
                    "y": float(rotation[1]),
                    "z": float(rotation[2]),
                }
            })
        for p in result['progressKeyFrames']:
            if spline_distance > 0.0001:
                p['alpha'] /= spline_distance
            else:
                p['alpha'] = 0.0

        result['controlPoints'] = self._fix_control_points(
            result['controlPoints'])
        
        # If we have enough control points, allow the smooth inteprolation, if
        # the segment is a smooth interpolation type.
        if (
                len(result['controlPoints']) >= 4 and
                transforms[0].location_interpolation ==
                    InterpolationMode.SMOOTH):
            result['interpolation'] = "smooth"
        result['totalTimeSeconds'] = end_time - time_offset
        return result

    def get_script_text(self) -> str:
        # Get the data for the movement animation
        transforms = self._get_transform_data()
        segments = self._split_transforms_at_steps(transforms)
        movement_data: list[McApiCameraAnimationData] = []
        for i, segment in enumerate(segments):
            try:
                next_time = segments[i + 1][0].time
            except:
                next_time = self.length
            movement_data.append(
                self._transforms_to_mc_api_data(segment, next_time)
            )
        # Get the data for the FOV animation
        fov_data: list[McApiFovKeyFrame] = []
        for keyframe in sorted(self.fov_keyframes):
            fov_degrees, interpolation = self.fov_keyframes[keyframe]
            interpolation_str = "linear"
            if interpolation == InterpolationMode.STEP:
                interpolation_str = "step"
            elif interpolation == InterpolationMode.LINEAR:
                interpolation_str = "linear"
            elif interpolation == InterpolationMode.SMOOTH:
                interpolation_str = "smooth"
            fov_data.append({
                'timeSeconds': round((keyframe - 1) / self.fps, 2),
                'fov': fov_degrees,
                'interpolation': interpolation_str
            })
        # Combine for the output
        animation_data = {
            'totalTimeSeconds': self.length,
            'fov': fov_data,
            'movement': movement_data,
        }
        script = f"export default {json.dumps(animation_data)};\n"
        return script

    def yield_warnings(self) -> Iterable[str]:
        '''
        Yields warnings collected during the animation export process.
        '''
        yield from self.warnings