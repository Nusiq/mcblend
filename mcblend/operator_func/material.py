'''
Everything related to creating materials for the model.
'''
from typing import Deque, Optional, List, Tuple
from collections import deque

from bpy.types import Image, Material, Node, NodeTree
import bpy

from .typed_bpy_access import (
    get_inputs, get_links, get_nodes, get_outputs,
    new_material, set_default_value, set_image, set_interpolation,
    set_node_tree, set_operation, set_use_clamp)

PADDING = 300

def _create_node_group_defaults(name: str) -> Tuple[NodeTree, Node, Node]:
    group: NodeTree = bpy.data.node_groups.new(name, 'ShaderNodeTree')

    # create group inputs
    inputs: Node = get_nodes(group).new('NodeGroupInput')
    inputs.location = [0, 0]
    get_inputs(group).new('NodeSocketColor','Color')
    get_inputs(group).new('NodeSocketFloat','Alpha')

    # create group outputs
    outputs: Node = get_nodes(group).new('NodeGroupOutput')
    outputs.location = [4*PADDING, 0]
    get_outputs(group).new('NodeSocketColor','Color')
    get_outputs(group).new('NodeSocketFloat','Alpha')
    get_outputs(group).new('NodeSocketColor','Emission')

    return group, inputs, outputs

def create_entity_alphatest_node_group(material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity alphatest material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    if is_first:
        material.blend_method = 'CLIP'
    try:
        return bpy.data.node_groups['entity_alphatest']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_alphatest')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    # In: Alpha -> Math[ADD] -> Math[FLOOR] -> Out: Alpha
    math_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_node, 'GREATER_THAN')
    math_node.location = [1*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(math_node)[0], get_outputs(inputs)[1])
    get_links(group).new(get_inputs(outputs)[1], get_outputs(math_node)[0])
    # RGB (black) -> Out: Emission
    rgb_node = get_nodes(group).new("ShaderNodeRGB")
    set_default_value(get_outputs(rgb_node)['Color'], [0, 0, 0, 1])  # black
    rgb_node.location = [2*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(outputs)[2], get_outputs(rgb_node)[0])

    return group

