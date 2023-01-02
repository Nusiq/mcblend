# Essential concepts for creating animations in Mcblend

This page covers essential concepts to consider when creating animations using Mcblend. It is recommended that you read through this information before beginning to animate with Mcblend.

## Recomended workspace layout

Animations in Mcblend are based on Non Linear Animation (NLA) tracks. A single animation can contain multiple NLA tracks running at the same time, each track containing action strips. While working with animations in Mcblend, you'll be using the NLA tracks and action editor frequently. It is recommended to set up a workspace layout like the one shown in the image below for working with animations in Mcblend.

The editor on the left side of the screen is the `Nonlinear Animation` editor. The editor at the bottom is the `Dope Sheet` editor set to the `Action editor` mode.

![](/img/animations/animation_editing_workspace.png)

## Animation as a sequence of poses

During the export process, the exported data for animations is not solely based on the NLA tracks. Mcblend exports the same animation that is visible in the 3D viewport during the preview, which can be affected by various factors such as constraints, inverse kinematics, and physics. This means that some bones in the model may not be animated in the NLA tracks, but they will be animated in the exported animation due to the influence of other factors that affect their movement. The keyframe times for the animations are based on the keyframe times in the NLA tracks, but not at the bone level. Essentially, if there is any keyframe at a certain time, Mcblend compares the pose of the entire model at that time to the pose of the model at the previous keyframe. If the pose is different for a given bone, Mcblend will add a keyframe for that bone to the exported animation. Any pose changes that occur between keyframes are not checked, which can lead to unexpected results, particularly when using physics, which often generates complex movement that requires many keyframes to be animated correctly.

## Frame 0

In Mcblend, animations are based on comparing the poses of the model at different times. To do this, there must be a frame that defines the base pose of the model. This frame is frame 0 (it's 1 frame before the first frame and is technically not a part of the animation). Frame 0 has a special role in Mcblend and the model should be in its base pose during this frame. If it is not, the animations will not export properly. Frame 0 is also the frame used during the `Export Bedrock Model` operation.
