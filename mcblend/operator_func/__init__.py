'''
Functions used directly by the blender operators.
'''
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

import bpy
from bpy.types import Image, Material
import bpy_types
import numpy as np

from .animation import AnimationExport
from .bedrock_packs import Project, ResourcePack
from .common import (
    MINECRAFT_SCALE_FACTOR, CubePolygon, McblendObjectGroup, MeshType,
    apply_obj_transform_keep_origin, fix_cube_rotation)
from .importer import ImportGeometry, ModelLoader
from .material import create_bone_material
from .model import ModelExport
from .uv import CoordinatesConverter, UvMapper


def export_model(context: bpy_types.Context) -> Dict:
    '''
    Creates a Minecraft model JSON dict from selected objects.
    Raises NameConflictException if name conflicts in some bones
    are detected.

    :param context: the context of running the operator.
    :returns: JSON dict with Minecraft model.
    '''
    result = ModelExport.json_outer()
    for object in context.selected_objects:
        if object.type != 'ARMATURE':
            continue
        mcblend_obj_group = McblendObjectGroup(object)
        model_properties = object.mcblend_object_properties

        model = ModelExport(
            texture_width=model_properties.texture_width,
            texture_height=model_properties.texture_height,
            visible_bounds_offset=tuple(  # type: ignore
                model_properties.visible_bounds_offset),
            visible_bounds_width=model_properties.visible_bounds_width,
            visible_bounds_height=model_properties.visible_bounds_height,
            model_name=model_properties.model_name,
        )
        model.load(mcblend_obj_group)
        result['minecraft:geometry'].append(model.json_inner())
    return result

def export_animation(
        context: bpy_types.Context, old_dict: Optional[Dict]
    ) -> Dict:
    '''
    Creates a Minecraft animation (dictionary) from selected objects.
    Raises NameConflictException if name conflicts in some bones are
    duplicated.

    :param context: the context of running the operator.
    :param old_dict: optional - JSON dict with animation to write into.
    :returns: JSON dict of Minecraft animations.
    '''
    # Check and create object properties
    # TODO - now McblendObjectGroup is created from armature object not from
    # context. This exporter needs to be changed.
    object_properties = McblendObjectGroup(context)

    anim_data = context.scene.mcblend_animations[
        context.scene.mcblend_active_animation]

    animation = AnimationExport(
        name=anim_data.name,
        length=(context.scene.frame_end-1)/context.scene.render.fps,
        loop_animation=anim_data.loop,
        single_frame=anim_data.single_frame,
        anim_time_update=anim_data.anim_time_update,
        fps=context.scene.render.fps,
        effect_events={
            event.name: event.get_effects_dict()
            for event in context.scene.mcblend_events
        }
    )
    animation.load_poses(object_properties, context)
    return animation.json(
        old_json=old_dict, skip_rest_poses=anim_data.skip_rest_poses)

def set_uvs(context: bpy_types.Context):
    '''
    Maps the UV for selected objects.

    Raises NotEnoughTextureSpace when the texture width and height
    wasn't big enough.
    Raises NameConflictException if name conflicts in some
    bones are detected.

    :param context: the execution context.
    '''
    for object in context.selected_objects:
        if object.type != 'ARMATURE':
            continue
        model_properties = object.mcblend_object_properties
        width = model_properties.texture_width
        height = model_properties.texture_height
        allow_expanding = model_properties.allow_expanding
        generate_texture = model_properties.generate_texture
        resolution = model_properties.texture_template_resolution

        mcblend_obj_group = McblendObjectGroup(object)
        mapper = UvMapper(width, height, mcblend_obj_group)
        mapper.plan_uv(allow_expanding)

        # Replace old mappings
        for objprop in mapper.uv_boxes:
            objprop.clear_uv_layers()


        # Update height and width
        if allow_expanding:
            widths = [width]
            heights = [height]
            for box in mapper.uv_boxes:
                widths.append(box.uv[0] + box.size[0])
                heights.append(box.uv[1] + box.size[1])
            height = max(heights)
            width = max(widths)

            model_properties.texture_height = height
            model_properties.texture_width = width

        if generate_texture:
            old_image = None
            if "template" in bpy.data.images:
                old_image = bpy.data.images['template']
            image = bpy.data.images.new(
                "template", width*resolution, height*resolution, alpha=True
            )
            if old_image is not None:
                # If exists remap users of old image and remove it
                old_image.user_remap(image)
                bpy.data.images.remove(old_image)
                image.name = "template"


            # This array represents new texture
            # DIM0:up axis DIM1:right axis DIM2:rgba axis
            arr = np.zeros([image.size[1], image.size[0], 4])

            for uv_cube in mapper.uv_boxes:
                uv_cube.paint_texture(arr, resolution)
            image.pixels = arr.ravel()  # Apply texture pixels values

        # Set blender UVs
        converter = CoordinatesConverter(
            np.array([[0, width], [0, height]]),
            np.array([[0, 1], [1, 0]])
        )
        for curr_uv in mapper.uv_boxes:
            curr_uv.new_uv_layer()
            curr_uv.set_blender_uv(converter)

