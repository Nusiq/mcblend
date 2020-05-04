
# mcblend.operator_func.common

Functions and objects shared between other modules of Mcblend.


## MCObjType
```python
MCObjType(cls, value, names=None, *, module, qualname, type, start)
```

Used to mark what type of minecraft object should be created from a mesh in
blender.

- CUBE - is a cube which is a part of a bone.
- BONE - is just a bone without cubes in it.
- BOTH - is a bone with a cube inside.


## ObjectId
```python
ObjectId(_cls, name: str, bone_name: str)
```

Unique ID of a mesh, empty or a bone.

For meshes and empties it's bone_name is just an empty string and the
name is the name of the object.

For bones the ID uses both the name (armature name) and bone name
which is the name of the bone contained in the bone.


## ObjectMcProperties
```python
ObjectMcProperties(
  self, thisobj_id: ObjectId, thisobj: Object,
  mcparent: typing.Union[mcblend.operator_func.common.ObjectId, NoneType],
  mcchildren: typing.List[mcblend.operator_func.common.ObjectId],
  mctype: MCObjType)
```

Wrapper class for the objects used by the addon to create some parts of
the minecraft model. This class can be used to containg bpy_types.Object
and bones from the armature to provide for them similar functionallity.


## ObjectMcTransformations
```python
ObjectMcTransformations(_cls, location: <built-in function array>,
                        scale: <built-in function array>,
                        rotation: <built-in function array>)
```

Temporary properties of transformations of an object (mesh or empty)
for the minecraft animation. Changes in these values over the frames of the
animation are used to calculate the values for minecraft animation json.


## McConvertibleType
```python
McConvertibleType(cls,
                  value,
                  names=None,
                  *,
                  module,
                  qualname,
                  type,
                  start)
```

Type of an object in blender that can be converted into something in
minecraft model.


## get_vect_json
```python
get_vect_json(arr: typing.Iterable)
```

Changes the iterable whith numbers into basic python list of floats.
Values from the original iterable are rounded to the 3rd deimal
digit. If value is interer changes it to integer type to skip writing
unnecesary zero decimal.


## get_local_matrix
```python
get_local_matrix(parent_world_matrix: Matrix,
                 child_world_matrix: Matrix)
```

Returns translation matrix of child in relation to parent.
In space defined by parent translation matrix.


## get_mcrotation
```python
get_mcrotation(
  child_matrix: Matrix,
  parent_matrix: typing.Union[mathutils.Matrix, NoneType] = None)
```

Returns the rotation of mcbone.
- child_matrix - the matrix_world of the object that represents the mcbone
- parent_matrix - optional. the matrix_world of the object that is a
  mcparent (custom parenting) of the object that represents the mcbone.


## get_mcube_size
```python
get_mcube_size(objprop: ObjectMcProperties)
```

Returns cube size based on the bounding box of an object.
The returned value is moved by the translation matrix from "translation"


## get_mccube_position
```python
get_mccube_position(objprop: ObjectMcProperties)
```
Returns cube position based on the bounding box of an object.

## get_mcpivot
```python
get_mcpivot(
    objprop: ObjectMcProperties, object_properties:
    typing.Dict[mcblend.operator_func.common.ObjectId, mcblend.operator_func.common.ObjectMcProperties]
)
```

Returns the pivot point of a mcbone (or mccube).
- objprop - the properties of this mcbone/mccube
- object_properties - the properties of all of the mccubes and mcbones in
  minecraft model


## loop_objects
```python
loop_objects(objects: typing.List)
```

Loops over the empties, meshes and armature objects and yields them and
their ids.
If object is an armatre than it loops over every bone and yields the
armature and the id of the bone.


## get_parent_mc_bone
```python
get_parent_mc_bone(obj: Object)
```

Goes up through the ancesstors of the bpy_types.Object which
will be changed into mccube during model exporting and tries to find the
mcbone that contains this mccube.

Returns the ObjectId of the ancesstor.


## get_name_conflicts
```python
get_name_conflicts(
    object_properties:
    typing.Dict[mcblend.operator_func.common.ObjectId, mcblend.operator_func.common.ObjectMcProperties]
)
```

Looks through the object_properties dictionary and tries to find name
conflicts. Returns empty string (when there are no conflicts) or a name
which is used by multiple object.


## get_object_mcproperties
```python
get_object_mcproperties(context: Context)
```

Loops through context.selected_objects and returns a dictionary with custom
properties of mcobjects. Returned dictionary uses the ObjectId of the
objects as keys and the custom properties as values.


## pick_closest_rotation
```python
pick_closest_rotation(
  modify: ndarray,
  close_to: ndarray,
  original_rotation: typing.Union[numpy.ndarray, NoneType] = None)
```

Takes two numpy.arrays that represent rotation in
euler rotation mode (using degrees). Modifies the
values of 'modify' vector to get different representations
of the same rotation. Picks the vector which is the
closest to 'close_to' vector (euclidean distance).

original_rotation is added specificly to fix some issues with bones
which were rotated before the animation. Issue [`25`](#25) describes the problem
in detail.