def create_entity_alphatest_one_sided_node_group(
        material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity alphatest one sided material if it
    doesn't exist already, otherwise it returns existing node group.
    '''
    if is_first:
        material.blend_method = 'CLIP'
        material.use_backface_culling = True
    try:
        return bpy.data.node_groups['entity_alphatest_one_sided']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults(
        'entity_alphatest_one_sided')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    # In: Alpha -> Math[ADD] -> Math[FLOOR] -> Out: Alpha
    math_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_node, 'GREATER_THAN')
    math_node.location = [1*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(math_node)[0], get_outputs(inputs)[1])
    get_links(group).new(get_inputs(outputs)[1], get_outputs(math_node)[0])
    # RGB (black) -> Out: Emission
    rgb_node = get_nodes(group).new("ShaderNodeRGB")
    set_default_value(get_outputs(rgb_node)['Color'], [0, 0, 0, 1])  # black
    rgb_node.location = [2*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(outputs)[2], get_outputs(rgb_node)[0])

    return group

def create_entity_node_group(material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity alphatest material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    # pylint: disable=unused-argument
    # This is an opaque material it always everything below it and every
    # non-opaque material on top of it. It will never be combined with any
    # other material. "is_first" nad "material" are not used here
    # if is_first:
    #    pass
    try:
        return bpy.data.node_groups['entity']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults('entity')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    # Value (1.0) -> Out: Alpha
    value_node = get_nodes(group).new("ShaderNodeValue")
    set_default_value(get_outputs(value_node)['Value'], 1.0)
    value_node.location = [2*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(outputs)[1], get_outputs(value_node)[0])
    # RGB (black) -> Out: Emission
    rgb_node = get_nodes(group).new("ShaderNodeRGB")
    set_default_value(get_outputs(rgb_node)['Color'], [0, 0, 0, 1])  # black
    rgb_node.location = [2*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(outputs)[2], get_outputs(rgb_node)[0])

    return group

def create_entity_alphablend_node_group(material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity alphablend material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    if is_first:
        material.blend_method = 'BLEND'
        material.use_backface_culling = True
    try:
        return bpy.data.node_groups['entity_alphablend']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_alphablend')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    # In: Alpha -> Out: Alpha
    get_links(group).new(get_inputs(outputs)[1], get_outputs(inputs)[1])
    # RGB (black) -> Out: Emission
    rgb_node = get_nodes(group).new("ShaderNodeRGB")
    set_default_value(get_outputs(rgb_node)['Color'], [0, 0, 0, 1])  # black
    rgb_node.location = [1*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(outputs)[2], get_outputs(rgb_node)[0])

    return group

def create_entity_emissive_node_group(material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity emissive material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    # pylint: disable=unused-argument
    # This is an opaque material it always everything below it and every
    # non-opaque material on top of it. It will never be combined with any
    # other material. "is_first" nad "material" are not used here
    # if is_first:
    #    pass
    try:
        return bpy.data.node_groups['entity_emissive']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_emissive')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    # Value (1.0) -> Out: Alpha
    value_node = get_nodes(group).new("ShaderNodeValue")
    set_default_value(get_outputs(value_node)['Value'], 1.0)
    value_node.location = [2*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(outputs)[1], get_outputs(value_node)[0])
    # In: Color -> ... -> ... -> Vector[MULTIPLY][0] -> Out: Emission
    vector_node = get_nodes(group).new('ShaderNodeVectorMath')
    set_operation(vector_node, 'MULTIPLY')
    vector_node.location = [3*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(vector_node)[0], get_outputs(inputs)[0])
    get_links(group).new(get_inputs(outputs)[2], get_outputs(vector_node)[0])
    # In: Alpha -> Math[MULTIPLY] -> Math[SUBTRACT][1] -> Vector[MULTIPLY][1]
    math_1_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_1_node, 'MULTIPLY')
    math_1_node.location = [1*PADDING, -2*PADDING]
    math_2_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_2_node, 'SUBTRACT')
    set_use_clamp(math_2_node, True)
    math_2_node.location = [2*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(math_1_node)[0], get_outputs(inputs)[1])
    get_links(group).new(get_inputs(math_2_node)[1], get_outputs(math_1_node)[0])
    get_links(group).new(get_inputs(vector_node)[1], get_outputs(math_2_node)[0])

    return group

def create_entity_emissive_alpha_node_group(material: Material, is_first: bool) -> NodeTree:
    '''
    Creates a node group for entity emissive alpha material if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    if is_first:
        material.blend_method = 'CLIP'
    try:
        return bpy.data.node_groups['entity_emissive_alpha']
    except:  # pylint: disable=bare-except
        pass
    group, inputs, outputs = _create_node_group_defaults('entity_emissive_alpha')

    # In: Color-> Out: Color
    get_links(group).new(get_inputs(outputs)[0], get_outputs(inputs)[0])
    #  In: Alpha -> MATH[CEIL] -> Out: Alpha
    math_3_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_3_node, 'CEIL')
    math_3_node.location = [2*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(math_3_node)[0], get_outputs(inputs)[1])
    get_links(group).new(get_inputs(outputs)[1], get_outputs(math_3_node)[0])
    # In: Color -> ... -> ... -> Vector[MULTIPLY][0] -> Out: Emission
    vector_node = get_nodes(group).new('ShaderNodeVectorMath')
    set_operation(vector_node, 'MULTIPLY')
    vector_node.location = [3*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(vector_node)[0], get_outputs(inputs)[0])
    get_links(group).new(get_inputs(outputs)[2], get_outputs(vector_node)[0])
    # In: Alpha -> Math[MULTIPLY] -> Math[SUBTRACT][1] -> Vector[MULTIPLY][1]
    math_1_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_1_node, 'MULTIPLY')
    math_1_node.location = [1*PADDING, -2*PADDING]
    math_2_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_2_node, 'SUBTRACT')
    set_use_clamp(math_2_node, True)
    math_2_node.location = [2*PADDING, -2*PADDING]
    get_links(group).new(get_inputs(math_1_node)[0], get_outputs(inputs)[1])
    get_links(group).new(get_inputs(math_2_node)[1], get_outputs(math_1_node)[0])
    get_links(group).new(get_inputs(vector_node)[1], get_outputs(math_2_node)[0])

    return group

