# Essential concepts for creating animations in Mcblend

This page covers essential concepts to consider when creating animations using Mcblend. It is recommended that you read through this information before beginning to animate with Mcblend.

## Recomended workspace layout

Animations in Mcblend are based on Non Linear Animation (NLA) tracks. A single animation can contain multiple NLA tracks running at the same time, each track containing action strips. While working with animations in Mcblend, you'll be using the NLA tracks and action editor frequently. It is recommended to set up a workspace layout like the one shown in the image below for working with animations in Mcblend.

The editor on the left side of the screen is the `Nonlinear Animation` editor. The editor at the bottom is the `Dope Sheet` editor set to the `Action editor` mode.

![](/img/animations/animation_editing_workspace.png)

## Animation as a sequence of poses

During the export process, the exported data for animations is not solely based on the NLA tracks. Mcblend exports the same animation that is visible in the 3D viewport during the preview, which can be affected by various factors such as constraints, inverse kinematics, and physics. This means that some bones in the model may not be animated in the NLA tracks, but they will be animated in the exported animation due to the influence of other factors that affect their movement. The keyframe times for the animations are based on the keyframe times in the NLA tracks, but not at the bone level. Essentially, if there is any keyframe at a certain time, Mcblend compares the pose of the entire model at that time to the pose of the model at the previous keyframe. If the pose is different for a given bone, Mcblend will add a keyframe for that bone to the exported animation. Any pose changes that occur between keyframes are not checked, which can lead to unexpected results, particularly when using physics, which often generates complex movement that requires many keyframes to be animated correctly.

## Stepped, Linear, and Smooth Interpolation

Minecraft supports three types of frames: stepped, linear, and smooth. Blender offers corresponding interpolation modes: constant, linear, and Bézier.

Since Mcblend understands animations as a sequence of poses (as described in the previous section), understanding how Blender's interpolation modes affect the exported animation is crucial.

Mcblend uses a simple rule - if it needs to add a keyframe for a bone at a certain time and that bone doesn't have a keyframe at that time, it will use the same interpolation mode as the most recent keyframe for that bone. If there is no previous keyframe, Mcblend will use linear interpolation.

```{note}
Example:
![](/img/animations/essential_concepts_timeline.png)
Let's say that in the image above, `bone_2` uses constant interpolation on frame 1. At frame 10 (marked "New Pose"), `bone_1` has a keyframe. If something moves `bone_2` between frames 1 and 10, Mcblend will export that movement as stepped interpolation because the most recent keyframe for `bone_2` was set to constant interpolation.
```

This behavior can cause unexpected results when using stepped or smooth interpolation. To ensure predictable animations, it's generally best to use linear interpolation unless a different mode is necessary.

```{warning}
Bézier interpolation in Blender does not exactly match smooth frames in Minecraft, which use a Catmull-Rom spline. For a similar effect in Blender's preview, use Bézier interpolation with "automatic" handle types.

Note that the Bézier interpolation in Blender is the default. It's good to build a habit of changing it to linear for all keyframes when working with Mcblend.
```

## Frame 0

In Mcblend, animations are based on comparing the poses of the model at different times. To do this, there must be a frame that defines the base pose of the model. This frame is frame 0 (it's 1 frame before the first frame and is technically not a part of the animation). Frame 0 has a special role in Mcblend and the model should be in its base pose during this frame. If it is not, the animations will not export properly. Frame 0 is also the frame used during the `Export Bedrock Model` operation.
