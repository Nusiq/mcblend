
# src.operator_func

Functions used directly by the blender operators.


## export_model
```python
export_model(context: Context)
```

Uses context.selected_objects to create and return dictionary with
minecraft model.

Additionally returns a string with error message or an empty string when
there are no errors.


## export_animation
```python
export_animation(context: Context,
                 old_dict: typing.Union[typing.Dict, NoneType])
```

Uses context.selected_objects to create and return dictionary with
minecraft animation.
old_dict is an optional value with dictionary that contains the content of
animation file. This function validates the dictionary and tries to use it
while exporting the animation.


## set_uvs
```python
set_uvs(context: Context)
```

Used by the operator that sets UV. Calculates the UV-map for selected
objects.

Depending on operator configuration this function can:
- add/edit mc_uv property to the objects.
- add new Blender UV (to match it to mc_uvs).
- removes old Blender UV


## set_inflate
```python
set_inflate(context: Context, inflate: float, mode: str)
```

Adds mc_inflate property to objects and changes their dimensions. Returns
the number of edited objects.
Returns the number of edited objects.


## round_dimensions
```python
round_dimensions(context: Context)
```

Rounds dimensions of selected objects. Returns the number of edited
objects.


## import_model
```python
import_model(data: typing.Dict, geometry_name: str, context: Context)
```

Import and build model from JSON file. Returns success result value (bool).