def fix_uvs(context: bpy_types.Context) -> Tuple[int, int]:
    '''
    Fixes the UV-mapping of selected objects.

    Raises NoCubePolygonsException when one of the is not a cuboid.

    :param context: the execution context.

    :returns: The number of fixed cubes and the number of fixed faces.
    '''
    # TODO - now McblendObjectGroup is created from armature object not from
    # context. This operator needs to be changed.
    object_properties = McblendObjectGroup(context)
    total_fixed_uv_faces = 0
    total_fixed_cubes = 0

    for objprop in object_properties.values():
        if (
                objprop.obj_type != 'MESH' or
                objprop.mesh_type != MeshType.CUBE or
                objprop.obj_data.uv_layers.active is None):
            continue
        polygons = objprop.cube_polygons()
        uv_layer = objprop.obj_data.uv_layers.active
        fixed_faces = 0
        for polygon in polygons:
            crds = polygon.uv_layer_coordinates(uv_layer)
            if CubePolygon.validate_rectangle_uv(crds)[0]:
                continue  # The UVs are correct already

            # left down, right down, right up, left up
            max_ = crds.max(axis=0)
            min_ = crds.min(axis=0)
            expected = np.array([
                min_, [max_[0], min_[1]],
                max_, [min_[0], max_[1]]
            ])
            # Try connecting crds to the closest corners of the "bound box"
            # of the UV
            new_crds = np.empty((4,2))
            first_index: Optional[int] = None
            for i in range(4):
                distances = np.linalg.norm(expected-crds[i], axis=1)
                # First result of where, first (and only) coordinate -> [0][0]
                index = np.where(distances == np.min(distances))[0][0]
                if first_index is None:
                    first_index = index
                new_crds[i] = expected[index]

            if not (  # Still not valid. Rearrange based on left down
                np.allclose(new_crds, expected) or
                np.allclose(new_crds, expected[[1, 0, 3, 2]]) or  # flip left right
                np.allclose(new_crds, expected[[2, 3, 0, 1]]) or  # flip up down
                np.allclose(new_crds, expected[[3, 2, 1, 0]])  # flip both
            ):
                if first_index == 0:
                    new_crds = expected
                elif first_index == 1:
                    new_crds = expected[[1, 0, 3, 2]]
                elif first_index == 2:
                    new_crds = expected[[2, 3, 0, 1]]
                elif first_index == 3:
                    new_crds = expected[[3, 2, 1, 0]]
                else:
                    raise RuntimeError('Invalid state')
            # Apply new_crds to the UV
            ordered_loop_indices = np.array(
                polygon.side.loop_indices)[[polygon.order]]
            for i, loop_index in enumerate(ordered_loop_indices):
                uv_layer.data[loop_index].uv =  new_crds[i]
            fixed_faces += 1
        if fixed_faces > 0:
            total_fixed_cubes += 1
            total_fixed_uv_faces += fixed_faces
    return total_fixed_cubes, total_fixed_uv_faces


