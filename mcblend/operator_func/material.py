'''
Everything related to creating materials for the model.
'''
from typing import Optional, List, Tuple

import bpy
from bpy.types import Image, Material

PADDING = 300

def _create_node_group_defaults(name: str):
    group = bpy.data.node_groups.new(name, 'ShaderNodeTree')

    # create group inputs
    inputs = group.nodes.new('NodeGroupInput')
    inputs.location = (0, 0)
    group.inputs.new('NodeSocketColor','Color')
    group.inputs.new('NodeSocketFloat','Alpha')

    # create group outputs
    outputs = group.nodes.new('NodeGroupOutput')
    outputs.location = (4*PADDING, 0)
    group.outputs.new('NodeSocketColor','Color')
    group.outputs.new('NodeSocketFloat','Alpha')
    group.outputs.new('NodeSocketColor','Emission')

    return group, inputs, outputs

def create_entity_alphatest_node_group():
    '''
    Creates a node group for entity alphatest material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['entity_alphatest']
    except:
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_alphatest')
    
    # In: Color-> Out: Color
    group.links.new(outputs.inputs[0], inputs.outputs[0])
    # In: Alpha -> Math[ADD] -> Math[FLOOR] -> Out: Alpha
    math_1_node = group.nodes.new('ShaderNodeMath')
    math_1_node.operation = 'ADD'
    math_1_node.location = (1*PADDING, -1*PADDING)
    math_2_node = group.nodes.new('ShaderNodeMath')
    math_2_node.operation = 'FLOOR'
    math_2_node.use_clamp = True
    math_2_node.location = (2*PADDING, -1*PADDING)
    group.links.new(math_1_node.inputs[0], inputs.outputs[1])
    group.links.new(math_2_node.inputs[0], math_1_node.outputs[0])
    group.links.new(outputs.inputs[1], math_2_node.outputs[0])
    # RGB (black) -> Out: Emission
    rgb_node = group.nodes.new("ShaderNodeRGB")
    rgb_node.outputs['Color'].default_value = (0, 0, 0, 1)  # black
    rgb_node.location = (2*PADDING, -2*PADDING)
    group.links.new(outputs.inputs[2], rgb_node.outputs[0])

    return group

def create_entity_alphablend_node_group():
    '''
    Creates a node group for entity alphablend material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['entity_alphablend']
    except:
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_alphablend')

    # In: Color-> Out: Color
    group.links.new(outputs.inputs[0], inputs.outputs[0])
    # In: Alpha -> Out: Alpha
    group.links.new(outputs.inputs[1], inputs.outputs[1])
    # RGB (black) -> Out: Emission
    rgb_node = group.nodes.new("ShaderNodeRGB")
    rgb_node.outputs['Color'].default_value = (0, 0, 0, 1)  # black
    rgb_node.location = (1*PADDING, -1*PADDING)
    group.links.new(outputs.inputs[2], rgb_node.outputs[0])

    return group

