
# mcblend.operator_func.importer

Object representation of Minecraft model JSON files and data validation


## get_path
```python
get_path(jsonable: typing.Dict,
         path: typing.List[typing.Union[str, int]])
```

Goes through a dictionary and checks its structure. Returns an object
from given path and success result.
If path is invalid returns None and False. For valid paths returns
object the object and True.


## assert_is_vector
```python
assert_is_vector(vect: typing.Any,
                 length: int,
                 types: typing.Tuple,
                 msg: str = '')
```

Asserts that the "vect" is "length" long vector and all of the items
in the vector are instances of types from types list.


## assert_is_model
```python
assert_is_model(model: typing.Any)
```

Asserts that the input dictionary is a valid model file.


## ImportLocator
```python
ImportLocator(self, name: str,
              position: typing.Tuple[float, float, float])
```
Represents minecraft locator during import operation.

## ImportCube
```python
ImportCube(self, uv: typing.Tuple[int, int], mirror: bool,
           origin: typing.Tuple[float, float, float],
           pivot: typing.Tuple[float, float, float],
           size: typing.Tuple[float, float, float],
           rotation: typing.Tuple[float, float, float])
```
Represents minecraft cube during import operation.

## ImportBone
```python
ImportBone(
  self, name: str, parent: typing.Union[str, NoneType],
  pivot: typing.Tuple[float, float, float],
  rotation: typing.Tuple[float, float, float],
  cubes: typing.List[mcblend.operator_func.importer.ImportCube],
  locators: typing.List[mcblend.operator_func.importer.ImportLocator])
```
Represents minecraft bone during import operation.

## ImportGeometry
```python
ImportGeometry(
  self, identifier: str, texture_width: int, texture_height: int,
  bones: typing.Dict[str, mcblend.operator_func.importer.ImportBone])
```
Represents whole minecraft geometry during import operation.

## load_model
```python
load_model(data: typing.Dict, geometry_name: str = '')
```

Returns ImportGeometry object with all of the data loaded from data dict.
The data dict is a dictionary representaiton of the JSON file with
Minecraft model. Doesn't validates the input. Use assert_is_model for that.

geometry_name is a name of the geometry to load. This argument is optional
if not specified or epmty string only the first model is imported.


## build_geometry
```python
build_geometry(geometry: ImportGeometry, context: Context)
```
Builds the geometry in Blenders 3D space
