# Exporting Animations

This section explains how to export animations from Mcblend and mentions some additional settings that can be configured before exporting.

To export an animation, you first need to create one using the `New animation` button in the `Object Properties` panel under the `Mcblend: Animations` tab. This tab is only visible when an armature is selected. If you want to remove an animation, use the `Remove this animation` button.

Before exporting the animation, you can configure some additional settings in the `Object Properties` panel. The `Skip rest poses` checkbox allows you to create more optimized animations by skipping unnecessary keyframes that don't affect the pose of the model. The `Export as pose` option changes the animation to a single pose, creating a looped animation with a single frame.

The `Override previous animation`, `Loop`, and `Anim Time update` settings are properties of Minecraft animations and are directly exported to the file. They have no effect on Mcblend. The `Frame start` and `Frame end` settings determine the range of frames that will be exported to the animation.

Exporting the animation is similar to exporting a model, as explained in the "Creating animations from scratch" documentation page. Simply go to `File > Export > Export Bedrock Animation` and select the export path.