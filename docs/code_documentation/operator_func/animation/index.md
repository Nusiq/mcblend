
# mcblend.operator_func.animation

Functions related to exporting animations.


## AnimationProperties
```python
AnimationProperties(_cls, name: str, length: float, loop_animation: bool,
                    anim_time_update: str)
```

Data class that represents configuration of animation
- name - name of the animation
- length - the length of animation (seconds)
- loop_animation - Loops the animation
- anim_time_update - Adds anim_time_update property to the animation.


## get_mcanimation_json
```python
get_mcanimation_json(
  animation_properties: AnimationProperties,
  bone_data:
    typing.Dict[mcblend.operator_func.common.ObjectId, typing.Dict[str, typing.List[typing.Dict]]],
  object_properties:
    typing.Dict[mcblend.operator_func.common.ObjectId, mcblend.operator_func.common.ObjectMcProperties],
  extend_json: typing.Union[typing.Dict, NoneType] = None)
```

- animation_properties - basic properties of the animation
- bone_data - Dictionary filled with dictionaries that describe postition,
  rotation and scale for each frame (uses bone ObjectId as a key).
- object_properties - a dictionary with relations between object created by
get_object_mcproperties() funciton.
- extend_json - optional argument with a dictionary with content of old
file with animation. If this parameter is None or has invalid structure
a new dictionary is created.

Returns a dictionary with animation for minecraft entity. The animation is
optimised. Unnecessary keyframes from bone_data are not used in the result
dictionary.


## get_transformations
```python
get_transformations(
    object_properties:
    typing.Dict[mcblend.operator_func.common.ObjectId, mcblend.operator_func.common.ObjectMcProperties]
)
```

Loops over object_properties and returns the dictionary with
information about transformations of every bone.

Returns a dicionary with name of the object as keys and transformation
properties as values.


## get_mctranslations
```python
get_mctranslations(parent_rot: ndarray, child_rot: ndarray,
                   parent_scale: ndarray, child_scale: ndarray,
                   parent_loc: ndarray, child_loc: ndarray)
```

Compares original transformations with new transformations of an object
to return location, rotation and scale values (in this order) that can be
used by the dictionary used for exporting the animation data to minecraft
format.


## get_next_keyframe
```python
get_next_keyframe(context: Context)
```

Returns the index of next keyframe from all of selected objects.
Returns None if there is no more keyframes to chose.

