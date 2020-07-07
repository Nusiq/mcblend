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
    McblendObjectGroup
)
from .importer import load_model, build_geometry, assert_is_model
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

    # Remove old mappings
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
    '''
    Adds mc_inflate property to objects and changes their dimensions. Returns
    the number of edited objects.
    Returns the number of edited objects.

    # Arguments:
    - `context: bpy_types.Context` - the context of running the operator.
    - `inflate: float` - the inflation value.
    - `mode: str` - Can be either "RELATIVE" or "ABSOLUTE". If "RELATIVE" than
      the value before appying the operator is taken as a base (0 means that
      no changes should be applied). If "ABSOLUTE" than the inflate value passed
      by the user is passed directly to the inflate value in Minecraft model.

    # Returns:
    `bool` - the success value of the function.
    '''
    if mode == 'RELATIVE':
        relative = True
    elif mode == 'ABSOLUTE':
        relative = False
    else:
        raise ValueError(f'Unknown mode for set_inflate operator: {mode}')

    counter = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            if 'mc_inflate' in obj:
                if relative:
                    effective_inflate = obj['mc_inflate'] + inflate
                else:
                    effective_inflate = inflate
                delta_inflate = effective_inflate - obj['mc_inflate']
                obj['mc_inflate'] = effective_inflate
            else:
                delta_inflate = inflate
                obj['mc_inflate'] = inflate
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

            # Remove the property if it's equal to 0
            if obj['mc_inflate'] == 0:
                del obj['mc_inflate']

            counter += 1
    return counter


def round_dimensions(context: bpy_types.Context) -> int:
    '''
    Rounds dimensions of selected objects so they are the whole numbers in
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
        data: Dict, geometry_name: str, context: bpy_types.Context
    ):
    '''
    Import and build model from JSON file.

    # Arguments:
    - `data: Dict` - a dictionary with data loaded from JSON file.
    - `geometry_name: str` - the name of the geometry that should be loaded
       into Blender.
    - `context: bpy_types.Context` - the context of running the operator.
    '''
    assert_is_model(data)
    geometry = load_model(data, geometry_name)
    build_geometry(geometry, context)

    context.scene.nusiq_mcblend.texture_width = geometry.texture_width
    context.scene.nusiq_mcblend.texture_height = geometry.texture_height

    if geometry.identifier.startswith('geometry.'):
        context.scene.nusiq_mcblend.model_name = geometry.identifier[9:]
    else:
        context.scene.nusiq_mcblend.model_name = geometry.identifier
