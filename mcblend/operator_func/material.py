'''
Everything related to creating materials for the model.
'''
from typing import Deque, Optional, List, Tuple

import bpy
from collections import deque
from bpy.types import Image, Material, Node, NodeTree

PADDING = 300

def _create_node_group_defaults(name: str) -> Tuple[NodeTree, Node, Node]:
    group: NodeTree = bpy.data.node_groups.new(name, 'ShaderNodeTree')

    # create group inputs
    inputs: Node = group.nodes.new('NodeGroupInput')
    inputs.location = (0, 0)
    group.inputs.new('NodeSocketColor','Color')
    group.inputs.new('NodeSocketFloat','Alpha')

    # create group outputs
    outputs: Node = group.nodes.new('NodeGroupOutput')
    outputs.location = (4*PADDING, 0)
    group.outputs.new('NodeSocketColor','Color')
    group.outputs.new('NodeSocketFloat','Alpha')
    group.outputs.new('NodeSocketColor','Emission')

    return group, inputs, outputs

def create_entity_alphatest_node_group() -> NodeTree:
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
    math_node = group.nodes.new('ShaderNodeMath')
    math_node.operation = 'GREATER_THAN'
    math_node.location = (1*PADDING, -1*PADDING)
    group.links.new(math_node.inputs[0], inputs.outputs[1])
    group.links.new(outputs.inputs[1], math_node.outputs[0])
    # RGB (black) -> Out: Emission
    rgb_node = group.nodes.new("ShaderNodeRGB")
    rgb_node.outputs['Color'].default_value = (0, 0, 0, 1)  # black
    rgb_node.location = (2*PADDING, -2*PADDING)
    group.links.new(outputs.inputs[2], rgb_node.outputs[0])

    return group

def create_entity_alphablend_node_group() -> NodeTree:
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

def create_entity_emissive_node_group() -> NodeTree:
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

def create_entity_emissive_alpha_node_group() -> NodeTree:
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

def create_material_mix_node_group() -> NodeTree:
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
    math_node.operation = 'MAXIMUM'
    math_node.location = (1*PADDING, 0)
    # math_node.use_clamp = True
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

MATERIALS_MAP = {
        'entity_alphatest': create_entity_alphatest_node_group,

        'entity_alphablend': create_entity_alphablend_node_group,

        'entity_emissive': create_entity_emissive_node_group,
        'blaze_body': create_entity_emissive_node_group,

        'entity_emissive_alpha': create_entity_emissive_alpha_node_group,
        'enderman': create_entity_emissive_alpha_node_group,
        'spider': create_entity_emissive_alpha_node_group,
    }

def create_bone_material(
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

    material: Material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    material.blend_method = 'OPAQUE'
    if len(data) > 0:
        _, name = data[0]
        if name in (
                'entity_alphatest', 'entity_emissive_alpha', 'enderman',
                'spider'):
            material.blend_method = 'CLIP'
        elif name in 'entity_alphablend':
            material.blend_method = 'BLEND'
            material.use_backface_culling = True

    node_tree = material.node_tree
    output_node = node_tree.nodes['Material Output']
    bsdf_node = node_tree.nodes["Principled BSDF"]
    bsdf_node.inputs['Specular'].default_value = 0
    bsdf_node.inputs['Sheen Tint'].default_value = 0
    bsdf_node.inputs['Roughness'].default_value = 1

    node_groups: Deque[Node] = deque()

    for i, item in enumerate(data):
        img, name = item
        try:
            node_group_data = MATERIALS_MAP[name]()
        except:
            node_group_data = create_entity_alphatest_node_group()  # default
        node_group: Node = node_tree.nodes.new('ShaderNodeGroup')
        node_group.node_tree = node_group_data
        node_group.location = (-3*PADDING, -i*PADDING)
        image_node = node_tree.nodes.new('ShaderNodeTexImage')
        image_node.interpolation = 'Closest'
        image_node.image = img
        image_node.location = (-4*PADDING, -i*PADDING)
        node_tree.links.new(node_group.inputs[0], image_node.outputs[0])
        node_tree.links.new(node_group.inputs[1], image_node.outputs[1])
        node_groups.append(node_group)
    # Join node groups using mix node groups
    i = 0
    while True:
        if len(node_groups) > 1:
            connection = node_tree.nodes.new('ShaderNodeGroup')
            connection.node_tree = create_material_mix_node_group()
            connection.location = ((i-2)*PADDING, -i*PADDING)
            bottom = node_groups.popleft()
            top = node_groups.popleft()
            node_groups.appendleft(connection)
            
            node_tree.links.new(connection.inputs['Color1'], bottom.outputs['Color'])
            node_tree.links.new(connection.inputs['Alpha1'], bottom.outputs['Alpha'])
            node_tree.links.new(connection.inputs['Emission1'], bottom.outputs['Emission'])
            node_tree.links.new(connection.inputs['Color2'], top.outputs['Color'])
            node_tree.links.new(connection.inputs['Alpha2'], top.outputs['Alpha'])
            node_tree.links.new(connection.inputs['Emission2'], top.outputs['Emission'])
            i += 1
        elif len(node_groups) == 1:
            final_node = node_groups[0]
            node_tree.links.new(bsdf_node.inputs['Base Color'], final_node.outputs['Color'])
            node_tree.links.new(bsdf_node.inputs['Alpha'], final_node.outputs['Alpha'])
            node_tree.links.new(bsdf_node.inputs['Emission'], final_node.outputs['Emission'])
            break
        else:  # shouldn't happen if bone uses any materials
            break
    bsdf_node.location = [(i-1)*PADDING, 0]
    output_node.location = [i*PADDING, 0]
    return material
