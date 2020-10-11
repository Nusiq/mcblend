'''
Functions related to exporting animations.
'''
from __future__ import annotations

from typing import NamedTuple, Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from itertools import tee, islice

import bpy
import bpy_types
import mathutils

import numpy as np
from .json_tools import get_vect_json
from .common import (
    MINECRAFT_SCALE_FACTOR, MCObjType, McblendObjectGroup
)


def _pick_closest_rotation(
        base: np.ndarray, close_to: np.ndarray,
        original_rotation: Optional[np.ndarray] = None
    ) -> np.ndarray:
    '''
    Takes two arrays with euler rotations in degrees. Looks for rotations
    that result in same orientation ad the base rotation. Picks the vector
    which is the closest to the :code:`close_to` using euclidean distance.

    *The :code:`original_rotation` is added specificly to fix some issues with
    bones rotated before the animation. Issue #25 on Github describes the
    problem in detail.

    :base: np.ndarray: the base rotation. Function is looking for different
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

    def _pick_closet_location(
            base: np.ndarray, close_to: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        choice: np.ndarray = base
        distance = np.linalg.norm(choice - close_to)

        for i in range(3):  # Adds removes 360 to all 3 axis (picks the best)
            arr = np.zeros(3)
            arr[i] = 360
            while choice[i] < close_to[i]:
                new_choice = choice + arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                distance, choice = new_distance, new_choice
            while choice[i] > close_to[i]:
                new_choice = choice - arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                distance, choice = new_distance, new_choice
        return distance, choice

    distance1, choice1 = _pick_closet_location(base, close_to)
    distance2, choice2 = _pick_closet_location(  # Counterintuitive but works
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

def _get_next_keyframe(context: bpy_types.Context) -> Optional[int]:
    '''
    Returns the next keyframe index from selected objects or None if there is
    no more keyframes to chose from until the entd of animation.

    :param context: the context of running the operator.
    :returns: index of the next keyframe or None.
    '''
    curr = context.scene.frame_current
    next_keyframe = None
    for obj in context.selected_objects:
        if (
                obj.animation_data is None or
                obj.animation_data.action is None or
                obj.animation_data.action.fcurves is None
        ):
            continue
        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.keyframe_points is None:
                continue
            for kframe_point in fcurve.keyframe_points:
                time = kframe_point.co[0]
                if time <= curr:
                    continue
                if next_keyframe is None:
                    next_keyframe = time
                else:
                    next_keyframe = min(time, next_keyframe)
    if next_keyframe is not None and next_keyframe > context.scene.frame_end:
        return None
    return next_keyframe

class PoseBone(NamedTuple):
    '''Properties of a pose of single bone.'''
    name: str
    location: np.array
    rotation: np.array
    scale: np.array

    def relative(self, original: PoseBone) -> PoseBone:
        '''
        Returns :class:`PoseBone` object with properties of the bone
        relative to the original pose.

        :param original: the original pose.
        '''
        return PoseBone(
            name=self.name, scale=self.scale / original.scale,
            location=self.location - original.location,
            rotation=self.rotation - original.rotation,
        )

class Pose:
    '''A pose in a frame of animation.'''
    def __init__(self):
        self.pose_bones: Dict[str, PoseBone] = {}
        '''dict of bones in a pose keyd by the name of the bones'''

    def load_poses(
            self, object_properties: McblendObjectGroup
        ):
        '''
        Builds :class:`Pose` object from object properties.

        :param object_properties: group of mcblend objects.
        '''
        for objprop in object_properties.values():
            if objprop.mctype in [MCObjType.BONE, MCObjType.BOTH]:
                # Scale
                scale = (
                    np.array(objprop.obj_matrix_world.to_scale()) /
                    # pylint: disable=no-value-for-parameter
                    np.array(mathutils.Matrix().to_scale())
                )[[0, 2, 1]]
                # Locatin
                local_matrix = objprop.get_local_matrix(objprop.parent)
                location = np.array(local_matrix.to_translation())
                location = location[[0, 2, 1]] * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = objprop.get_mcrotation(objprop.parent)
                self.pose_bones[objprop.obj_name] = PoseBone(
                    name=objprop.obj_name, location=location, scale=scale,
                    rotation=rotation
                )

@dataclass
class AnimationExport:
    '''
    Object that represents animation during export.

    :param name: Name of the animation.
    :param length: Length of animation in seconds.
    :param loop_animation: Whether the Minecraft animation shuold be exported
        with loop property set to true.
    :param anim_time_update: Value of anim_time_update property of Minecraft
        animation.
    :param fps: The FPS setting of the scene.
    :param original_pose: Optional - the base pose of the animated object.
        The pose is empty by default after object creation until it's loaded.
    :param single_frame: Optional - whether the animation should be exported as
        a single frame pose (True) or as whole animation. False by default.
    :param poses: Opational - poses of the animation (keyframes) keyed by the
        number of the frame. This dictionary is empty by default after the
        creation and it gets populated on loading the poses.
    '''
    name: str
    length: float
    loop_animation: bool
    anim_time_update: str
    fps: float
    original_pose: Pose = field(default_factory=Pose)
    single_frame: bool = field(default_factory=bool)  # bool() = False
    poses: Dict[int, Pose] = field(default_factory=dict)

    def load_poses(
            self, object_properties: McblendObjectGroup,
            context: bpy_types.Context
        ):
        '''
        Populates the poses dictoionary of this object.

        :param object_properties: group of mcblend objects.
        :param context: the context of running the operator.
        '''
        original_frame = context.scene.frame_current
        bpy.ops.screen.animation_cancel()
        try:
            context.scene.frame_set(0)
            self.original_pose.load_poses(object_properties)
            if self.single_frame:
                context.scene.frame_set(original_frame)
                pose = Pose()
                pose.load_poses(object_properties)

                # The frame value in the dictionary key doesn't really matter
                self.poses[original_frame] = pose
            else:
                # next_keyframe = _get_next_keyframe(context)
                next_keyframe = context.scene.frame_start
                while next_keyframe is not None:
                    context.scene.frame_set(next_keyframe)
                    curr_pose = Pose()
                    curr_pose.load_poses(object_properties)
                    self.poses[next_keyframe] = curr_pose
                    next_keyframe = _get_next_keyframe(context)
        finally:
            context.scene.frame_set(original_frame)

    def json(self, old_json: Optional[Dict] = None) -> Dict:
        '''
        Returns the JSON dict with Minecraft animation. If JSON dict with
        valid animation file is passed to the function the function
        modifies it's content.

        :param old_json: The original animation file to write into.
        :returns: JSON dict with Minecraft animation.
        '''
        # Create result dict
        result: Dict = {"format_version": "1.8.0", "animations": {}}
        try:
            if isinstance(old_json['animations'], dict):  # type: ignore
                result: Dict = old_json  # type: ignore
        except (TypeError, LookupError):
            pass

        bones: Dict = {}
        for bone_name in self.original_pose.pose_bones:
            bones[bone_name] = self._json_bone(bone_name)

        if self.single_frame:
            # Other properties don't apply
            result["animations"][f"animation.{self.name}"] = {
                "bones": bones,
                "loop": True
            }
        else:
            result["animations"][f"animation.{self.name}"] = {
                "animation_length": self.length,
                "bones": bones
            }
            data = result["animations"][f"animation.{self.name}"]
            if self.loop_animation:
                data['loop'] = True
            if self.anim_time_update != "":
                data['anim_time_update'] = self.anim_time_update
        return result

    def _json_bone(
                self, bone_name: str
        ) -> Dict:
        '''
        Returns optimised JSON dict with an animation of single bone.

        :param bone_name: the name of the bone.
        :returns: the part of animation with animation of a single bone.
        '''
        # t, rot, loc, scale
        poses: List[Dict] = []
        prev_pose_bone = PoseBone(
            name=bone_name, scale=np.zeros(3), location=np.zeros(3),
            rotation=np.zeros(3),
        )
        for key_frame in self.poses:
            # Get relative PoseBone with minimised rotation
            pose_bone = self.poses[key_frame].pose_bones[bone_name].relative(
                self.original_pose.pose_bones[bone_name]
            )
            pose_bone = PoseBone(
                name=pose_bone.name, scale=pose_bone.scale,
                location=pose_bone.location, rotation=_pick_closest_rotation(
                    pose_bone.rotation, prev_pose_bone.rotation,
                    self.original_pose.pose_bones[bone_name].rotation
                )
            )
            timestamp = str(round((key_frame-1) / self.fps, 4))
            poses.append({
                't': timestamp,
                'loc': get_vect_json(pose_bone.location),
                'scl': get_vect_json(pose_bone.scale),
                'rot': get_vect_json(pose_bone.rotation),
            })
            # Update prev pose
            prev_pose_bone = pose_bone

        # Filter unnecessary frames and add them to bone
        if not poses:  # If empty return empty animation
            return {'position': {}, 'rotation': {}, 'scale': {}}
        if self.single_frame:  # Returning single frame pose is easier
            return {  # dictionary populated with 0 timestamp frame
                'position': poses[0]['loc'],
                'rotation': poses[0]['rot'],
                'scale': poses[0]['scl']}
        bone: Dict = {  # dictionary populated with 0 timestamp frame
            'position': {poses[0]['t']: poses[0]['loc']},
            'rotation': {poses[0]['t']: poses[0]['rot']},
            'scale': {poses[0]['t']: poses[0]['scl']},
        }
        # iterate in threes (previous, current , next)
        prev, curr, next_ = tee(poses, 3)
        for prv, crr, nxt in zip(
                prev, islice(curr, 1, None), islice(next_, 2, None)
        ):
            if prv['scl'] != crr['scl'] or crr['scl'] != nxt['scl']:
                bone['scale'][crr['t']] = crr['scl']

            if prv['loc'] != crr['loc'] or crr['loc'] != nxt['loc']:
                bone['position'][crr['t']] = crr['loc']

            if prv['rot'] != crr['rot'] or crr['rot'] != nxt['rot']:
                bone['rotation'][crr['t']] = crr['rot']
        # Add last element unless there is only one (in which case it's already
        # added)
        if len(poses) > 1:
            bone['scale'][poses[-1]['t']] = poses[-1]['scl']
            bone['position'][poses[-1]['t']] = poses[-1]['loc']
            bone['rotation'][poses[-1]['t']] = poses[-1]['rot']
        return bone