def round_dimensions(context: bpy_types.Context) -> int:
    '''
    Rounds dimensions of selected objects in such way that they'll be integers
    in exported Minecraft model.

    :param context: the context of running the operator.
    :returns: the number of edited objects.
    '''
    counter = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            # Clear parent from children for a moment
            children = obj.children
            for child in children:
                old_matrix = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = old_matrix

            # Set new dimensions
            dimensions = np.array(obj.dimensions)

            if obj.mcblend_object_properties.inflate != 0.0:
                dimensions -= (
                    obj.mcblend_object_properties.inflate * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            dimensions = np.array(
                dimensions * MINECRAFT_SCALE_FACTOR
            ).round() / MINECRAFT_SCALE_FACTOR
            if obj.mcblend_object_properties.inflate != 0.0:
                dimensions += (
                    obj.mcblend_object_properties.inflate * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            obj.dimensions = dimensions
            context.view_layer.update()

            # Add children back and set their previous transformations
            for child in children:
                child.parent = obj
                child.matrix_parent_inverse = obj.matrix_world.inverted()

            counter += 1
    return counter

def import_model(data: Dict, geometry_name: str, context: bpy_types.Context):
    '''
    Import and build model from JSON dict.

    :param data: JSON dict with minecraft model.
    :param geometry_name: the name of the geometry to load from the model.
    :param context: the context of running the operator.
    '''
    # :param replace_bones_with_empties: Whether to import bones as empties
    #     (True) or as armature and bones (False).

    geometry = ImportGeometry(ModelLoader(data, geometry_name))
    # TODO - add support for empties as bones again
    # if replace_bones_with_empties:
    #     geometry.build_with_empties(context)
    # else:
    armature = geometry.build_with_armature(context)
    model_properties = armature.mcblend_object_properties

    model_properties.texture_width = geometry.texture_width
    model_properties.texture_height = geometry.texture_height
    model_properties.visible_bounds_offset = geometry.visible_bounds_offset
    model_properties.visible_bounds_width = geometry.visible_bounds_width
    model_properties.visible_bounds_height = geometry.visible_bounds_height

    if geometry.identifier.startswith('geometry.'):
        # TODO - maybe just use the amrature name instead of that property?
        model_properties.model_name = geometry.identifier[9:]
        armature.name = geometry.identifier[9:]
    else:
        model_properties.model_name = geometry.identifier
        armature.name = geometry.identifier

def separate_mesh_cubes(context: bpy_types.Context):
    '''
    Separate selected object with meshes that use cuboids only by the lose
    parts. Rotate bound boxes of the objects to fit them to the rotation of the
    separated cubes.
    '''
    bpy.ops.mesh.separate(type='LOOSE')
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        apply_obj_transform_keep_origin(obj)
        bpy.context.view_layer.update()
        fix_cube_rotation(obj)

def inflate_objects(
        context: bpy_types.Context, objects: List[bpy.types.Object],
        inflate: float, mode: str) -> int:
    '''
    Adds inflate property to objects and changes their dimensions. Returns
    the number of edited objects.

    :param context: Context of running the operator.
    :param objects: List of objects to inflate.
    :param inflate: The inflation value.
    :param mode: Either "RELATIVE" or "ABSOLUTE". If "RELATIVE" than
        the value before applying the operator is taken as a base (0 means that
        no changes should be applied). If "ABSOLUTE" than the inflate value
        passed by the user is passed directly to the inflate value of
        Minecraft model.
    :returns: number of edited objects
    '''
    if mode == 'RELATIVE':
        relative = True
    elif mode == 'ABSOLUTE':
        relative = False
    else:
        raise ValueError(f'Unknown mode for set_inflate operator: {mode}')

    counter = 0
    for obj in objects:
        if (
                obj.type == 'MESH' and
                obj.mcblend_object_properties.mesh_type ==
                MeshType.CUBE.value):
            if obj.mcblend_object_properties.inflate != 0.0:
                if relative:
                    effective_inflate = (
                        obj.mcblend_object_properties.inflate + inflate)
                else:
                    effective_inflate = inflate
                delta_inflate = (
                    effective_inflate -
                    obj.mcblend_object_properties.inflate)
                obj.mcblend_object_properties.inflate = effective_inflate
            else:
                delta_inflate = inflate
                obj.mcblend_object_properties.inflate = inflate
            # Clear parent from children for a moment
            children = obj.children
            for child in children:
                old_matrix = child.matrix_world.copy()
                child.parent = None
                child.matrix_world = old_matrix

            dimensions = np.array(obj.dimensions)

            # Set new dimensions
            dimensions = (
                dimensions +
                (2*delta_inflate/MINECRAFT_SCALE_FACTOR)
            )

            obj.dimensions = dimensions
            context.view_layer.update()

            # Add children back and set their previous transformations
            for child in children:
                child.parent = obj
                child.matrix_parent_inverse = obj.matrix_world.inverted()

            counter += 1
    return counter

def reload_rp_entities(context: bpy_types.Context):
    '''
    Loads the names of the entities used in the resource pack.

    :param context: the context of running the operator.
    '''
    project = context.scene.mcblend_project
    project_entities = project.entities
    project_rcs = project.render_controllers
    rp_path: Path = Path(context.scene.mcblend_project.rp_path)

    # context.scene.mcblend_project.active_entity = -1
    project_entities.clear()
    project_rcs.clear()

    if not rp_path.exists() or rp_path.is_file():
        return
    p = Project()
    p.add_rp(ResourcePack(rp_path))
    # Loud entity data into project
    for rp_entity in p.rp_entities:
        new_entity = project_entities.add()
        new_entity.name = rp_entity.identifier

        # new_entity.textures: Collection[NameValuePair]
        for t in  rp_entity.textures:
            new_texture = new_entity.textures.add()
            new_texture.name = 'texture.' + t.short_name
            new_texture.value = t.identifier
        # new_entity.geometries: Collection[NameValuePair]
        for g in rp_entity.geometries:
            new_geometry = new_entity.geometries.add()
            new_geometry.name = 'geometry.' + g.short_name
            new_geometry.value = g.identifier
        # new_entity.materials: Collection[NameValuePair]
        for m in rp_entity.materials:
            new_material = new_entity.materials.add()
            new_material.name = 'material.' + m.short_name
            new_material.value = m.identifier
        # new_entity.render_controllers: Collection[JustName]
        for rc in rp_entity.render_controllers:
            new_rc = new_entity.render_controllers.add()
            new_rc.name = rc.identifier

    # Select existing entity for the entity_names enum of the Project
    if len(project_entities) > 0:
        entity = project_entities[0]
        project.entity_names = entity.name

    # Load render controller data into project
    for rc_file in p.rp_render_controllers:
        for rc in rc_file:
            new_rc = project_rcs.add()
            # new_rc.name: String
            new_rc.name = rc.json.parent_key
            # new_rc.geometry_molang: String
            new_rc.geometry_molang = rc.geometry
            # new_rc.texture_molang: String
            if len(rc.textures) > 0:  # Currently only one texture is allowed
                new_rc.texture_molang =  rc.textures[0]
            else:
                new_rc.texture_molang = ''
            # new_rc.materials: Collection[MaterialProperties]
            for k, v in rc.materials.items():
                material = new_rc.materials.add()
                material.name = k  # pattern
                material.value_molang = v
                material.owner_name = new_rc.name
            # new_rc.geometry_arrays: Collection[ArrayProperties]
            for array_name, array_v in rc.geometry_arrays.items():
                geo_array = new_rc.geometry_arrays.add()
                geo_array.name = array_name
                for i in array_v:
                    item = geo_array.items.add()
                    item.name = i
            # new_rc.texture_arrays: Collection[ArrayProperties]
            for array_name, array_v in rc.texture_arrays.items():
                texture_array = new_rc.texture_arrays.add()
                texture_array.name = array_name
                for i in array_v:
                    item = texture_array.items.add()
                    item.name = i
            # new_rc.material_arrays: Collection[ArrayProperties]
            for array_name, array_v in rc.material_arrays.items():
                material_array = new_rc.material_arrays.add()
                material_array.name = array_name
                for i in array_v:
                    item = material_array.items.add()
                    item.name = i

# TODO - maybe move some of this code somewhere else... it's getting pretty
# long and hard to read. This files is meant to be short and contain only
# the most important functions for operators
def star_pattern_match(text: str, pattern: str) -> bool:
    '''
    Matches text with a pattern that uses "*" as a wildcard which
    can represent any number of characters.

    :param pattern: the pattern
    :param text: the text being matched with pattern
    '''
    lenp, lent = len(pattern), len(text)

    # Only empty text can match empty pattern
    if lenp == 0:
        return lent == 0

    # The table that represents matching smaller patterns to
    # parts of the text. Row 0 is for empty pattern, column 0
    # represents empty text: matches[text+1][pattern+1]
    matches = [[False for i in range(lenp + 1)] for j in range(lent + 1)]

    # Empty pattern matches the empty string
    matches[0][0] = True

    # Only paterns made out of '*' can match empty stirng
    for p in range(1, lenp+1):
        # Propagate matching apttern as long as long as the
        # pattern uses only '*'
        if pattern[p - 1] == '*':
            matches[0][p] = matches[0][p - 1]
        else:
            break
    # Fill the pattern matching table (solutions to
    # shorter patterns/texts are used to solve
    # other patterns with increasing complexity).
    for t in range(1, lent + 1):
        for p in range(1, lenp + 1):
            if pattern[p - 1] == '*':
                # Two wys to propagate matching value
                # A) Same pattern without '*' worked so this also works
                # B) Shorter text matched this pattern, and it ends with '*'
                # so adding characters doesn't change anything
                matches[t][p] = (
                    matches[t][p - 1] or
                    matches[t - 1][p]
                )
            elif pattern[p -1] == text[t - 1]:
                # One way to propagate matching value
                # If the pattern with one less character matched the text
                # with one less character (and we have a matching pair now)
                # then this pattern also matches
                matches[t][p] = matches[t - 1][p - 1]
            else:
                matches[t][p] = False  # no match, always false
    return matches[lent][lenp]  # return last matched pattern

@dataclass
class RcStackItem:
    '''
    Properties of a render controller.
    '''
    texture: Optional[Image]
    '''The image with the textue'''
    materials: Dict[str, str] = field(default_factory=dict)
    '''Materials dict with pattern keys and full material names values.'''

def import_model_form_project(context: bpy_types.Context):
    '''
    Imports model using data selected in Project menu.
    '''
    # 1. Load cached data
    cached_project = context.scene.mcblend_project
    # 2. Open project
    rp_path: Path = Path(cached_project.rp_path)
    if not rp_path.exists() or rp_path.is_file():
        raise ValueError("Invalid resource pack path.")
    p = Project()
    p.add_rp(ResourcePack(rp_path))

    # 3. Load the cached entity data
    cached_entity = cached_project.entities[cached_project.entity_names]
    # 5. Unpack the data (get full IDs instead of short names) from render
    # controllers into a single object and group it by used geometry.
    geo_rc_stacks: Dict[str, List[RcStackItem]] = defaultdict(list)
    for rc_name in cached_entity.render_controllers.keys():
        if rc_name in cached_project.render_controllers.keys():
            cached_rc = cached_project.render_controllers[rc_name]
        else:
            cached_rc = cached_project.fake_render_controllers[rc_name]
        texture_keys = cached_entity.textures.keys()
        if cached_rc.texture in cached_entity.textures.keys():
            texture_name = cached_entity.textures[cached_rc.texture].value
            texture = bpy.data.images.load(  # TODO - what if there is no image file?
                p.rp_texture_files[:texture_name:0].path.as_posix())
        new_rc_stack_item = RcStackItem(texture)
        if cached_rc.geometry not in cached_entity.geometries:
            raise ValueError(
                f"The render controller uses a geometry {cached_rc.geometry} "
                "undefined by the selected entity")
        geo_rc_stacks[
            cached_entity.geometries[cached_rc.geometry].value
        ].append(new_rc_stack_item)
        for material in cached_rc.materials:
            if material.value in cached_entity.materials.keys():
                material_full_name = cached_entity.materials[
                    material.value].value
            else:
                material_full_name = "entity_alphatest"  # default
            # (pattern: full identifier) pair
            new_rc_stack_item.materials[material.name] = material_full_name

    # 7. Load every geometry
    # blender_materials - Prevents creating same material multiple times
    # it's a dictionary of materials which uses a tuple with pairs of
    # names of the texutes and minecraft materials as the identifiers
    # of the material to create.
    blender_materials: Dict[Tuple[Tuple[str, str], ...], Material] = {}
    for geo_name, rc_stack in geo_rc_stacks.items():
        geometry_data: Dict = p.rp_models[:geo_name:0].json.data  # type: ignore
        # Import model
        geometry = ImportGeometry(ModelLoader(geometry_data, geo_name))
        armature = geometry.build_with_armature(context)

        # 7.1. Set proper textures resolution and model bounds
        model_properties = armature.mcblend_object_properties

        model_properties.texture_width = geometry.texture_width
        model_properties.texture_height = geometry.texture_height
        model_properties.visible_bounds_offset = geometry.visible_bounds_offset
        model_properties.visible_bounds_width = geometry.visible_bounds_width
        model_properties.visible_bounds_height = geometry.visible_bounds_height
        if geometry.identifier.startswith('geometry.'):
            model_properties.model_name = geometry.identifier[9:]
            armature.name = geometry.identifier[9:]
        else:
            model_properties.model_name = geometry.identifier
            armature.name = geometry.identifier
        # 7.2. Save render controller properties in the armature
        for rc_stack_item in rc_stack:
            armature_rc = armature.mcblend_object_properties.\
                render_controllers.add()
            armature_rc.texture = rc_stack_item.texture.name
            for pattern, material in rc_stack_item.materials.items():
                armature_rc_material = armature_rc.materials.add()
                armature_rc_material.pattern = pattern
                armature_rc_material.material = material

        # 7.3. For every bone of geometry, create blender material from.
        # Materials are created from a list of pairs:
        # (Image, minecraft material)
        for bone_name, bone in geometry.bones.items():
            # Create a list of materials applicable for this bone
            bone_materials: List[Tuple[Image, str]] = []
            bone_materials_id: List[Tuple[Image, str]] = []
            for rc_stack_item in reversed(rc_stack):
                matched_material: Optional[str] = None
                for pattern, material in rc_stack_item.materials.items():
                    if star_pattern_match(bone_name, pattern):
                        matched_material = material
                # Add material to bone_materials only if something matched
                if matched_material is not None:
                    bone_materials.append(
                        (rc_stack_item.texture, matched_material))
                    bone_materials_id.append(
                        (rc_stack_item.texture.name, matched_material))
            if len(bone_materials) == 0:  # No material for this bone!
                continue
            try:  # try to use existing material
                material = blender_materials[tuple(bone_materials_id)]
            except:  # create material
                material = create_bone_material("MC_Material", bone_materials)
                blender_materials[tuple(bone_materials_id)] = material
            for c in bone.cubes:
                if c.blend_cube is None:
                    continue
                c.blend_cube.data.materials.append(
                    blender_materials[tuple(bone_materials_id)])

def apply_materials(context: bpy.types.Context):
    '''
    Applies materials from render controller menu into the model.

    :param context: the context of running the operator.
    '''
    blender_materials: Dict[Tuple[Tuple[str, str], ...], Material] = {}
    for armature in context.selected_objects:
        if armature.type != 'ARMATURE':
            continue
        mcblend_obj_group = McblendObjectGroup(armature)
        armature_properties = armature.mcblend_object_properties

        model = ModelExport(
            texture_width=armature_properties.texture_width,
            texture_height=armature_properties.texture_height,
            visible_bounds_offset=tuple(  # type: ignore
                armature_properties.visible_bounds_offset),
            visible_bounds_width=armature_properties.visible_bounds_width,
            visible_bounds_height=armature_properties.visible_bounds_height,
            model_name=armature_properties.model_name,
        )
        model.load(mcblend_obj_group)
        for bone in model.bones:
            # Create a list of materials applicable for this bone
            bone_materials: List[Tuple[Image, str]] = []
            bone_materials_id: List[Tuple[Image, str]] = []


            for rc in reversed(armature_properties.render_controllers):
                texture: Optional[Image] = None
                if rc.texture in bpy.data.images:
                    texture = bpy.data.images[rc.texture]
                rc_stack_item = RcStackItem(texture)
                for rc_material in rc.materials:
                    rc_stack_item.materials[
                        rc_material.pattern] = rc_material.material

                matched_material: Optional[str] = None
                for pattern, material in rc_stack_item.materials.items():
                    if star_pattern_match(bone.name, pattern):
                        matched_material = material
                # Add material to bone_materials only if something matched
                if matched_material is not None:
                    bone_materials.append(
                        (rc_stack_item.texture, matched_material))
                    bone_materials_id.append(
                        (rc_stack_item.texture.name, matched_material))
            if len(bone_materials) == 0:  # No material for this bone!
                continue
            try:  # try to use existing material
                material = blender_materials[tuple(bone_materials_id)]
            except:  # create material
                material = create_bone_material("MC_Material", bone_materials)
                blender_materials[tuple(bone_materials_id)] = material
            for c in bone.cubes:
                c.mcblend_obj.obj_data.materials.clear()
                c.mcblend_obj.obj_data.materials.append(
                    blender_materials[tuple(bone_materials_id)])
            for p in bone.poly_mesh.mcblend_objs:
                p.mcblend_obj.obj_data.materials.clear()
                p.mcblend_obj.obj_data.materials.append(
                    blender_materials[tuple(bone_materials_id)])
