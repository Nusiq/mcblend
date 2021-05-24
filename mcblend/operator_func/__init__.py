'''
Functions used directly by the blender operators.
'''
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import bpy
import bpy_types
import numpy as np

from .animation import AnimationExport
from .bedrock_packs import Project, ResourcePack
from .common import (
    MINECRAFT_SCALE_FACTOR, CubePolygon, McblendObjectGroup, MeshType,
    apply_obj_transform_keep_origin, fix_cube_rotation)
from .importer import ImportGeometry, ModelLoader
from .material import create_material
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
    object_properties = McblendObjectGroup(context)

    model = ModelExport(
        texture_width=context.scene.nusiq_mcblend.texture_width,
        texture_height=context.scene.nusiq_mcblend.texture_height,
        visible_bounds_offset=tuple(  # type: ignore
            context.scene.nusiq_mcblend.visible_bounds_offset),
        visible_bounds_width=context.scene.nusiq_mcblend.visible_bounds_width,
        visible_bounds_height=context.scene.nusiq_mcblend.visible_bounds_height,
        model_name=context.scene.nusiq_mcblend.model_name,
    )
    model.load(object_properties)
    return model.json()

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
    object_properties = McblendObjectGroup(context)

    anim_data = context.scene.nusiq_mcblend_animations[
        context.scene.nusiq_mcblend_active_animation]

    animation = AnimationExport(
        name=anim_data.name,
        length=(context.scene.frame_end-1)/context.scene.render.fps,
        loop_animation=anim_data.loop,
        single_frame=anim_data.single_frame,
        anim_time_update=anim_data.anim_time_update,
        fps=context.scene.render.fps,
        effect_events={
            event.name: event.get_effects_dict()
            for event in context.scene.nusiq_mcblend_events
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
    width = context.scene.nusiq_mcblend.texture_width
    height = context.scene.nusiq_mcblend.texture_height
    allow_expanding = context.scene.nusiq_mcblend.allow_expanding
    generate_texture = context.scene.nusiq_mcblend.generate_texture
    resolution = context.scene.nusiq_mcblend.texture_template_resolution

    object_properties = McblendObjectGroup(context)
    mapper = UvMapper(width, height, object_properties)
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

        context.scene.nusiq_mcblend.texture_height = height
        context.scene.nusiq_mcblend.texture_width = width

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

            if obj.nusiq_mcblend_object_properties.inflate != 0.0:
                dimensions -= (
                    obj.nusiq_mcblend_object_properties.inflate * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            dimensions = np.array(
                dimensions * MINECRAFT_SCALE_FACTOR
            ).round() / MINECRAFT_SCALE_FACTOR
            if obj.nusiq_mcblend_object_properties.inflate != 0.0:
                dimensions += (
                    obj.nusiq_mcblend_object_properties.inflate * 2 /
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

def import_model(
        data: Dict, geometry_name: str, replace_bones_with_empties: bool,
        context: bpy_types.Context
    ):
    '''
    Import and build model from JSON dict.

    :param data: JSON dict with minecraft model.
    :param geometry_name: the name of the geometry to load from the model.
    :param replace_bones_with_empties: Whether to import bones as empties
        (True) or as armature and bones (False).
    :param context: the context of running the operator.
    '''
    geometry = ImportGeometry(ModelLoader(data, geometry_name))
    if replace_bones_with_empties:
        geometry.build_with_empties(context)
    else:
        geometry.build_with_armature(context)

    context.scene.nusiq_mcblend.texture_width = geometry.texture_width
    context.scene.nusiq_mcblend.texture_height = geometry.texture_height
    context.scene.nusiq_mcblend.visible_bounds_offset = geometry.visible_bounds_offset
    context.scene.nusiq_mcblend.visible_bounds_width = geometry.visible_bounds_width
    context.scene.nusiq_mcblend.visible_bounds_height = geometry.visible_bounds_height

    if geometry.identifier.startswith('geometry.'):
        context.scene.nusiq_mcblend.model_name = geometry.identifier[9:]
    else:
        context.scene.nusiq_mcblend.model_name = geometry.identifier

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
                obj.nusiq_mcblend_object_properties.mesh_type ==
                MeshType.CUBE.value):
            if obj.nusiq_mcblend_object_properties.inflate != 0.0:
                if relative:
                    effective_inflate = (
                        obj.nusiq_mcblend_object_properties.inflate + inflate)
                else:
                    effective_inflate = inflate
                delta_inflate = (
                    effective_inflate -
                    obj.nusiq_mcblend_object_properties.inflate)
                obj.nusiq_mcblend_object_properties.inflate = effective_inflate
            else:
                delta_inflate = inflate
                obj.nusiq_mcblend_object_properties.inflate = inflate
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
    project = context.scene.nusiq_mcblend_project
    project_entities = project.entities
    rp_path: Path = Path(context.scene.nusiq_mcblend_project.rp_path)

    # context.scene.nusiq_mcblend_project.active_entity = -1
    project_entities.clear()

    if not rp_path.exists() or rp_path.is_file():
        return
    p = Project()
    p.add_rp(ResourcePack(rp_path))
    for rp_entity in p.rp_entities:
        new_entity = project_entities.add()
        new_entity.name = rp_entity.identifier
        for t in  rp_entity.textures:
            new_texture = new_entity.textures.add()
            new_texture.name = t.short_name
            new_texture.value = t.identifier
        for g in rp_entity.geometries:
            new_geometry = new_entity.geometries.add()
            new_geometry.name = g.short_name
            new_geometry.value = g.identifier
        for m in rp_entity.materials:
            new_material = new_entity.materials.add()
            new_material.name = m.short_name
            new_material.value = m.identifier
        for rc in rp_entity.render_controllers:
            new_rc = new_entity.render_controllers.add()
            new_rc.name = rc.identifier

    # Set the project enum values to existing enum members
    if len(project_entities) > 0:
        entity = project_entities[0]
        project.entity_names = entity.name
        if len(entity.render_controllers) > 0:
            project.render_controller_names = entity.render_controllers[0].name
        if len(entity.geometries) > 0:
            project.geometry_names = entity.geometries[0].name
        if len(entity.textures) > 0:
            project.texture_names = entity.textures[0].name


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


def import_model_form_project(
        replace_bones_with_empties: bool, context: bpy_types.Context):
    '''
    Imports model using data selected in Project menu.
    '''
    project = context.scene.nusiq_mcblend_project
    # project_entities = project.entities

    rp_path: Path = Path(context.scene.nusiq_mcblend_project.rp_path)
    if not rp_path.exists() or rp_path.is_file():
        raise ValueError("Invalid resource pack path.")
    p = Project()
    p.add_rp(ResourcePack(rp_path))

    entity_name: str = project.entity_names
    entity = project.entities[entity_name]

    geo_short_name: str = project.geometry_names
    geo_name = entity.geometries[geo_short_name].value

    render_controller_name: str = project.render_controller_names

    texture_short_name: str = project.texture_names
    texture_name: str = entity.textures[texture_short_name].value

    # Find model
    geometry_data: Dict = p.rp_models[:geo_name:0].json.data  # type: ignore
    # Find render controller and it's materials
    material_map: Dict[str, str] = {}
    try:
        rc_data = p.rp_render_controllers[
            :render_controller_name:0]  # type: ignore
        for mat in rc_data.materials:
            if mat.array is not None:
                continue  # array reference to material (not supported)
            if mat.render_controller != render_controller_name:
                continue  # different render controller from the same file
            mat_pattern: str = mat.json.parent_key  # type: ignore
            if mat.short_name[9:] in entity.materials:
                mat_name: str = (
                    entity.materials[mat.short_name[9:]].value)
            else:
                mat_name = 'entity_alphatest'  # default material
            material_map[mat_pattern] = mat_name
    except KeyError:  # unable to load render controller
        pass

    if len(material_map) == 0:
        material_map = {"*": "entity_alphatest"}


    # Import model
    geometry = ImportGeometry(ModelLoader(geometry_data, geo_name))
    if replace_bones_with_empties:
        geometry.build_with_empties(context)
    else:
        geometry.build_with_armature(context)

    context.scene.nusiq_mcblend.texture_width = geometry.texture_width
    context.scene.nusiq_mcblend.texture_height = geometry.texture_height
    context.scene.nusiq_mcblend.visible_bounds_offset = geometry.visible_bounds_offset
    context.scene.nusiq_mcblend.visible_bounds_width = geometry.visible_bounds_width
    context.scene.nusiq_mcblend.visible_bounds_height = geometry.visible_bounds_height
    # Import texture
    try:
        texture_file = p.rp_texture_files[
            :texture_name:0]  # type: ignore
        texture = bpy.data.images.load(str(texture_file.path))
    except KeyError:
        texture = None # unable to find texture file

    # Create blender materials
    blender_materials = {}
    for v in material_map.values():
        if v in blender_materials:
            continue
        blender_materials[v] = create_material(v, texture)

    if geometry.identifier.startswith('geometry.'):
        context.scene.nusiq_mcblend.model_name = geometry.identifier[9:]
    else:
        context.scene.nusiq_mcblend.model_name = geometry.identifier
    # Connect materials to the model
    for bone_name, bone in geometry.bones.items():
        matched_material = ''
        for pattern, material in material_map.items():
            # If nothing matches just use the first material
            if matched_material is None:
                matched_material = material
            elif star_pattern_match(bone_name, pattern):
                # Later materials can overwrite
                matched_material = material
        for c in bone.cubes:
            if c.blend_cube is None:
                continue
            c.blend_cube.data.materials.append(
                blender_materials[matched_material]
            )
