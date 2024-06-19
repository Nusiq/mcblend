'''
Functions used directly by the blender operators.
'''
from __future__ import annotations

from pathlib import Path
from typing import (
    Dict, Iterable, List, Literal, Optional, Tuple, cast, Callable, Any)
from dataclasses import dataclass, field
from collections import defaultdict

import bpy
from bpy.types import Image, Material, Context, Object, Armature, Mesh
import numpy as np

from .common import ModelOriginType
from .typed_bpy_access import (
    get_mcblend_project,
    get_mcblend_events,
    get_mcblend)

from .sqlite_bedrock_packs.better_json_tools import load_jsonc

from .animation import AnimationExport
from .common import (
    MINECRAFT_SCALE_FACTOR, CubePolygon, McblendObject, McblendObjectGroup, MeshType,
    apply_obj_transform_keep_origin, fix_cube_rotation, star_pattern_match,
    MCObjType)
from .extra_types import Vector2di
from .importer import ImportGeometry, ModelLoader
from .material import create_bone_material
from .model import ModelExport
from .uv import CoordinatesConverter, UvMapper, UvModelMerger
from .db_handler import get_db_handler
from .rp_importer import PksForModelImport

def export_model(
        context: Context) -> Tuple[Dict[str, Any], Iterable[str]]:
    '''
    Creates a Minecraft model JSON dict from selected objects.

    :param context: the context of running the operator.
    :returns: JSON dict with Minecraft model and a generator that yields
        warnings about exporting.
    '''
    result = ModelExport.json_outer()
    armature = context.object  # an armature
    if armature is None or armature.type != 'ARMATURE':
        # Should never happen (checked in the operator)
        raise ValueError("Selected object is not an armature")
    
    origin: Optional[Object] = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        origin = armature
    mcblend_obj_group = McblendObjectGroup(armature, origin)
    model_properties = get_mcblend(armature)

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
    return result, model.yield_warnings()

def export_animation(
        context: Context, old_dict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
    '''
    Creates a Minecraft animation (dictionary) from selected objects.

    :param context: the context of running the operator.
    :param old_dict: optional - JSON dict with animation to write into.
    :returns: JSON dict of Minecraft animations.
    '''
    armature = context.object  # an armature
    if armature is None or armature.type != 'ARMATURE':
        # Should never happen (checked in the operator)
        raise ValueError("Selected object is not an armature")
    anim_data = get_mcblend(armature).animations[
        get_mcblend(armature).active_animation]

    # TODO - write this code nicer, passing world_origin as a string isn't
    # a perfect solution
    world_origin = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        world_origin = armature

    # Check and create object properties
    object_properties = McblendObjectGroup(armature, world_origin)

    animation = AnimationExport(
        name=anim_data.name,
        length=(context.scene.frame_end-1)/context.scene.render.fps,
        loop_animation=anim_data.loop,
        single_frame=anim_data.single_frame,
        anim_time_update=anim_data.anim_time_update,
        override_previous_animation=anim_data.override_previous_animation,
        fps=context.scene.render.fps,
        effect_events={
            event.name: event.get_effects_dict()
            for event in get_mcblend_events(context.scene)
        }
    )
    animation.load_poses(object_properties, context)
    return animation.json(
        old_json=old_dict, skip_rest_poses=anim_data.skip_rest_poses)

def set_uvs(context: Context):
    '''
    Maps the UV for selected objects.

    Raises NotEnoughTextureSpace when the texture width and height
    wasn't big enough.

    :param context: the execution context.
    '''
    armature = context.object # an armature
    if armature is None or armature.type != 'ARMATURE':
        # Should never happen (checked in the operator)
        raise ValueError("Selected object is not an armature")
    model_properties = get_mcblend(armature)
    width = model_properties.texture_width
    height = model_properties.texture_height
    allow_expanding = model_properties.allow_expanding
    generate_texture = model_properties.generate_texture
    resolution = model_properties.texture_template_resolution

    origin = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        origin = armature
    mcblend_obj_group = McblendObjectGroup(armature, origin)
    mapper = UvMapper(width, height)
    mapper.append_for_uv_mapping(mcblend_obj_group)
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

def fix_uvs(context: Context) -> Vector2di:
    '''
    Fixes the UV mapping of selected objects.

    Raises ExporterException when one of the is not a cuboid.

    :param context: the execution context.

    :returns: The number of fixed cubes and the number of fixed faces.
    '''
    armature = context.object  # an armature
    if armature is None or armature.type != 'ARMATURE':
        # Should never happen (checked in the operator)
        raise ValueError("Selected object is not an armature")

    origin: Object | None = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        origin = armature
    object_properties = McblendObjectGroup(armature, origin)
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
                polygon.side.loop_indices)[polygon.order,]
            for i, loop_index in enumerate(ordered_loop_indices):
                uv_layer.data[loop_index].uv =  new_crds[i]
            fixed_faces += 1
        if fixed_faces > 0:
            total_fixed_cubes += 1
            total_fixed_uv_faces += fixed_faces
    return total_fixed_cubes, total_fixed_uv_faces