def create_material_mix_node_group() -> NodeTree:
    '''
    Creates a node group for mixing Minecraft materials if it doesn't exist
    already, otherwise it returns existing node group.
    '''
    try:
        return bpy.data.node_groups['material_mix']
    except:  # pylint: disable=bare-except
        pass
    group = bpy.data.node_groups.new('material_mix', 'ShaderNodeTree')
    # create group inputs
    inputs = get_nodes(group).new('NodeGroupInput')
    inputs.location = [0, 0]
    get_inputs(group).new('NodeSocketColor','Color1')
    get_inputs(group).new('NodeSocketColor','Color2')
    get_inputs(group).new('NodeSocketFloat','Alpha1')
    get_inputs(group).new('NodeSocketFloat','Alpha2')
    get_inputs(group).new('NodeSocketFloat','Emission1')
    get_inputs(group).new('NodeSocketFloat','Emission2')

    # create group outputs
    outputs = get_nodes(group).new('NodeGroupOutput')
    outputs.location = [2*PADDING, 0]
    get_outputs(group).new('NodeSocketColor','Color')
    get_outputs(group).new('NodeSocketFloat','Alpha')
    get_outputs(group).new('NodeSocketColor','Emission')

    # Mix colors (Color mix node)
    mix_colors_node = get_nodes(group).new('ShaderNodeMixRGB')
    mix_colors_node.location = [1*PADDING, 1*PADDING]
    get_links(group).new(get_inputs(mix_colors_node)['Color1'], get_outputs(inputs)['Color1'])
    get_links(group).new(get_inputs(mix_colors_node)['Color2'], get_outputs(inputs)['Color2'])
    get_links(group).new(get_inputs(mix_colors_node)['Fac'], get_outputs(inputs)['Alpha2'])
    get_links(group).new(get_inputs(outputs)['Color'], get_outputs(mix_colors_node)['Color'])

    # Mix alpha (Add and clamp aplha)
    math_node = get_nodes(group).new('ShaderNodeMath')
    set_operation(math_node, 'MAXIMUM')
    math_node.location = [1*PADDING, 0]
    # set_use_clamp(math_node, True)
    get_links(group).new(get_inputs(math_node)[0], get_outputs(inputs)['Alpha1'])
    get_links(group).new(get_inputs(math_node)[1], get_outputs(inputs)['Alpha2'])
    get_links(group).new(get_inputs(outputs)['Alpha'], get_outputs(math_node)[0])

    # Mix emissions (Color mix node)
    mix_emissions_node = get_nodes(group).new('ShaderNodeMixRGB')
    mix_emissions_node.location = [1*PADDING, -1*PADDING]
    get_links(group).new(get_inputs(mix_emissions_node)['Color1'], get_outputs(inputs)['Emission1'])
    get_links(group).new(get_inputs(mix_emissions_node)['Color2'], get_outputs(inputs)['Emission2'])
    get_links(group).new(get_inputs(mix_emissions_node)['Fac'], get_outputs(inputs)['Alpha2'])
    get_links(group).new(get_inputs(outputs)['Emission'], get_outputs(mix_emissions_node)['Color'])

    return group

