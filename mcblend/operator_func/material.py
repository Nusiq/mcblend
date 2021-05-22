'''
Everything related to creating materials for the model.
'''
from typing import Optional

import bpy
from bpy.types import Image, Material


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
        return create_entity_alphatest(material_name)
    return materials_map[material_name](material_name, image)