def import_model(
        data: Dict[str, Any], geometry_name: str, context: Context
) -> List[str]:
    '''
    Import and build model from JSON dict.

    :param data: JSON dict with minecraft model.
    :param geometry_name: the name of the geometry to load from the model.
    :param context: the context of running the operator.

    :returns: list of warnings
    '''
    model_loader = ModelLoader(data, geometry_name)
    geometry = ImportGeometry(model_loader)
    armature = geometry.build_with_armature(context)
    model_properties = get_mcblend(armature)

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
    return model_loader.warnings

def separate_mesh_cubes(context: Context):
    '''
    Separate selected object with meshes that use cuboids only by the lose
    parts. Rotate bound boxes of the objects to fit them to the rotation of the
    separated cubes.

    :returns: the number of created objects
    '''
    bpy.ops.mesh.separate(type='LOOSE')  # pyright: ignore[reportUnknownMemberType]
    edited_objects = len(context.selected_objects)
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
        apply_obj_transform_keep_origin(obj)
        bpy.context.view_layer.update()
        fix_cube_rotation(obj)
    return edited_objects

def inflate_objects(
        context: Context, objects: List[Object],
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
                get_mcblend(obj).mesh_type ==
                MeshType.CUBE.value):
            if get_mcblend(obj).inflate != 0.0:
                if relative:
                    effective_inflate = (
                        get_mcblend(obj).inflate + inflate)
                else:
                    effective_inflate = inflate
                delta_inflate = (
                    effective_inflate -
                    get_mcblend(obj).inflate)
                get_mcblend(obj).inflate = effective_inflate
            else:
                delta_inflate = inflate
                get_mcblend(obj).inflate = inflate
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
            obj.dimensions = cast(list[float], dimensions)
            context.view_layer.update()

            # Add children back and set their previous transformations
            for child in children:
                child.parent = obj
                child.matrix_parent_inverse = obj.matrix_world.inverted()

            counter += 1
    return counter

def load_rp_to_mcblned(
        context: Context, path: Path):
    '''
    Loads the resource pack to the mcblend dadtabase.

    :param context: the context of running the operator.
    :param path: path to the resource pack.
    '''
    mcblend_project = get_mcblend_project(context.scene)
    # Cleared cached data for GUI it will be reloaded later
    # Clear cached entity data
    mcblend_project.entities.clear()
    mcblend_project.selected_entity = ''
    mcblend_project.entity_render_controllers.clear()
    # Clear cached attachable data
    mcblend_project.attachables.clear()
    mcblend_project.selected_attachable = ''
    mcblend_project.attachable_render_controllers.clear()

    db_handler = get_db_handler()
    if not path.exists():
        return
    db_handler.load_resource_pack(path)

    # Load entity data
    duplicate_counter: int = 1
    last_name: Optional[str] = None
    for pk, name in db_handler.list_entities_with_models_and_rc():
        entity = mcblend_project.entities.add()
        # Add primary key property
        entity.primary_key = pk
        # Add name (if duplicated add index to it)
        if name == last_name:
            duplicate_counter += 1
            entity.name = f'{name} ({duplicate_counter})'
        else:
            duplicate_counter = 1
            entity.name = name
        last_name = name

    # Load attachable data
    duplicate_counter: int = 1
    last_name: Optional[str] = None
    for pk, name in db_handler.list_attachables_with_models_and_rc():
        attachable = mcblend_project.attachables.add()
        # Add primary key property
        attachable.primary_key = pk
        # Add name (if duplicated add index to it)
        if name == last_name:
            duplicate_counter += 1
            attachable.name = f'{name} ({duplicate_counter})'
        else:
            duplicate_counter = 1
            attachable.name = name
        last_name = name

