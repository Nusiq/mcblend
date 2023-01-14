# Attachable item models

This tutorial will show you how to adjust the position of an attachable item so that it fits into the hand of a player. However, it does not cover the process of creating or adding the model into the game. If you need a more comprehensive guide, you can refer to the following links:

- [https://mcblend.readthedocs.io/en/v10.0.0/advanced_tutorials/attachables_and_1st_person_animations/](https://mcblend.readthedocs.io/en/v10.0.0/advanced_tutorials/attachables_and_1st_person_animations/) is a tutorial from an older version of Mcblend's documentation that explains how to create, animate, and add an attachable item to the game. However, it utilizes a removed feature, the `World origin` property of animations, which has been replaced by the `Model origin` property of models.
- [https://wiki.bedrock.dev/items/attachables.html](https://wiki.bedrock.dev/items/attachables.html) is a tutorial from the Bedrock Wiki (created by the Minecraft Add-on making community) that explains how to create attachable items and add them to the game, but it does not use Mcblend.

## Positioning the model

This tutorial uses the Mcblend template project, which you can learn more about in the [dedicated section of the documentation](/tips_and_tricks/mcblend_blender_template.md). The Mcblend template project is specially designed to work with Minecraft models, and it also includes the player model, which can be useful when animating the attachable item later on. You don't have to use the template, but it's recommended because you won't have to set up the project from scratch.

![](/img/tips_and_tricks/template_project_menu.png)

To begin working on the attachable model, we can make the player model invisible for the time being.

![](/img/modeling/attachable_hide_player.png)

The model of the attachable should be oriented in a way that corresponds to the player's hand. In this example, the tutorial model is a hammer. The player model is facing forward, and the player is holding their hands down. In this posture, it is natural to hold the hammer with the head of the hammer facing forward.

![](/img/modeling/attachable_unpositioned_model.png)

When the model is complete and you are satisfied with its appearance, you can proceed to the next steps to use it as an attachable item in Minecraft. Note that attachable models have a 1.5m offset that must be taken into consideration when creating them. To ensure proper positioning, go to `Pose Mode` and move all of the bones of the model 1.5m up. If you're using the Mcblend template project, the world scale is set to 16x (to match Minecraft modeling size units), so you should move the model 24m up. This will ensure that the model is correctly positioned slightly below the player's head. Once the model is in the correct position, apply the pose as the rest pose by selecting all bones in `Pose Mode`, pressing `F3`, and finding the `Apply Pose as Rest Pose` operation. This operation sets the positions and rotations of the bones as the default position of the model. It is important to ensure that the pivot point of the armature remains at the origin of the world, which can be seen as a little orange dot in the 3D view when in `Object Mode` and the armature is selected.

![](/img/modeling/attachable_apply_pose.png)

![](/img/modeling/attachable_applied_pose.png)

To make adjusting the position of the attachable model easier, you can add a `Child Of` constraint to its armature. This will parent the armature of the attachable model to the armature of the player model, allowing you to see how the model will appear in-game while you make adjustments.

To add the constraint:
1. Go to `Object Mode` and select the armature of the attachable model.
2. In the `Constraints` tab, add a new constraint by clicking on the `Add Object Constraint` button and selecting `Child Of`.
3. In the `Child Of` constraint settings, set the `Target` to be the armature of the player model and the `Bone` to be `rightItem`.

![](/img/modeling/attachable_add_child_of.png)

After adding the constraint, press the `Clear Inverse` button. This will place the attachable model in a position above the player's hand, with a 1.5m offset.

![](/img/modeling/attachable_child_of_setup.png)

To position the attachable model correctly, you should move the armature of the model 1.5m down in `Object Mode`. This will place the item roughly in the right position. You can then fine-tune the position further by adjusting the bones in `Pose Mode`. After you've finished adjusting the position, apply the pose again (as described in previous steps of this tutorial). The final position of the origin of the armature should be 1.5m below the `rightItem` bone of the player model and the item should be positioned in the player's hand in a believable and natural way.

![](/img/modeling/attachable_apply_pose_2.png)

To make your attachable item functional in Minecraft, you must add a special property to the root bone of the model. In this case, the model has only one bone. This property is called "binding" and it should contain the name of the bone that the attachable should be attached to. To add this property, you will use the Molang expression. The proper format of a Molang expression for a bone named `rightItem` is `'rightitem'` (with single quotes and all letters in lowercase). To set this property in Mcblend, go to `Pose Mode`, select the root bone of the armature of the attachable, select the `Object Properties`, and in the `Mcblend: Bone Properties` set the `Binding` property to `'rightitem'`.

![](/img/modeling/attachable_binding.png)

The player model in the template project has an additional animation that allows you to preview how the attachable item will be held in the game in 1st person mode. This can be useful as a reference when creating animations for the attachable item.

![](/img/modeling/attachable_first_person_preview.png)

Once you have the attachable model in the desired position, you can animate both the player model and the attachable simultaneously. The process of creating animations for attachables is no different than creating animations for any other model. The key is to pay attention to the armature that you have selected while exporting the model or animation. If the armature of the player is selected, Mcblend will export a model/animation for the player. If the armature of the attachable is selected, Mcblend will export a model/animation for the attachable.

When exporting the attachable, ensure that the `Model Origin` in the `Object Properties > Mcblend: Model Properties` is set to `armature`. This is the default setting, so unless you have changed it, you don't need to worry about it. This setting ensures that all animations of the armature are relative to its origin and not the world, so the movement of the hand holding the item is not exported as part of the animation of the attachable.