MATERIALS_MAP_ALIASES = {  # Aliases used when loading but not suggested in GUI
    # DIRECT ALIASES
    # entity_alphatest
    'armor': 'entity_alphatest',
    'armor_stand': 'entity_alphatest',
    'arrow': 'entity_alphatest',
    'axolotl': 'entity_alphatest',
    'bat': 'entity_alphatest',
    'bed': 'entity_alphatest',
    'bee': 'entity_alphatest',
    'chicken_legs': 'entity_alphatest',
    'dragon_head': 'entity_alphatest',
    'egg': 'entity_alphatest',
    'elytra': 'entity_alphatest',
    'ender_crystal': 'entity_alphatest',
    'endermite': 'entity_alphatest',
    'eye_of_ender_signal': 'entity_alphatest',
    'ender_pearl': 'entity_alphatest',
    'evoker': 'entity_alphatest',
    'fang': 'entity_alphatest',
    'fireball': 'entity_alphatest',
    'fireworks_rocket': 'entity_alphatest',
    'fishing_hook': 'entity_alphatest',
    'clownfish': 'entity_alphatest',
    'cod': 'entity_alphatest',
    'conduit': 'entity_alphatest',
    'pufferfish': 'entity_alphatest',
    'salmon': 'entity_alphatest',
    'guardian': 'entity_alphatest',
    'horse': 'entity_alphatest',
    'husk': 'entity_alphatest',
    'husk_clothes': 'entity_alphatest',
    'ravager': 'entity_alphatest',
    'iron_golem': 'entity_alphatest',
    'minecart': 'entity_alphatest',
    'mob_head': 'entity_alphatest',
    'mooshroom_mushrooms': 'entity_alphatest',
    'npc': 'entity_alphatest',
    'ocelot': 'entity_alphatest',
    'parrot': 'entity_alphatest',
    'hoglin': 'entity_alphatest',
    'zoglin': 'entity_alphatest',
    'trident_riptide': 'entity_alphatest',
    'player_alphatest': 'entity_alphatest',
    'shulker': 'entity_alphatest',
    'shulker_box': 'entity_alphatest',
    'shulker_bullet': 'entity_alphatest',
    'silverfish_layers': 'entity_alphatest',
    'skeleton': 'entity_alphatest',
    'pillager': 'entity_alphatest',
    'piglin': 'entity_alphatest',
    'piglin_brute': 'entity_alphatest',
    'goat': 'entity_alphatest',
    'slime': 'entity_alphatest',
    'snowball': 'entity_alphatest',
    'stray': 'entity_alphatest',
    'stray_clothes': 'entity_alphatest',
    'strider': 'entity_alphatest',
    'vex': 'entity_alphatest',
    'villager': 'entity_alphatest',
    'vindicator': 'entity_alphatest',
    'wandering_trader': 'entity_alphatest',
    'witch': 'entity_alphatest',
    'wither_boss': 'entity_alphatest',
    'zombie': 'entity_alphatest',
    'zombie_villager': 'entity_alphatest',

    # entity
    'agent': 'entity',
    'bell': 'entity',
    'boat': 'entity',
    'chalkboard': 'entity',
    'chest': 'entity',
    'chicken': 'entity',
    'cow': 'entity',
    'creeper': 'entity',
    'enchanting_table_book': 'entity',
    'fox': 'entity',
    'leash_knot': 'entity',
    'llama_spit': 'entity',
    'mooshroom': 'entity',
    'pig': 'entity',
    'shield': 'entity',
    'trident': 'entity',
    'piston_arm': 'entity',
    'player': 'entity',
    'polar_bear': 'entity',
    'panda': 'entity',
    'rabbit': 'entity',
    'silverfish': 'entity',
    'snow_golem': 'entity',
    'snow_golem_pumpkin': 'entity',
    'squid': 'entity',
    'dolphin': 'entity',
    'turtle': 'entity',
    'camera': 'entity',

    # entity_emissive
    'glow_squid': 'entity_emissive',
    'blaze_body': 'entity_emissive',

    # entity_emissive_alpha
    'blaze_head': 'entity_emissive_alpha',
    'drowned': 'entity_emissive_alpha',
    'enderman': 'entity_emissive_alpha',
    'ghast': 'entity_emissive_alpha',
    'magma_cube': 'entity_emissive_alpha',
    'spider': 'entity_emissive_alpha',
    'phantom': 'entity_emissive_alpha',

    # entity_alphatest_one_sided
    'axolotl_limbs': 'entity_alphatest_one_sided',

    # SIMILAR BUT NOT EXACTLY
    # entity_alphatest
    'villager_v2': 'entity_alphatest',
    'entity_alphatest_glint_item': 'entity_alphatest',
    'on_screen_effect': 'entity_alphatest',
    'player_animated': 'entity_alphatest',
    'item_in_hand_entity_alphatest': 'entity_alphatest',
    'conduit_wind': 'entity_alphatest',
    'map': 'entity_alphatest',
    'zombie_villager_v2': 'entity_alphatest',
    'entity_alphatest_glint': 'entity_alphatest',

    'entity_multitexture_masked': 'entity_alphatest',
    'villager_v2_masked': 'entity_alphatest',
    'zombie_villager_v2_masked': 'entity_alphatest',
    'entity_alphatest_multicolor_tint': 'entity_alphatest',
    'entity_custom': 'entity_alphatest',
    'entity_dissolve_layer1': 'entity_alphatest',
    'entity_multitexture_multiplicative_blend': 'entity_alphatest',

    # entity
    'entity_dissolve_layer0': 'entity',
    'entity_nocull': 'entity',
    'entity_lead_base': 'entity',
    'beacon_beam_transparent': 'entity',
    'slime_outer': 'entity',
    'entity_multitexture': 'entity',
    'entity_glint': 'entity',
    'entity_alphablend': 'entity',
    'entity_emissive': 'entity',
    'experience_orb': 'entity',
    'item_in_hand': 'entity',


    # entity_emissive_alpha
    'enderman_invisible': 'entity_emissive_alpha',
    'spider_invisible': 'entity_emissive_alpha',
    'phantom_invisible': 'entity_emissive_alpha',
    'entity_emissive_alpha_one_sided': 'entity_emissive_alpha',
}

MATERIALS_MAP = {
    'entity_alphatest': create_entity_alphatest_node_group,
    'entity_alphatest_one_sided': create_entity_alphatest_one_sided_node_group,
    'entity_alphablend': create_entity_alphablend_node_group,
    'entity_emissive': create_entity_emissive_node_group,
    'entity_emissive_alpha': create_entity_emissive_alpha_node_group,
    'entity': create_entity_node_group,
}

