# Importing models from a file

In this page, you will learn how to import a Minecraft model into Mcblend from a file. This is useful if you want to modify an existing model or if you have a custom model created outside of Mcblend.

```{note}
It is recommended to [import models from resource](/modeling/importing_models_from_rp) packs whenever possible, as it will automatically set up the texture and render controllers for you using the information from the resource pack. You can learn how to import models from resource packs in the next page.
```

## Importing the model

To import a Minecraft model from a file, go to `File > Import > Import Bedrock Model`. This will open a file browser where you can select the model file. The model files usually have the `.geo.json` extension.

After selecting the file, the model will be imported into your Blender scene. The model will be represented by a collection of cubes parented to an armature.

![](/img/modeling/import_model.png)

If the model file contains multiple models, you should specify the name of the model you want to import. You may omit the `geometry.` prefix. Otherwise, the first model in the list will be imported.

![](/img/modeling/import_model_dialog.png)

## Importing and applying the texture to the model

To import the texture and apply it to your model, you'll need to use the Render controllers feature in Mcblend. These work in a similar way to the render controllers in Minecraft, defining which textures should be used by the model, which cubes they should be applied to, and the properties of the material of each cube.

To import and apply the texture to your model:

1. Select the armature object in `Object Mode` and go to the `Mcblend: Render Controllers` tab in `Object Properties`.
2. Press the `Add Render Controller` button to create a new render controller.
3. Click on the folder icon next to the `Texture` field and select the texture file using the file browser.
4. Press the `Apply Material` button to apply the material to the model.

You can view the textures on the model by switching the viewing mode in the 3D viewport to Material Preview.

![](/img/modeling/import_model_texture.png)