def create_entity_emissive_node_group():
    '''
    Creates a node group for entity emissive material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['entity_emissive']
    except:
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_emissive')

    # In: Color-> Out: Color
    group.links.new(outputs.inputs[0], inputs.outputs[0])
    # Value (1.0) -> Out: Alpha
    value_node = group.nodes.new("ShaderNodeValue")
    value_node.outputs['Value'].default_value = 1.0
    value_node.location = (2*PADDING, -1*PADDING)
    group.links.new(outputs.inputs[1], value_node.outputs[0])
    # In: Color -> ... -> ... -> Vector[MULTIPLY][0] -> Out: Emission
    vector_node = group.nodes.new('ShaderNodeVectorMath')
    vector_node.operation = 'MULTIPLY'
    vector_node.location = (3*PADDING, -2*PADDING)
    group.links.new(vector_node.inputs[0], inputs.outputs[0])
    group.links.new(outputs.inputs[2], vector_node.outputs[0])
    # In: Alpha -> Math[MULTIPLY] -> Math[SUBTRACT][1] -> Vector[MULTIPLY][1]
    math_1_node = group.nodes.new('ShaderNodeMath')
    math_1_node.operation = 'MULTIPLY'
    math_1_node.location = (1*PADDING, -2*PADDING)
    math_2_node = group.nodes.new('ShaderNodeMath')
    math_2_node.operation = 'SUBTRACT'
    math_2_node.use_clamp = True
    math_2_node.location = (2*PADDING, -2*PADDING)
    group.links.new(math_1_node.inputs[0], inputs.outputs[1])
    group.links.new(math_2_node.inputs[1], math_1_node.outputs[0])
    group.links.new(vector_node.inputs[1], math_2_node.outputs[0])

    return group

def create_entity_emissive_alpha_node_group():
    '''
    Creates a node group for entity emissive alpha material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['entity_emissive_alpha']
    except:
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_emissive_alpha')

    # In: Color-> Out: Color
    group.links.new(outputs.inputs[0], inputs.outputs[0])
    #  In: Alpha -> MATH[CEIL] -> Out: Alpha
    math_3_node = group.nodes.new('ShaderNodeMath')
    math_3_node.operation = 'CEIL'
    math_3_node.location = (2*PADDING, -1*PADDING)
    group.links.new(math_3_node.inputs[0], inputs.outputs[1])
    group.links.new(outputs.inputs[1], math_3_node.outputs[0])
    # In: Color -> ... -> ... -> Vector[MULTIPLY][0] -> Out: Emission
    vector_node = group.nodes.new('ShaderNodeVectorMath')
    vector_node.operation = 'MULTIPLY'
    vector_node.location = (3*PADDING, -2*PADDING)
    group.links.new(vector_node.inputs[0], inputs.outputs[0])
    group.links.new(outputs.inputs[2], vector_node.outputs[0])
    # In: Alpha -> Math[MULTIPLY] -> Math[SUBTRACT][1] -> Vector[MULTIPLY][1]
    math_1_node = group.nodes.new('ShaderNodeMath')
    math_1_node.operation = 'MULTIPLY'
    math_1_node.location = (1*PADDING, -2*PADDING)
    math_2_node = group.nodes.new('ShaderNodeMath')
    math_2_node.operation = 'SUBTRACT'
    math_2_node.use_clamp = True
    math_2_node.location = (2*PADDING, -2*PADDING)
    group.links.new(math_1_node.inputs[0], inputs.outputs[1])
    group.links.new(math_2_node.inputs[1], math_1_node.outputs[0])
    group.links.new(vector_node.inputs[1], math_2_node.outputs[0])

    return group

