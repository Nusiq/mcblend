# Conversion rules
There are no directly equivalent objects in blender models to Minecraft models.
Mcblend uses a set of rules to decide which parts of the model
should be turned into bone, locator or cube.

!!! note
    The best way to learn what kinds of object are converted to what is trial
    and error. You can use the set of rules below if you notice something
    unexpected.

1. An empty or mesh with custom
  [_export as bone_](../basic_operators/#toggle-export-as-bones) property
  always creates a a bone or a bone with cube, respectively.
2. A Blender bone is converted into a Minecraft bone unless it has no children
  and no parents. In this case it isn't converted at all. This behavior is to
  prevent the exporting of inverse kinematics bones.
3. An empty becomes a bone unless it has a parent but no children. In this case
  it creates a locator.
4. Mesh without parent becomes a bone with a cube inside. Mesh with a parent
  becomes a cube.

**The conversion rules can also be represented with this table:**

||Export as bone|no parent, no children| parent, no children|no parent,children|parent and children|
|---|---|---|---|---|---|
|__Bone__ |N/A|NONE|bone|bone|bone|
|__Empty__|bone|bone|locator|bone|bone|
|__Mesh__ |bone & cube|bone & cube|cube| bone & cube|cube|

