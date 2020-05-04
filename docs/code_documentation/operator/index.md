
# mcblend.operator

This module contains all of the operators.


## OBJECT_OT_NusiqMcblendExportOperator
```python
OBJECT_OT_NusiqMcblendExportOperator(cls, *args, **kw)
```
Operator used for exporting minecraft models from blender

## menu_func_nusiq_mcblend_export
```python
menu_func_nusiq_mcblend_export(self, context)
```
'Helper function adds export model operator to the menu.

## OBJECT_OT_NusiqMcblendExportAnimationOperator
```python
OBJECT_OT_NusiqMcblendExportAnimationOperator(cls, *args, **kw)
```
Operator used for exporting minecraft animations from blender

## menu_func_nusiq_mcblend_export_animation
```python
menu_func_nusiq_mcblend_export_animation(self, context)
```
'Helper function adds export animation operator to the menu.

## OBJECT_OT_NusiqMcblendMapUvOperator
```python
OBJECT_OT_NusiqMcblendMapUvOperator(cls, *args, **kw)
```
Operator used for creating UV-mapping for minecraft model.

## OBJECT_OT_NusiqMcblendUvGroupOperator
```python
OBJECT_OT_NusiqMcblendUvGroupOperator(cls, *args, **kw)
```

Operator used for setting custom property called mc_uv_group for selected
objects.


## OBJECT_OT_NusiqMcblendToggleMcMirrorOperator
```python
OBJECT_OT_NusiqMcblendToggleMcMirrorOperator(cls, *args, **kw)
```

Operator used for toggling custom property called mc_mirror for selected
objects


## OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator
```python
OBJECT_OT_NusiqMcblendToggleMcIsBoneOperator(cls, *args, **kw)
```

Operator used for toggling custom property called mc_is_bone for selected
objects.


## OBJECT_OT_NusiqMcblendSetInflateOperator
```python
OBJECT_OT_NusiqMcblendSetInflateOperator(cls, *args, **kw)
```

Operator used for setting the inflate value of selected objects. It changes
the dimensions of selected object and adds custom property called
mc_inflate.


## OBJECT_OT_NusiqMcblendRoundDimensionsOperator
```python
OBJECT_OT_NusiqMcblendRoundDimensionsOperator(cls, *args, **kw)
```

Operator used for rounding the values of dimensions.


## OBJECT_OT_NusiqMcblendImport
```python
OBJECT_OT_NusiqMcblendImport(cls, *args, **kw)
```
Operator used for importiong minecraft models to blender

## menu_func_nusiq_mcblend_import
```python
menu_func_nusiq_mcblend_import(self, context)
```
'Helper function adds import model operator to the menu.
