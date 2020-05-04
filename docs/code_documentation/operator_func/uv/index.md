
# mcblend.operator_func.uv

Functions related to creating UV map.


## get_uv_face
```python
get_uv_face(objprop: ObjectMcProperties, face_name: str)
```

- objprop - the properties of the object
- face_name - decides which face should be returned

Returns a dictionary with list of integer indices of loops which are part
of a UV of a cube.


## set_uv
```python
set_uv(objprop: ObjectMcProperties, uv_face: typing.Dict[str, int],
       crds: typing.Tuple[float, float],
       size: typing.Tuple[float, float], mirror_y: bool, mirror_x: bool)
```

- objprop - the data of the object
- uv_face - the dictionary with loop indices used to define which loops
  of the uv should be moved.
- crds - value from 0 to 1 the position of the bottom left loop on blender
  uv mapping coordinates system.
- size - value from 0 to 1 the size of the rectangle in blender uv mapping
  coordinates system.


## set_cube_uv
```python
set_cube_uv(objprop: ObjectMcProperties, uv: typing.Tuple[float, float],
            width: float, depth: float, height: float,
            texture_width: int, texture_height: int)
```

- objprop - properties of the object
- uv - value from 0 to 1 the position of the bottom left loop on blender
  uv mapping coordinates system.
- width - value from 0 to 1 the width of the cube converted into blender
  uv mapping coordinates system.
- depth - value from 0 to 1 the depth of the cube converted into blender
  uv mapping coordinates system.
- height - value from 0 to 1 the height of the cube converted into blender
  uv mapping coordinates system.
- texture_width  - texture_width for scaling
- texture_height  - texture_height for scaling
Sets the UV faces of a mesh object that represents a mccube in the same
patter as minecraft UV mapping.


## UvCorner
```python
UvCorner(cls, value, names=None, *, module, qualname, type, start)
```

During UV-mapping UVBox objects use this enum combined with coordinates
to suggest possible positions to check for other UvBoxes (to find free
space on the texture).

For example a pair ((1, 2), UvCorner.TOP_RIGHT) represents a suggestion
that UvBoxes that look for free space should try a position in which
their TOP_RIGHT corner is at the (1, 2) pixel.

Members:
- TOP_RIGHT
- TOP_LEFT
- BOTTOM_RIGHT
- BOTTOM_LEFT


## UvBox
```python
UvBox(self,
      size: typing.Tuple[int, int],
      uv: typing.Tuple[int, int] = None)
```
Rectangular space that is mapped or needs mapping on the texture.

## UvMcCube
```python
UvMcCube(self,
         width: int,
         depth: int,
         height: int,
         uv: typing.Tuple[int, int] = None)
```

Six UvBoxes grouped together to represent space on the texture need for
UV mapping of single cube in minecraft model.


## plan_uv
```python
plan_uv(boxes: typing.List[mcblend.operator_func.uv.UvMcCube],
        width: int,
        height: int = None)
```

Plans UVs for all of the boxes on the list. The size of the texture is
limited by width and optionally by height.

Returns success result.


## get_uv_mc_cubes
```python
get_uv_mc_cubes(
  objprops: typing.List[mcblend.operator_func.common.ObjectMcProperties],
  read_existing_uvs)
```

Returns name-uv_mc_cube dictionary with uv_mc_cubes of selected objects.

- objprops - list of the properties of the objects
- read_existing_uvs - if set to True it will try to read the custom
  properties of the `obj` to read its UV values.

