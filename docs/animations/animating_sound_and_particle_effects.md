# Animating sound and particle effects

The sound effects and particle effects are animated with the use of events. You can define events in the `Mcblend: Animation Events` menu in `Scene Properties`. One event can contain multiple particle and sound effects. The effects are not visible in the animation preview in Blender. They only add some information to the exported animation.

Events can be attached to the animation by adding markers in the timeline with the name of the event. You can trigger the same event multiple times in the animation by adding multiple timeline markers with the same name.

Timeline markers that do not have a matching event name are ignored when exporting the animation and serve the same purpose as any other timeline marker in Blender.

A timeline with timeline markers for events:
![](/img/animations/effect_animation.png)