def unload_rps(context: Context):
    '''
    Unload resrouce pakcs in GUI.
    '''
    mcblend_project = get_mcblend_project(context.scene)
    mcblend_project.entity_render_controllers.clear()
    mcblend_project.entities.clear()
    mcblend_project.selected_entity = ''
    db_handler = get_db_handler()
    db_handler.delete_db()

@dataclass
class RcStackItem:
    '''
    Properties of a render controller.
    '''
    texture: Optional[Image]
    '''The image with the textue'''
    materials: Dict[str, str] = field(default_factory=dict)
    '''Materials dict with pattern keys and full material names values.'''

def import_model_form_project(
        context: Context,
        import_type: Literal['entity', 'attachable'],
        query_data: PksForModelImport) -> List[str]:
    '''
    Imports model using data selected in Project menu.

    :returns: list of warnings
    '''
    # 1. Create RcStackItems
    db_handler = get_db_handler()
    pk = query_data['pk']
    geo_rc_stacks: Dict[int, List[RcStackItem]] = defaultdict(list)
    for render_controller_data in query_data['render_controllers']:
        try:
            # texture - Optional[Image] (bpy.types.Image)
            texture_file_path = db_handler.get_texture_file_path(
                render_controller_data['texture_file_pk'])
            texture = bpy.data.images.load(
                texture_file_path.as_posix())
        except RuntimeError:
            texture = None
        new_rc_stack_item = RcStackItem(texture)
        geo_rc_stacks[render_controller_data['geometry_pk']].append(
            new_rc_stack_item)
        material_pks = render_controller_data[
            'render_controller_materials_field_pks']
        if import_type == 'attachable':
            get_material_pattern_and_material: Callable[
                [int, int], tuple[str, str]
            ] = db_handler.get_attachable_material_pattern_and_material
        elif import_type == 'entity':
            get_material_pattern_and_material = (
                db_handler.get_entity_material_pattern_and_material)
        else:
            raise ValueError("Expected 'entity' or 'attachable'")
        if len(material_pks) > 0:
            for rc_material_field_pk in material_pks:
                pattern, material_full_name = (
                    get_material_pattern_and_material(
                        pk, rc_material_field_pk)
                )
                new_rc_stack_item.materials[pattern] = material_full_name
        else:
            # Pull materials from the attachable/entity it's a fake render
            # controller
            ce_material_field_pk = render_controller_data[
                'source_entity_material_field_pk']
            material_full_name = db_handler.get_full_material_identifier(
                ce_material_field_pk)
            new_rc_stack_item.materials['*'] = material_full_name

    # 2. Load every geometry
    # blender_materials - Prevents creating same material multiple times
    # it's a dictionary of materials which uses a tuple with pairs of
    # names of the texutes and minecraft materials as the identifiers
    # of the material to create.
    blender_materials: Dict[
        Tuple[Tuple[Optional[str], str], ...], Material] = {}
    warnings: List[str] = []
    for geo_pk, rc_stack in geo_rc_stacks.items():
        geo_path, geo_identifier = db_handler.get_geometry(geo_pk)
        geo_data = load_jsonc(geo_path).data
        if not isinstance(geo_data, dict):
            raise ValueError(f"File {geo_path} is not a valid geometry file")
        # # Import model
        model_loader = ModelLoader(geo_data, geo_identifier)
        warnings.extend(model_loader.warnings)
        geometry = ImportGeometry(model_loader)
        armature = geometry.build_with_armature(context)

        # 2.1. Set proper textures resolution and model bounds
        model_properties = get_mcblend(armature)

        model_properties.texture_width = geometry.texture_width
        model_properties.texture_height = geometry.texture_height
        model_properties.visible_bounds_offset = geometry.visible_bounds_offset
        model_properties.visible_bounds_width = geometry.visible_bounds_width
        model_properties.visible_bounds_height = geometry.visible_bounds_height

        # TODO - is this necessary?
        if geometry.identifier.startswith('geometry.'):
            model_properties.model_name = geometry.identifier[9:]
            armature.name = geometry.identifier[9:]
        else:
            model_properties.model_name = geometry.identifier
            armature.name = geometry.identifier

        # 2.2. Save render controller properties in the armature
        for rc_stack_item in rc_stack:
            armature_rc = get_mcblend(armature).\
                render_controllers.add()
            if rc_stack_item.texture is not None:
                armature_rc.texture = rc_stack_item.texture.name
            else:
                armature_rc.texture = ""
            for pattern, material_name in rc_stack_item.materials.items():
                armature_rc_material = armature_rc.materials.add()
                armature_rc_material.pattern = pattern
                armature_rc_material.material = material_name

        # 2.3. For every bone of geometry, create blender material from.
        # Materials are created from a list of pairs:
        # (Image, minecraft material)
        for bone_name, bone in geometry.bones.items():
            # Create a list of materials applicable for this bone
            bone_materials: List[Tuple[Optional[Image], str]] = []
            bone_materials_id: List[Tuple[Optional[str], str]] = []
            for rc_stack_item in reversed(rc_stack):
                matched_material: Optional[str] = None
                for pattern, material_name in rc_stack_item.materials.items():
                    if star_pattern_match(bone_name, pattern):
                        matched_material = material_name
                # Add material to bone_materials only if something matched
                if matched_material is not None:
                    bone_materials.append(
                        (rc_stack_item.texture, matched_material))
                    if rc_stack_item.texture is None:
                        bone_materials_id.append(
                            (None, matched_material))
                    else:
                        bone_materials_id.append(
                            (rc_stack_item.texture.name, matched_material))
            if len(bone_materials) == 0:  # No material for this bone!
                continue
            try:  # try to use existing material
                material = blender_materials[tuple(bone_materials_id)]
            except: # pylint: disable=bare-except
                # create material
                material = create_bone_material("MC_Material", bone_materials)
                blender_materials[tuple(bone_materials_id)] = material
            for c in bone.cubes:
                if c.blend_cube is None:
                    continue
                if not isinstance(c.blend_cube.data, Mesh):
                    continue
                c.blend_cube.data.materials.append(
                    blender_materials[tuple(bone_materials_id)])
    return warnings