# OPAQUE materials don't mix with other materials, they just overwrite
# everything below them
OPAQUE_MATERIALS = {
    'entity_emissive', 'entity'
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
    material: Material = new_material(material_name)
    material.use_nodes = True
    material.blend_method = 'OPAQUE'

    node_tree = material.node_tree
    output_node = get_nodes(node_tree)['Material Output']
    bsdf_node = get_nodes(node_tree)["Principled BSDF"]
    set_default_value(get_inputs(bsdf_node)['Specular'], 0)
    set_default_value(get_inputs(bsdf_node)['Sheen Tint'], 0)
    set_default_value(get_inputs(bsdf_node)['Roughness'], 1)

    node_groups: Deque[Node] = deque()
    # Test for opaque materials, if you don't find eny enter second loop
    for i, item in enumerate(data):
        img, name = item
        true_material_name = name
        try:
            if name not in MATERIALS_MAP:
                true_material_name = MATERIALS_MAP_ALIASES[name]
        except KeyError:
            true_material_name = 'entity_alphatest'  # default
        if true_material_name not in OPAQUE_MATERIALS:
            continue
        # Reach this code only with OPAQUE_MATERIALS (executed onece)
        node_group_data = MATERIALS_MAP[true_material_name](material, i == 0)
        node_group: Node = get_nodes(node_tree).new('ShaderNodeGroup')
        set_node_tree(node_group, node_group_data)
        node_group.location = [-3*PADDING, -i*PADDING]
        image_node = get_nodes(node_tree).new('ShaderNodeTexImage')
        set_interpolation(image_node, 'Closest')
        set_image(image_node, img)
        image_node.location = [-4*PADDING, -i*PADDING]
        get_links(node_tree).new(
            get_inputs(node_group)[0],
            get_outputs(image_node)[0])
        get_links(node_tree).new(
            get_inputs(node_group)[1],
            get_outputs(image_node)[1])
        node_groups.append(node_group)
        break  # found opaque material
    else:  # No opaque materials has been found
        for i, item in enumerate(data):
            img, name = item
            true_material_name = name
            try:
                if name not in MATERIALS_MAP:
                    true_material_name = MATERIALS_MAP_ALIASES[name]
            except KeyError:
                true_material_name = 'entity_alphatest'  # default
            node_group_data = MATERIALS_MAP[true_material_name](material, i == 0)
            node_group = get_nodes(node_tree).new('ShaderNodeGroup')
            set_node_tree(node_group, node_group_data)
            node_group.location = [-3*PADDING, -i*PADDING]
            image_node = get_nodes(node_tree).new('ShaderNodeTexImage')
            set_interpolation(image_node, 'Closest')
            set_image(image_node, img)
            image_node.location = [-4*PADDING, -i*PADDING]
            get_links(node_tree).new(
                get_inputs(node_group)[0],
                get_outputs(image_node)[0])
            get_links(node_tree).new(
                get_inputs(node_group)[1],
                get_outputs(image_node)[1])
            node_groups.append(node_group)

    # Join node groups using mix node groups
    i = 0
    while True:
        if len(node_groups) > 1:
            connection = get_nodes(node_tree).new('ShaderNodeGroup')
            set_node_tree(connection, create_material_mix_node_group())
            connection.location = [(i-2)*PADDING, -i*PADDING]
            bottom = node_groups.popleft()
            top = node_groups.popleft()
            node_groups.appendleft(connection)
            get_links(node_tree).new(
                get_inputs(connection)['Color1'],
                get_outputs(bottom)['Color'])
            get_links(node_tree).new(
                get_inputs(connection)['Alpha1'],
                get_outputs(bottom)['Alpha'])
            get_links(node_tree).new(
                get_inputs(connection)['Emission1'],
                get_outputs(bottom)['Emission'])
            get_links(node_tree).new(
                get_inputs(connection)['Color2'],
                get_outputs(top)['Color'])
            get_links(node_tree).new(
                get_inputs(connection)['Alpha2'],
                get_outputs(top)['Alpha'])
            get_links(node_tree).new(
                get_inputs(connection)['Emission2'],
                get_outputs(top)['Emission'])
            i += 1
        elif len(node_groups) == 1:
            final_node = node_groups[0]
            get_links(node_tree).new(
                get_inputs(bsdf_node)['Base Color'],
                get_outputs(final_node)['Color'])
            get_links(node_tree).new(
                get_inputs(bsdf_node)['Alpha'],
                get_outputs(final_node)['Alpha'])
            get_links(node_tree).new(
                get_inputs(bsdf_node)['Emission'],
                get_outputs(final_node)['Emission'])
            break
        else:  # shouldn't happen if bone uses any materials
            break
    bsdf_node.location = [(i-1)*PADDING, 0]
    output_node.location = [i*PADDING, 0]
    return material
