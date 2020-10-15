# UV-groups

UV-groups influence the process of UV-mapping.

The main purpose of UV-groups is to group cubes together so that they are mapped
to the same spot on the texture. Using UV groups can help reduce the texture
size when the model has many identical parts.

UV-groups also let you can change the appearance  of generated textures to your
preference. This can be useful for setting some distinguishable look for UV-group
members. You can create some fairly advanced textures with it, but it's usually
better to create textures in a usual way. Future versions of Mcblend will allow
you to export and import UV-group properties, making this feature more useful
for texturing.

## Creating and removing UV-groups
UV-groups are added / removed using the "Mcblend UV groups" panel from the
[Scene Properties](../gui_changes/#scene-properties) with "New UV group" and
"Delete this UV group" buttons.

## Adding objects to UV-groups
Adding object do UV-groups is done with
[Set the UV group](../basic_operators/#set-the-uv-group) button on sidebar. You
must create at least one UV-group in order to add objects to it.