def apply_materials(context: Context):
    '''
    Applies materials from render controller menu into the model.

    :param context: the context of running the operator.
    '''
    blender_materials: Dict[
        Tuple[Tuple[Optional[str], str], ...], Material] = {}
    armature = context.object
    if armature is None or armature.type != 'ARMATURE':
        # TODO - this should never happen. Rewrite the code so it's guaranteed
        raise ValueError("Selected object is not an armature")
    origin: Object | None = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        origin = armature
    mcblend_obj_group = McblendObjectGroup(armature, origin)
    armature_properties = get_mcblend(armature)

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
        bone_materials: List[Tuple[Optional[Image], str]] = []
        bone_materials_id: List[Tuple[Optional[str], str]] = []

        for rc in reversed(armature_properties.render_controllers):
            texture: Optional[Image] = None
            if rc.texture in bpy.data.images:
                texture = bpy.data.images[rc.texture]
            rc_stack_item = RcStackItem(texture)
            for rc_material in rc.materials:
                rc_stack_item.materials[
                    rc_material.pattern] = rc_material.material

            matched_material: Optional[str] = None
            for pattern, material_name in rc_stack_item.materials.items():
                if star_pattern_match(bone.name, pattern):
                    matched_material = material_name
            # Add material to bone_materials only if something matched
            if matched_material is not None:
                bone_materials.append(
                    (rc_stack_item.texture, matched_material))
                if rc_stack_item.texture is None:
                    bone_materials_id.append(
                        (None, matched_material))
                else:
                    bone_materials_id.append(
                        (rc_stack_item.texture.name, matched_material))
        if len(bone_materials) == 0:  # No material for this bone!
            continue
        try:  # try to use existing material
            material = blender_materials[tuple(bone_materials_id)]
        except:  # pylint: disable=bare-except
            # create material
            material = create_bone_material("MC_Material", bone_materials)
            blender_materials[tuple(bone_materials_id)] = material
        for c in bone.cubes:
            c.mcblend_obj.obj_data.materials.clear()
            c.mcblend_obj.obj_data.materials.append(
                blender_materials[tuple(bone_materials_id)])
        for p in bone.poly_mesh.mcblend_objs:
            p.obj_data.materials.clear()
            p.obj_data.materials.append(
                blender_materials[tuple(bone_materials_id)])

