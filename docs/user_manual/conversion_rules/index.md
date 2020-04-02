# Conversion rules
There are no directly equivalent objects in blender models to Minecraft bedrock
edition models. Mcblend uses set of rules to decide which parts of the model
shoud be converted into bones, locators or cubes in Minecraft model.

1. An empty or mesh with custom `is_mc_bone` property always creates a
  a bone or a bone with cube respectivly.
2. A bone is converted into a bone unless it has no children and no
  parents. In this case it isn't converted at all. This behavior is to prevent
  the conversions of inverse kinematics bones.
3. An empty becomes a bone unless it has a parent but no children. In this case
  it creates a locator.
4. Mesh without parent becomes a bone with a cube inside it. Mesh with a parent
  becomes a cube.

### The same set of rules as a table

||`is_mc_bone` property|no parent, no children| parent, no children|no parent,children|parent and children|
|---|---|---|---|---|---|
|__Bone__ |N/A*|NONE|bone|bone|bone|
|__Empty__|bone|bone|locator|bone|bone|
|__Mesh__ |bone & cube|bone & cube|cube| bone & cube|cube|

*_bones can't have `has_mc_bone` property_
