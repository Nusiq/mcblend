
# src.operator_func.model

Functions related to exporting models.


## get_mcmodel_json
```python
get_mcmodel_json(model_name: str, mc_bones: typing.List[typing.Dict],
                 texture_width: int, texture_height: int)
```

Returns the dictionary that represents JSON file for exporting the model


## get_mcbone_json
```python
get_mcbone_json(
    boneprop: ObjectMcProperties,
    cubeprops: typing.List[src.operator_func.common.ObjectMcProperties],
    locatorprops: typing.List[src.operator_func.common.ObjectMcProperties],
    object_properties:
    typing.Dict[src.operator_func.common.ObjectId, src.operator_func.common.ObjectMcProperties]
)
```

- boneprop - the main object that represents the bone.
- cubeprops - the list of objects that represent the cubes that belong to
  the bone. If the "boneprop" is one of the cubes it should be included on
  the list.
- locatorprops - the list of objects that represent the locators that
  belong to the bone.
- object_properties - the properties of all of the mccubes and mcbones in
  minecraft model.

Returns the dictionary that represents a single mcbone in json file
of model.