@dataclass
class _PhysicsObjectsGroup:
    '''
    Group of objects used for rigid body simulation of single bone of armature.
    '''
    rigid_body: Optional[Object] = None
    rigid_body_constraint: Optional[Object] = None
    object_parent_empty: Optional[Object] = None

def prepare_physics_simulation(context: Context) -> Dict[str, Any]:
    '''
    Creates objects necessary for the rigid body simulation of the Minecraft
    model.

    :param context: the context of running the operator.
    '''
    result = ModelExport.json_outer()
    armature = context.object
    if (
            armature is None
            or armature.type != 'ARMATURE'
            or not isinstance(armature.data, Armature)):
        raise ValueError("Selected object is not an armature")

    origin = None
    use_armature_origin: bool = get_mcblend(
        armature).model_origin == ModelOriginType.ARMATURE.value
    if use_armature_origin:
        origin = armature
    mcblend_obj_group = McblendObjectGroup(armature, origin)

    # If there is no rigid body world add it to the scene
    rigidbody_world = context.scene.rigidbody_world
    if rigidbody_world is None:  # type: ignore
        bpy.ops.rigidbody.world_add()  # pyright: ignore[reportUnknownMemberType]
        rigidbody_world = context.scene.rigidbody_world
    if rigidbody_world.collection is None:  # type: ignore
        collection = bpy.data.collections.new("RigidBodyWorld")
        rigidbody_world.collection = collection
    if rigidbody_world.constraints is None:  # type: ignore
        collection = bpy.data.collections.new("RigidBodyConstraints")
        rigidbody_world.constraints = collection

    # Create new collections for the scene
    physics_objects_groups: Dict[McblendObject, _PhysicsObjectsGroup] = {}
    main_collection = bpy.data.collections.new("Mcblend: Physics")
    rb_collection = bpy.data.collections.new("Rigid Body")
    rbc_collection = bpy.data.collections.new("Rigid Body Constraints")
    bp_collection = bpy.data.collections.new("Bone Parents")
    context.scene.collection.children.link(main_collection)
    main_collection.children.link(rb_collection)
    main_collection.children.link(rbc_collection)
    main_collection.children.link(bp_collection)

    for _, bone in mcblend_obj_group.items():
        if not bone.mctype == MCObjType.BONE:
            continue
        physics_objects_groups[bone] = _PhysicsObjectsGroup()
        # Create children cubes
        cubes_group: List[Object] = []
        for child in bone.children:
            if not child.mctype == MCObjType.CUBE:
                continue
            new_obj = child.thisobj.copy()
            new_obj = cast(Object, new_obj)
            new_obj.data = child.obj_data.copy()
            new_obj.animation_data_clear()
            context.collection.objects.link(new_obj)

            cubes_group.append(new_obj)
        bpy.ops.object.select_all(action='DESELECT')  # pyright: ignore[reportUnknownMemberType]
        rigid_body: Optional[Object] = None
        if len(cubes_group) > 1:
            for c in cubes_group:
                c.select_set(True)
            context.view_layer.objects.active = cubes_group[-1]
            bpy.ops.object.join()  # pyright: ignore[reportUnknownMemberType]
            rigid_body = context.object
        elif len(cubes_group) == 1:
            cubes_group[0].select_set(True)
            rigid_body = cubes_group[0]
        # Move origin to the center of mass and rename the object
        if rigid_body is not None:
            for material_slot in rigid_body.material_slots:
                material_slot.material = None  # type: ignore
            bpy.ops.object.origin_set(  # pyright: ignore[reportUnknownMemberType]
                type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')
            bpy.ops.object.visual_transform_apply()  # pyright: ignore[reportUnknownMemberType]
            matrix_world = rigid_body.matrix_world.copy()
            rigid_body.parent = None
            rigid_body.matrix_world = matrix_world
            rigidbody_world.collection.objects.link(rigid_body)
            # Move to rigid body colleciton
            context.collection.objects.unlink(rigid_body)
            rb_collection.objects.link(rigid_body)
            # Add keyframes to the rigid body "animated"/"kinematic" property (
            # enable it 1 frame after current frame)
            rigid_body.rigid_body.kinematic = True
            rigid_body.rigid_body.keyframe_insert("kinematic", frame=0)
            rigid_body.rigid_body.keyframe_insert(
                "kinematic", frame=bpy.context.scene.frame_current)
            rigid_body.rigid_body.kinematic = False
            rigid_body.rigid_body.keyframe_insert(
                "kinematic", frame=bpy.context.scene.frame_current+1)
            # rb - rigid body
            rigid_body.name = f'{bone.obj_name}_rb'
            physics_objects_groups[bone].rigid_body = rigid_body


            # Add bone parent empty
            empty = bpy.data.objects.new(
                f'{bone.obj_name}_bp', None)  # bp - bone parent
            bp_collection.objects.link(empty)
            empty.empty_display_type = 'CONE'
            empty.empty_display_size = 0.1
            empty.matrix_world = bone.obj_matrix_world
            physics_objects_groups[bone].object_parent_empty = empty
            # Add "Copy Transforms" constraint to the bone
            context.view_layer.objects.active = armature

            # Pose mode
            bpy.ops.object.posemode_toggle()  # pyright: ignore[reportUnknownMemberType]
            bpy.ops.pose.select_all(action='DESELECT')  # pyright: ignore[reportUnknownMemberType]

            armature.data.bones.active = armature.data.bones[
                bone.thisobj_id.bone_name]
            # bpy.ops.pose.constraint_add(type='COPY_TRANSFORMS')
            constraint = bone.this_pose_bone.constraints.new(
                type='COPY_TRANSFORMS')
            constraint.target = empty
            # Add keyframes to the "copy transformation" constraint (
            # enable it 1 frame after current frame)
            constraint.influence = 0
            constraint.keyframe_insert("influence", frame=0)
            constraint.keyframe_insert(
                "influence", frame=bpy.context.scene.frame_current)
            constraint.influence = 1
            constraint.keyframe_insert(
                "influence", frame=bpy.context.scene.frame_current+1)

            # Object mode
            bpy.ops.object.posemode_toggle()  # pyright: ignore[reportUnknownMemberType]

            # Add "Child of" constraint to parent empty
            context.view_layer.objects.active = empty
            empty.constraints.new(type='CHILD_OF').target = rigid_body

        empty = bpy.data.objects.new(
            f'{bone.obj_name}_rbc', None)  # bp - bone parent
        rbc_collection.objects.link(empty)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.empty_display_size = 0.1
        empty.matrix_world = bone.obj_matrix_world
        physics_objects_groups[bone].rigid_body_constraint = empty

    # Add constraints to rigid body constraints empty
    for bone, pog in physics_objects_groups.items():
        rbc = pog.rigid_body_constraint
        if rbc is None:
            continue
        if bone.parent is None or bone.parent.mctype != MCObjType.BONE:
            continue
        if bone.parent not in physics_objects_groups:
            continue
        parent_rb = physics_objects_groups[bone.parent].rigid_body
        if parent_rb is None:
            continue
        context.scene.rigidbody_world.constraints.objects.link(  # type: ignore
            rbc)
        rbc.rigid_body_constraint.object1 = pog.rigid_body  # type: ignore
        rbc.rigid_body_constraint.object2 = parent_rb

    return result

def merge_models(context: Context) -> None:
    '''
    Merges models of all of the selected armatures and creates a common
    render controller and texture for them.
    '''

    # GET OBJECTS TO MERGE
    uv_mergers: list[UvModelMerger] = []
    armatures: list[Object] = []
    for obj in context.selected_objects:
        # Deselect every object (for later)
        obj.select_set(False)
        # Exclude unwanted objects
        if obj.type != 'ARMATURE':
            continue
        obj_mcblend = get_mcblend(obj)
        if len(obj_mcblend.render_controllers) == 0:
            continue
        base_image = bpy.data.images[obj_mcblend.render_controllers[0].texture]

        # Create a merger object
        use_armature_origin: bool = (
            obj_mcblend.model_origin == ModelOriginType.ARMATURE.value)
        entity = McblendObjectGroup(obj, obj if use_armature_origin else None)
        merger = UvModelMerger(entity, base_image)

        # Append the merger object
        uv_mergers.append(merger)
        armatures.append(obj)

    # PLAN UVS - rearrange the UVs of the objectss
    mapper = UvMapper(0, 0)
    mapper.uv_boxes.extend(uv_mergers)
    mapper.plan_uv(True)

    # CREATE A NEW TEXTURE
    image = bpy.data.images.new(
        "merged", mapper.width, mapper.height, alpha=True)

    # This array represents new texture
    # DIM0:up axis DIM1:right axis DIM2:rgba axis
    arr = np.zeros([image.size[1], image.size[0], 4])
    for merger in uv_mergers:
        pixels = np.array(merger.base_image.pixels[:])

        pixels = pixels.reshape([
            merger.base_image_size[1], merger.base_image_size[0], 4
        ])
        # Paste the image into the texture
        min_x = merger.uv[0]
        max_x = min_x+merger.base_image_size[0]
        # Y is flipped on the array
        min_y = mapper.height-merger.uv[1]-merger.base_image_size[1]
        max_y = mapper.height-merger.uv[1]
        arr[min_y:max_y, min_x:max_x] = pixels
    image.pixels = arr.ravel()  # Apply texture pixels values

    # APPLY THE UVs
    converter = CoordinatesConverter(
        np.array([[0, mapper.width], [0, mapper.height]]),
        np.array([[0, 1], [1, 0]])
    )
    for i, merger in enumerate(uv_mergers):
        merger.set_blender_uv(converter)

    # MERGE THE ARMATURES
    context.view_layer.objects.active = armatures[0]
    for i, obj in enumerate(armatures):
        # This assertion should never raise an exception
        assert isinstance(obj.data, Armature), "Object is not an Armature"
        # Update bone names
        for bone in obj.data.bones:
            bone.name = f'{bone.name}_{i}'
        # Select the object for merging
        obj.select_set(True)
    bpy.ops.object.join()  # pyright: ignore[reportUnknownMemberType]
    # CREATE A NEW RENDER CONTROLLER FOR THE MODEL
    active_obj = context.view_layer.objects.active
    rcs = get_mcblend(active_obj).render_controllers
    rcs.clear()
    rc = rcs.add()
    rc.texture = image.name
    material = rc.materials.add()
    material.pattern = '*'
    material.material = 'entity_alphatest'
    # APPLY THE RENDER CONTROLLER
    apply_materials(context)
