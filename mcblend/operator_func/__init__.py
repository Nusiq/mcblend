'''
Functions used directly by the blender operators.
'''
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional
import math
from enum import Enum

import numpy as np

import bpy
import mathutils
import bpy_types

from .uv import UvMcCube, UvMapper, UvGroup, CoordinatesConverter
from .animation import AnimationExport
from .model import ModelExport
from .json_tools import get_vect_json
from .common import (
    MCObjType, ObjectId, McblendObject, MINECRAFT_SCALE_FACTOR,
    McblendObjectGroup, inflate_objets
)
from .importer import ImportGeometry, ModelLoader
from .exception import NameConflictException


def export_model(context: bpy_types.Context) -> Dict:
    '''
    Creates a Minecraft model (dictionary) from selected objects.
    Raises NameConflictException if name conflicts in some bones are detected.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.

    # Returns:
    `Dict` - a dictionary with the model..
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
    Raises NameConflictException if name conflicts in some bones are detected.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.
    - `old_dict: Optional[Dict]` - optional argument dictionary that represents
      the JSON file with animations.

    # Returns:
    `Dict` - a dictionary with the animation.
    '''
    # Check and create object properties
    object_properties = McblendObjectGroup(context)

    animation = AnimationExport(
        name=context.scene.nusiq_mcblend.animation_name,
        length=(context.scene.frame_end-1)/context.scene.render.fps,
        loop_animation=context.scene.nusiq_mcblend.loop_animation,
        anim_time_update=context.scene.nusiq_mcblend.anim_time_update,
        fps=context.scene.render.fps
    )
    animation.load_poses(object_properties, context)
    return animation.json(old_json=old_dict)


def set_uvs(context: bpy_types.Context):
    '''
    Used by the operator that sets UV. Calculates the UV-map for selected
    objects. Raises NotEnoughTextureSpace when the texture width and height
    wasn't big enough. Raises NameConflictException if name conflicts in some
    bones are detected.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.
    '''
    width = context.scene.nusiq_mcblend.texture_width
    height = context.scene.nusiq_mcblend.texture_height

    resolution = context.scene.nusiq_mcblend.texture_template_resolution
    if height <= 0:
        height = None

    object_properties = McblendObjectGroup(context)
    mapper = UvMapper(width, height)
    mapper.load_uv_boxes(object_properties, context)
    mapper.plan_uv()

    # Replace old mappings
    for objprop in mapper:
        objprop.clear_uv_layers()

    if height is None:
        new_height = max([i.uv[1] + i.size[1] for i in mapper.uv_boxes])
    else:
        new_height = height
    context.scene.nusiq_mcblend.texture_height = new_height

    if resolution >= 1:
        image = bpy.data.images.new(
            "template", width*resolution, new_height*resolution, alpha=True
        )

        # This array represents new texture
        # DIM0:up axis DIM1:right axis DIM2:rgba axis
        arr = np.zeros([image.size[1], image.size[0], 4])

        for uv_cube in mapper.uv_boxes:
            uv_cube.paint_texture(arr, resolution)
        image.pixels = arr.ravel()  # Apply texture pixels values

    # Set blender UVs
    converter = CoordinatesConverter(
        np.array([[0, width], [0, new_height]]),
        np.array([[0, 1], [1, 0]])
    )
    for curr_uv in mapper.uv_boxes:
        curr_uv.new_uv_layer()
        curr_uv.set_blender_uv(converter)

def set_inflate(context: bpy_types.Context, inflate: float, mode: str) -> int:
    '''Run common.inflate_objets function.'''
    return inflate_objets(context, context.selected_objects, inflate, mode)


def round_dimensions(context: bpy_types.Context) -> int:
    '''
    Rounds dimensions of selected objects so they are whole numbers in
    Minecraft model. Returns the number of edited objects.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.

    # Returns:
    `int` - the number of edited objects.
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
            if 'mc_inflate' in obj:
                dimensions -= (
                    obj['mc_inflate'] * 2 /
                    MINECRAFT_SCALE_FACTOR
                )
            dimensions = np.array(
                dimensions * MINECRAFT_SCALE_FACTOR
            ).round() / MINECRAFT_SCALE_FACTOR
            if 'mc_inflate' in obj:
                dimensions += (
                    obj['mc_inflate'] * 2 /
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
    Import and build model from JSON file.

    # Arguments:
    - `data: Dict` - a dictionary with data loaded from JSON file.
    - `geometry_name: str` - the name of the geometry that should be loaded
       into Blender.
    - `replace_bones_with_empties: bool` - imports model bones as empties
      instead of armatrue and bones
    - `context: bpy_types.Context` - the context of running the operator.
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
