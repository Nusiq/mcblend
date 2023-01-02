# Creating animations from scratch

In this section, you will learn how to create animations in Mcblend from scratch. It is assumed that the reader already knows how to make and export models in Mcblend. We will start with a simple model that has a single bone and a single cube connected to it.

## Creating movement animation

1. Select the armature
2. Go to the `Mcblend: Animations` panel under the `Object Properties` tab and click the `New Animation` button

![](/img/animations/creating_animation_new_animation_button.png)

3. Rename the animation to `my_cube.movement`. It is a good practice to name the animations using the pattern: `<model_name>.<animation_name>`. In our case, the model is called `my_cube`.
4. Select the `Skip rest poses` checkbox (the configuration of the animation is explained later in the documentation)
5. In the action editor, press the `New` button to create a new action for the armature. You can rename the action to the same name as the animation, but it is not necessary. It will be easier to find the action in the action editor if you do so.

![](/img/animations/creating_animation_animation_configuration.png)

6. Add a keyframe to location, rotation, and scale at frame 0. This will be the rest pose of the animation. The keyframe should be added in Pose mode. You should add the keyframe to all bones in the armature. In this case, we only have one bone. Select all of the bones by pressing `A` while in `Pose mode` and hovering over the 3D viewport. Then, press `I` to add the keyframe and select the `Location, Rotation & Scale` option.

![](/img/animations/creating_animation_new_adding_keyframe.png)

7. On the first frame, without moving the cube, add a keyframe to the location only.
8. Move the timeline and move the cube to the desired position, then add a keyframe to the location only.
9. Move the timeline to the last frame and reset the cube to the rest pose, then add a keyframe to the location only.
10. At this point, you should have an animation of a moving cube. Only the location of the cube should be animated.

![](/img/animations/creating_animation_ready_move_animation.png)

## Managing animations using the NLA editor

In this section, we will learn how to use the NLA editor to manage animations in Mcblend. This includes the ability to combine multiple actions into a single animation.

To create a new animation, return to Object mode and press the `New Animation` button. If you try to create a new animation while an active action is present, you will receive a warning to either "Stash or Push Down" the active action.

![](/img/animations/creating_animation_stash_or_push_down_warning.png)

1. In the `Action Editor`, press the `Push Down` button to add the animation to the NLA track and activate it. The Stash button does not activate the animation.


![](/img/animations/creating_animation_push_down_button.png)

2. To create a new animation, repeat the steps from the previous section, naming it `my_cube.scale` and creating a new action for it. Note that the action from the previous animation is still active in the NLA editor. You can disable it to prevent it from affecting the new animation.

![](/img/animations/creating_animation_animation_configuration_1.png)

3. Add keyframes as in the previous section, including a rest pose at keyframe 0. This time, do not add a keyframe to the location at frame 0 (we want to use the location animation from the previous animation). Instead, animate the scale of the cube. Remember to animate bones in Pose mode, not the armature.
4. If configured correctly, the currently open action should change the scale of the cube while the action from the NLA track makes it move.

![](/img/animations/creating_animation_ready_scale_animation.png)

5. `Push down` the animation to add it to the NLA track. You should now have two active NLA tracks. You can disable an animation from the NLA track by pressing the checkbox next to the track name.
6. You can rename the tracks for easier identification, but be aware that Mcblend remembers tracks by their names. Renaming a track used by an animation will unlink it from the animations that use it.


7. To switch between animations in the `Mcblend: Animations` panel, use the `Select Animation` dropdown list while in `Object Mode`. Keep in mind that switching the animation also activates different NLA tracks in the NLA editor. In this example, we want the `Move` animation to only affect the location of the cube, while the `Scale` animation should influence both movement and scale (using both NLA tracks). To accomplish this, the `Move` animation should have only the `Move` track active, and the `Scale` animation should have both the `Move` and `Scale` tracks active.

![](/img/animations/creating_animation_final_config_scale.png)

![](/img/animations/creating_animation_final_config_move.png)

## Exporting animations

To export animations in Mcblend, follow these steps:

1. Select the desired animation in the `Mcblend: Animations panel`, found under the `Object Properties` tab.
2. Choose `File > Export > Export Bedrock Animation` from the menu.
3. Select the location where you would like to save the exported animation file.
4. Repeat these steps to export any additional animations. Note that exporting multiple animations to the same file will not overwrite the previous animation - both will be included in the same file.

![](/img/animations/creating_animation_animation_export_animation.png)