def create_material_mix_node_group():
    '''
    Creates a node group for mixing Minecraft materials if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['material_mix']
    except:
        pass
    group = bpy.data.node_groups.new('material_mix', 'ShaderNodeTree')
    # create group inputs
    inputs = group.nodes.new('NodeGroupInput')
    inputs.location = (0, 0)
    group.inputs.new('NodeSocketColor','Color1')
    group.inputs.new('NodeSocketColor','Color2')
    group.inputs.new('NodeSocketFloat','Alpha1')
    group.inputs.new('NodeSocketFloat','Alpha2')
    group.inputs.new('NodeSocketFloat','Emission1')
    group.inputs.new('NodeSocketFloat','Emission2')

    # create group outputs
    outputs = group.nodes.new('NodeGroupOutput')
    outputs.location = (2*PADDING, 0)
    group.outputs.new('NodeSocketColor','Color')
    group.outputs.new('NodeSocketFloat','Alpha')
    group.outputs.new('NodeSocketColor','Emission')

    # Mix colors (Color mix node)
    mix_colors_node = group.nodes.new('ShaderNodeMixRGB')
    mix_colors_node.location = (1*PADDING, 1*PADDING)
    group.links.new(mix_colors_node.inputs['Color1'], inputs.outputs['Color1'])
    group.links.new(mix_colors_node.inputs['Color2'], inputs.outputs['Color2'])
    group.links.new(mix_colors_node.inputs['Fac'], inputs.outputs['Alpha2'])
    group.links.new(outputs.inputs['Color'], mix_colors_node.outputs['Color'])

    # Mix alpha (Add and clamp aplha)
    math_node = group.nodes.new('ShaderNodeMath')
    math_node.operation = 'ADD'
    math_node.location = (1*PADDING, 0)
    math_node.use_clamp = True
    group.links.new(math_node.inputs[0], inputs.outputs['Alpha1'])
    group.links.new(math_node.inputs[1], inputs.outputs['Alpha2'])
    group.links.new(outputs.inputs['Alpha'], math_node.outputs[0])

    # Mix emissions (Color mix node)
    mix_emissions_node = group.nodes.new('ShaderNodeMixRGB')
    mix_emissions_node.location = (1*PADDING, -1*PADDING)
    group.links.new(mix_emissions_node.inputs['Color1'], inputs.outputs['Emission1'])
    group.links.new(mix_emissions_node.inputs['Color2'], inputs.outputs['Emission2'])
    group.links.new(mix_emissions_node.inputs['Fac'], inputs.outputs['Alpha2'])
    group.links.new(outputs.inputs['Emission'], mix_emissions_node.outputs['Color'])

    return group

def _create_material_defaults(material_name: str) -> Material:
    # type: ignore
    material: Material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    bsdf_node.inputs['Specular'].default_value = 0
    bsdf_node.inputs['Sheen Tint'].default_value = 0
    bsdf_node.inputs['Roughness'].default_value = 1
    image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.interpolation = 'Closest'
    return material

def create_entity_alphatest(material_name: str, image: Optional[Image]=None) -> Material:
    '''
    Creates and returns Blender material that resembles Minecraft's
    entity_alphatest material.

    :param material_name: the name of the material (if it's already used then
        an created material can have additional index)
    :returns: newly created Blender material
    '''
    # TODO - use the node group from create_entity_alphatest_node_group
    material = _create_material_defaults(material_name)
    material.use_backface_culling = False
    material.blend_method = 'CLIP'
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    image_node = material.node_tree.nodes["Image Texture"]
    image_node.image = image
    material.node_tree.links.new(bsdf_node.inputs['Base Color'], image_node.outputs['Color'])
    material.node_tree.links.new(bsdf_node.inputs['Alpha'], image_node.outputs['Alpha'])
    return material

def create_entity_alphablend(material_name: str, image: Optional[Image]=None) -> Material:
    '''
    Creates and returns Blender material that resembles Minecraft's
    entity_alphablend material.

    :param material_name: the name of the material (if it's already used then
        an created material can have additional index)
    :returns: newly created Blender material
    '''
    # TODO - use the node group from create_entity_alphablend_node_group
    material = _create_material_defaults(material_name)
    material.use_backface_culling = True
    material.blend_method = 'BLEND'
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    image_node = material.node_tree.nodes["Image Texture"]
    image_node.image = image
    material.node_tree.links.new(bsdf_node.inputs['Base Color'], image_node.outputs['Color'])
    material.node_tree.links.new(bsdf_node.inputs['Alpha'], image_node.outputs['Alpha'])
    return material

def create_entity_emissive(material_name: str, image: Optional[Image]=None) -> Material:
    '''
    Creates and returns Blender material that resembles Minecraft's
    entity_emissive/blaze_body material.

    :param material_name: the name of the material (if it's already used then
        an created material can have additional index)
    :returns: newly created Blender material
    '''
    # TODO - use the node group from create_entity_emissive_node_group
    material = _create_material_defaults(material_name)
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    image_node = material.node_tree.nodes["Image Texture"]
    image_node.image = image

    math_1_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_1_node.operation = 'MULTIPLY'

    math_2_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_2_node.operation = 'SUBTRACT'

    vector_node = material.node_tree.nodes.new('ShaderNodeVectorMath')
    vector_node.operation = 'MULTIPLY'

    material.node_tree.links.new(bsdf_node.inputs['Base Color'], image_node.outputs['Color'])
    material.node_tree.links.new(bsdf_node.inputs['Emission'], vector_node.outputs['Vector'])
    material.node_tree.links.new(vector_node.inputs[0], image_node.outputs['Color'])
    material.node_tree.links.new(vector_node.inputs[1], math_2_node.outputs['Value'])
    material.node_tree.links.new(math_2_node.inputs[1], math_1_node.outputs['Value'])
    material.node_tree.links.new(math_1_node.inputs[0], image_node.outputs['Alpha'])

    return material

def create_entity_emissive_alpha(material_name: str, image: Optional[Image]=None) -> Material:
    '''
    Creates and returns Blender material that resembles Minecraft's
    entity_emissive_alpha/enderman/spider material.

    :param material_name: the name of the material (if it's already used then
        an created material can have additional index)
    :returns: newly created Blender material
    '''
    # TODO - use the node group from create_entity_emissive_alpha_node_group
    material = _create_material_defaults(material_name)
    material.use_backface_culling = False
    material.blend_method = 'CLIP'
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    image_node = material.node_tree.nodes["Image Texture"]
    image_node.image = image

    math_1_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_1_node.operation = 'MULTIPLY'

    math_2_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_2_node.operation = 'SUBTRACT'

    math_3_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_3_node.operation = 'CEIL'

    vector_node = material.node_tree.nodes.new('ShaderNodeVectorMath')
    vector_node.operation = 'MULTIPLY'

    material.node_tree.links.new(bsdf_node.inputs['Base Color'], image_node.outputs['Color'])
    material.node_tree.links.new(bsdf_node.inputs['Emission'], vector_node.outputs['Vector'])
    material.node_tree.links.new(vector_node.inputs[0], image_node.outputs['Color'])
    material.node_tree.links.new(vector_node.inputs[1], math_2_node.outputs['Value'])
    material.node_tree.links.new(math_2_node.inputs[1], math_1_node.outputs['Value'])
    material.node_tree.links.new(math_1_node.inputs[0], image_node.outputs['Alpha'])
    material.node_tree.links.new(bsdf_node.inputs['Alpha'], math_3_node.outputs['Value'])
    material.node_tree.links.new(math_3_node.inputs[0], image_node.outputs['Alpha'])

    return material

def create_material(material_name: str, image: Optional[Image]) -> Material:
    '''
    Creates a material based on it's name. If the name is unknown
    creates entity_alphatest material.

    :param material_name: the name of the material to create and the identifier
        used to select one of the known Minecraft materials.
    '''
    materials_map = {
        'entity_alphatest': create_entity_alphatest,
        'entity_alphablend': create_entity_alphablend,

        'entity_emissive': create_entity_emissive,
        'blaze_body': create_entity_emissive,

        'entity_emissive_alpha': create_entity_emissive_alpha,
        'enderman': create_entity_emissive_alpha,
        'spider': create_entity_emissive_alpha,
    }
    if material_name not in materials_map:
        return create_entity_alphatest(material_name, image)
    return materials_map[material_name](material_name, image)

def build_bone_material(
        material_name: str,
        data: List[Tuple[Optional[Image], str]]) -> Material:
    '''
    Creates Blender material for a Minecraft bone based on a list of textures
    and Minecraft materials used by the render controllers that dispay this
    bone.

    :param data: The list of tuples where every item is a pair of a texture and
        material name used by render controllers that display the bone.

    :returns: Material for Blender object that represent Minecraft bone.
    '''
    materials_map = {
        'entity_alphatest': create_entity_alphatest_node_group,
        'entity_alphablend': create_entity_alphablend_node_group,

        'entity_emissive': create_entity_emissive_node_group,
        'blaze_body': create_entity_emissive_node_group,

        'entity_emissive_alpha': create_entity_emissive_alpha_node_group,
        'enderman': create_entity_emissive_alpha_node_group,
        'spider': create_entity_emissive_alpha_node_group,
    }

    material: Material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    node_tree = material.node_tree
    bsdf_node = node_tree.nodes["Principled BSDF"]
    bsdf_node.inputs['Specular'].default_value = 0
    bsdf_node.inputs['Sheen Tint'].default_value = 0
    bsdf_node.inputs['Roughness'].default_value = 1

    node_groups = []

    for i, item in enumerate(data):
        img, name = item
        try:
            node_group_data = materials_map[name]()
        except:
            node_group_data = create_entity_alphatest_node_group()  # default
        node_group = node_tree.nodes.new('ShaderNodeGroup')
        node_group.node_tree = node_group_data
        node_group.location = (PADDING, -i*PADDING)
        image_node = node_tree.nodes.new('ShaderNodeTexImage')
        image_node.interpolation = 'Closest'
        image_node.image = img
        node_group.location = (0, -i*PADDING)
        node_tree.links.new(node_group.inputs[0], image_node.outputs[0])
        node_tree.links.new(node_group.inputs[1], image_node.outputs[1])
        node_groups.append(node_group)
    return material
