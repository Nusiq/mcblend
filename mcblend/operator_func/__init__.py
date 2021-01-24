'''
Functions used directly by the blender operators.
'''
from __future__ import annotations

from typing import Dict, Optional, List

import numpy as np

import bpy
import bpy_types

from .uv import UvMapper, CoordinatesConverter
from .animation import AnimationExport
from .model import ModelExport
from .common import (
    MINECRAFT_SCALE_FACTOR, McblendObjectGroup, MeshType,
    apply_obj_transform_keep_origin, fix_cube_rotation)
from .importer import ImportGeometry, ModelLoader


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
    model.load(object_properties, context)
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
    mapper = UvMapper(width, height)
    mapper.load_uv_boxes(object_properties, context)
    mapper.plan_uv(allow_expanding)

    # Replace old mappings
    for objprop in mapper:
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
