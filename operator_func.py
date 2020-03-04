import bpy
import mathutils
import math
import numpy as np
from enum import Enum

from collections import defaultdict

# Additional imports for mypy
import bpy_types
import typing as tp


MINECRAFT_SCALE_FACTOR = 16

# Data structures/enums
class MCObjType(Enum):
    CUBE = 'CUBE'
    BONE = 'BONE'
    BOTH = 'BOTH'


class ObjectMcProperties(tp.NamedTuple):
    '''Temporary minecraft-related properties of an object (mesh or empty).'''
    mcchildren: tp.Tuple[str]
    mctype: MCObjType


class ObjectMcTransformations(tp.NamedTuple):
    '''
    Temporary properties of transformations of an object (mesh or empty)
    for the minecraft animation. Changes of these values over the frames of the
    animation are used to calculate the values for minecraft animation json.
    '''
    location: np.array
    scale: np.array
    rotation: np.array


# MAIN
def export_model(context: bpy_types.Context, model_name: str):
    object_properties = get_object_mcproperties(context)

    mc_bones: tp.List[tp.Dict] = []

    for obj in context.selected_objects:
        if (
            obj.name in object_properties and
            object_properties[obj.name].mctype in
            [MCObjType.BONE, MCObjType.BOTH]
        ):
            # Create cubes list
            if object_properties[obj.name].mctype == MCObjType.BOTH:
                cubes = [obj]
            elif object_properties[obj.name].mctype == MCObjType.BONE:
                cubes = []
            # Add children cubes if they are MCObjType.CUBE type
            for child_name in (
                object_properties[obj.name].mcchildren
            ):
                if (
                    child_name in object_properties and
                    object_properties[child_name].mctype ==
                    MCObjType.CUBE
                ):
                    cubes.append(bpy.data.objects[child_name])

            mcbone = get_mcbone_json(obj, cubes)
            mc_bones.append(mcbone)

    result = get_mcmodel_json(model_name, mc_bones)
    return result

def export_animation(context: bpy_types.Context):
    object_properties = get_object_mcproperties(context)

    start_frame = context.scene.frame_current
    
    bone_data: tp.Dict[str, tp.Dict[str, tp.List[tp.Dict]]] = (  # TODO - Create object for that for safer/cleaner code - https://www.python.org/dev/peps/pep-0589/
        defaultdict(lambda: {
            'scale': [], 'rotation': [], 'position': []
        })
    )

    # Stop animation if running & jump to the first frame
    bpy.ops.screen.animation_cancel()
    context.scene.frame_set(0)
    default_translation = get_transformations(context, object_properties)
    prev_rotation = {
        name:np.zeros(3) for name in default_translation.keys()
    }

    next_keyframe = get_next_keyframe(context)

    while next_keyframe is not None:
        context.scene.frame_set(math.ceil(next_keyframe))
        current_translations = get_transformations(context, object_properties)
        for d_key, d_val in default_translation.items():
            # Get the difference from original
            loc, rot, scale = get_mctranslations(
                d_val.rotation, current_translations[d_key].rotation,
                d_val.scale, current_translations[d_key].scale,
                d_val.location, current_translations[d_key].location
            )
            time = str(round(
                (context.scene.frame_current-1) /
                context.scene.render.fps, 4
            ))
            
            bone_data[d_key]['position'].append({
                'time': time,
                'value': get_vect_json(loc)
            })
            rot = pick_closest_rotation(
                rot, prev_rotation[d_key]
            )
            bone_data[d_key]['rotation'].append({
                'time': time,
                'value': get_vect_json(rot)
            })
            bone_data[d_key]['scale'].append({
                'time': time,
                'value': get_vect_json(scale)
            })

            prev_rotation[d_key] = rot  # Save previous rotation

        next_keyframe = get_next_keyframe(context)

    context.scene.frame_set(start_frame)
    animation_dict = get_mcanimation_json(
        context,
        name=context.scene.bedrock_exporter.animation_name,
        length=context.scene.frame_end,
        loop_animation=context.scene.bedrock_exporter.loop_animation,
        anim_time_update=context.scene.bedrock_exporter.anim_time_update,
        bone_data=bone_data
    )

    return animation_dict

# COMMON
def get_local_matrix(
    parent_world_matrix: mathutils.Matrix, child_world_matrix: mathutils.Matrix
) -> mathutils.Matrix:
    '''
    Returns translation matrix of child in relation to parent.
    In space defined by parent translation matrix.
    '''
    return (
        parent_world_matrix.inverted() @ child_world_matrix
    )


def get_vect_json(arr: tp.Iterable) -> tp.List[float]:
    '''
    Changes the iterable whith numbers into basic python list of floats.
    Values from the original iterable are rounded to the 4th deimal
    digit.
    '''
    return [round(i, 3) for i in arr]


def get_mcrotation(
    child_matrix: mathutils.Matrix,
    parent_matrix: tp.Optional[mathutils.Matrix]=None
) -> np.ndarray:
    '''Returns the rotation of mcbone represented by the "obj" object.'''
    def local_rotation(
        child_matrix: mathutils.Matrix, parent_matrix: mathutils.Matrix
    ) -> mathutils.Euler:
        '''
        Reuturns Euler rotation of a child matrix in relation to parent matrix
        '''
        child_matrix = child_matrix.normalized()
        parent_matrix = parent_matrix.normalized()
        return (
            parent_matrix.inverted() @ child_matrix
        ).to_quaternion().to_euler('XZY')

    if parent_matrix is not None:
        result = local_rotation(
            child_matrix, parent_matrix
        )
    else:
        result = child_matrix.to_euler('XZY')
    result = np.array(result)[[0, 2, 1]]
    result = result * np.array([1, -1, 1])
    result = result * 180/math.pi  # math.degrees() for array
    return result


# MODELS
def get_mcube_size(
    obj: bpy_types.Object, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube size based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return (np.array(obj.bound_box[6]) - np.array(obj.bound_box[0]))[[0, 2, 1]]


def get_mccube_position(
    obj: bpy_types.Object, translation: mathutils.Matrix
) -> np.ndarray:
    '''
    Returns cube position based on the bounding box of an object.
    The returned value is moved by the translation matrix from "translation"
    '''
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(obj.bound_box[0])[[0, 2, 1]]


def get_mcpivot(obj: bpy_types.Object) -> np.ndarray:
    '''
    Returns the pivot point. Of a mcbone (or mccube represented by the "obj"
    object.
    '''
    def local_crds(
        parent_matrix: mathutils.Matrix, child_matrix: mathutils.Matrix
    ) -> mathutils.Vector:
        '''Local coordinates of child matrix inside parent matrix'''
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _get_mcpivot(obj: bpy_types.Object) -> mathutils.Vector:
        if 'mc_parent' in obj:
            result = local_crds(
                obj['mc_parent'].matrix_world,
                obj.matrix_world
            )
            result += _get_mcpivot(obj['mc_parent'])
        else:
            result = obj.matrix_world.to_translation()
        return result

    return np.array(_get_mcpivot(obj).xzy)


def get_mcbone_json(
    bone: bpy_types.Object, cubes: tp.List[bpy_types.Object]
) -> tp.Dict:
    '''
    - bone - the main object that represents the bone.
    - cubes - the list of objects that represent the cubes that belong to
      the bone. If the "bone" is one of the cubes it should be included on the
      list.

    Returns the dictionary that represents a single mcbone in json file
    of exported model.
    '''
    def _scale(obj: bpy_types.Object) -> np.ndarray:
        '''Scale of a bone'''
        _, _, scale = obj.matrix_world.decompose()
        return np.array(scale.xzy)

    mcbone = {'name': bone.name, 'cubes': []}

    # Code
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name
        b_rot = get_mcrotation(bone.matrix_world, bone['mc_parent'].matrix_world)
    else:
        b_rot = get_mcrotation(bone.matrix_world)

    b_pivot = get_mcpivot(bone) * MINECRAFT_SCALE_FACTOR

    for cube in cubes:
        translation = get_local_matrix(
            bone.matrix_world, cube.matrix_world
        )

        _b_scale = _scale(cube)

        c_size = (
            get_mcube_size(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_pivot = get_mcpivot(cube) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            get_mccube_position(cube, translation) * _b_scale *
            MINECRAFT_SCALE_FACTOR
        )
        c_rot = get_mcrotation(cube.matrix_world, bone.matrix_world)

        mcbone['cubes'].append({
            'uv': [0, 0],
            'size': get_vect_json(c_size),
            'origin': get_vect_json(c_origin),
            'pivot': get_vect_json(c_pivot),
            'rotation': get_vect_json(c_rot)
        })

    mcbone['pivot'] = get_vect_json(b_pivot)
    mcbone['rotation'] = get_vect_json(b_rot)
    return mcbone


def get_mcmodel_json(model_name: str, mc_bones: tp.List[tp.Dict]) -> tp.Dict:
    '''
    Returns the dictionary that represents JSON file for exporting the model
    '''
    return {
        "format_version": "1.12.0",
        "minecraft:geometry": [
            {
                "description": {
                    "identifier": f"geometry.{model_name}",
                    "texture_width": 1,
                    "texture_height": 1,
                    "visible_bounds_width": 10,
                    "visible_bounds_height": 10,
                    "visible_bounds_offset": [0, 2, 0]
                },
                "bones": mc_bones
            }
        ]
    }


# TODO - update __doc__ string
def get_object_mcproperties(
    context: bpy_types.Context
) -> tp.Dict[str, ObjectMcProperties]:
    '''
    Loops through context.selected_objects and returns a dictionary with
    some properties of selected objects:
     - "mc_obj_type" with value "MCObjType.CUBE" or "MCObjType.BONE" or "MCObjType.BOTH".
     - "mc_children" properties for easy access to reverse relation
       of "mc_parent".

    The properties are returned as dictionary.
    '''
    tmp_properties: tp.DefaultDict = defaultdict(
        lambda: {"mc_children": [], "mc_obj_type": ""}
    )

    # Objects other than EMPTY and MESH are ignored.
    for obj in context.selected_objects:
        if obj.type == 'EMPTY' or obj.type == 'MESH':
            if "mc_parent" in obj:
                tmp_properties[
                    obj["mc_parent"].name
                ]["mc_children"].append(obj)

    properties: tp.Dict[str, ObjectMcProperties] = {}
    for obj in context.selected_objects:
        tmp_prop = tmp_properties[obj.name]
        if obj.type == 'EMPTY':
            tmp_prop['mc_obj_type'] = MCObjType.BONE
        elif obj.type == 'MESH':
            if len(tmp_properties[obj.name]["mc_children"]) > 0:
                tmp_prop['mc_obj_type'] = MCObjType.BOTH
            elif "mc_is_bone" in obj and obj["mc_is_bone"] == 1:
                tmp_prop["mc_obj_type"] = MCObjType.BOTH
            elif "mc_parent" in obj:
                tmp_prop["mc_obj_type"] = MCObjType.CUBE
            else:  # Not connected to anything
                tmp_prop["mc_obj_type"] = MCObjType.BOTH

        properties[obj.name] = ObjectMcProperties(
            mcchildren = tuple(i.name for i in tmp_prop['mc_children']),  # type: ignore
            mctype = tmp_prop['mc_obj_type']
        )

    return properties


# ANIMATIONS
def get_transformations(
    context: bpy_types.Context,
    object_properties: tp.Dict[str, ObjectMcProperties]
) -> tp.Dict[str, ObjectMcTransformations]:
    '''
    Loops over context.selected_objects and returns the dictionary with
    information about transformations of every bone. `object_properties` is
    a dictionary that represents temporary properties of the object used for
    exporting like classification of the object as a MCObjType.BONE,
    MCObjType.CUBE or MCObjType.BOTH.

    Result is a dictionary with name of the bone as a key and whith another
    dictionary that contains the information about "rotation", "scale" and
    "location" of the bone. The scale is an np.ndarray Euler rotation in
    degrees.
    '''
    transformations:tp.Dict[str, ObjectMcTransformations] = {}
    for obj in context.selected_objects:
        if (
            obj.name in object_properties and
            object_properties[obj.name].mctype in
            [MCObjType.BONE, MCObjType.BOTH]
        ):
            if 'mc_parent' in obj:
                parent = obj['mc_parent']
                # Scale
                scale = (
                    np.array(obj.matrix_world.to_scale()) /
                    np.array(parent.matrix_world.to_scale())
                )[[0, 2, 1]]
                # Locatin
                local_matrix = get_local_matrix(
                    parent.matrix_world.normalized(),
                    obj.matrix_world.normalized()
                )
                location = np.array(local_matrix.to_translation())
                location = location[[0, 2, 1]] * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = get_mcrotation(obj.matrix_world, parent.matrix_world)
            else:
                # Scale
                scale = np.array(obj.matrix_world.to_scale())[[0, 2, 1]]
                # Location
                location = np.array(
                    obj.matrix_world.normalized().to_translation()
                )
                location = location[[0, 2, 1]] * scale * MINECRAFT_SCALE_FACTOR
                # Rotation
                rotation = get_mcrotation(obj.matrix_world)
            transformations[obj.name] = ObjectMcTransformations(
                location=location, scale=scale, rotation=rotation
            )
    return transformations


def get_next_keyframe(context: bpy_types.Context) -> tp.Optional[int]:
    '''
    Returns the index of next keyframe from selected objects.
    Returns None if there is no more keyframes to chose.
    '''
    curr = context.scene.frame_current
    next_keyframe = None
    for obj in context.selected_objects:
        if (
            obj.animation_data is not None and
            obj.animation_data.action is not None and
            obj.animation_data.action.fcurves is not None
        ):
            for fcurve in obj.animation_data.action.fcurves:
                if fcurve.keyframe_points is not None:
                    for kframe_point in fcurve.keyframe_points:
                        time = kframe_point.co[0]
                        if time > curr:
                            if next_keyframe is None:
                                next_keyframe = time
                            else:
                                next_keyframe = min(time, next_keyframe)
    return next_keyframe


def get_mctranslations(
    parent_rot: np.ndarray, child_rot: np.ndarray,
    parent_scale: np.ndarray, child_scale: np.ndarray,
    parent_loc: np.ndarray, child_loc: np.ndarray
) -> tp.Tuple[np.ndarray, np.ndarray, np.ndarray]:
    '''
    Compares original rotation, scale and translation with new rotation, scale
    and translation of an object to return location, rotation and scale values
    (in this order) that can be used by the dictionary used for exporting the
    animation data to minecraft format.
    '''
    child_scale = child_scale
    parent_scale = parent_scale
    scale = child_scale / parent_scale
    scale = scale

    loc = child_loc - parent_loc
    loc = loc / parent_scale

    rot = child_rot - parent_rot

    return loc, rot, scale


def get_mcanimation_json(
    context: bpy_types.Context,
    name: str, length: int, loop_animation: bool, anim_time_update: str,
    bone_data: tp.Dict[str, tp.Dict[str, tp.List[tp.Dict]]]
):
    '''
    - name - name of the animation
    - length - the length of animation (in frames). The FPS vlaue is extracted
      from context.scene.render.fps.
    - loop_animation - Loops the animation
    - anim_time_update - Adds anim_time_update property to the animation.
    - bone_data - Dictionary filled with dictionaries that describe postition,
      rotation and scale for each frame (uses bone name as a key).

    Returns the tamplate of a dictionary that represents the JSON file with
    minecraft animation.
    '''
    def reduce_property(
        context: bpy_types.Context,
        ls: tp.List[tp.Dict]
    ) -> tp.List[tp.Dict]:
        '''
        Removes some of the keyframes from list of keyframes values of
        a property (rotation, location or scale)
        '''
        if len(ls) == 0:
            return []
        last_val = ls[0]['value']
        reduced_property = [ls[0]]
        for i in range(1, len(ls)-1):
            curr_val = ls[i]['value']
            next_val = ls[i+1]['value']
            if curr_val != last_val or curr_val != next_val:
                reduced_property.append(ls[i])
                last_val = curr_val
        # Add last element unless there is only one (in which case it's
        # already added)
        if len(ls) > 1:
            reduced_property.append(ls[-1])
        return reduced_property

    # Extract bones data
    bones: tp.Dict = {}
    for bone_name, bone in bone_data.items():
        bones[bone_name] = {
            'position': {},
            'rotation': {},
            'scale': {}
        }
        for prop in reduce_property(context, bone['position']):
            bones[bone_name]['position'][prop['time']] = prop['value']
        for prop in reduce_property(context, bone['rotation']):
            bones[bone_name]['rotation'][prop['time']] = prop['value']
        for prop in reduce_property(context, bone['scale']):
            bones[bone_name]['scale'][prop['time']] = prop['value']
    # Returning result
    result: tp.Dict = {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{name}": {
                "animation_length": (length-1)/context.scene.render.fps,
                "bones": bones
            }
        }
    }
    data = result["animations"][f"animation.{name}"]
    if loop_animation:
        data['loop'] = True
    if anim_time_update != "":
        data['anim_time_update'] = anim_time_update
    return result


def pick_closest_rotation(
    modify: np.ndarray, close_to: np.ndarray
) -> np.ndarray:
    '''
    Takes two numpy.arrays that represent rotation in
    euler rotation mode (using degrees). Modifies the
    values of 'modify' vector to get different representations
    of the same rotation. Picks the vector which is the
    closest to 'close_to' vector (euclidean distance).
    '''
    def _pick_closet_location(
        modify: np.ndarray, close_to: np.ndarray
    ) -> tp.Tuple[float, np.ndarray]:
        choice = modify
        distance = np.linalg.norm(choice - close_to)

        for i in range(3):  # Adds removes 360 to all 3 axis (picks the best)
            arr = np.zeros(3)
            arr[i] = 360
            while choice[i] < close_to[i]:
                new_choice = choice + arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                else:
                    distance, choice = new_distance, new_choice
            while choice[i] > close_to[i]:
                new_choice = choice - arr
                new_distance = np.linalg.norm(new_choice - close_to)
                if new_distance > distance:
                    break
                else:
                    distance, choice = new_distance, new_choice
        return distance, choice

    distance1, choice1 = _pick_closet_location(modify, close_to)
    distance2, choice2 = _pick_closet_location(  # Counterintuitive but works
        (modify + np.array([180, 180, 180])) * np.array([1, -1, 1]),
        close_to
    )
    if distance2 < distance1:
        return choice2
    else:
        return choice1


# TODO - porper naming of the functions below
def get_uv_face(
    obj: bpy_types.Object, face_name: str
) -> tp.Dict[str, int]:
    '''
    - obj - the mesh object with cube
    - face_name - decides which face should be returned

    Returns a dictionary with list of integer indices of loops which are part
    of a UV of a cube.
    '''
    bound_box_faces = {
        'front': [0, 4, 5, 1], 'back': [7, 3, 2, 6], 'left': [4, 7, 6, 5],
        'right': [3, 0, 1, 2], 'top': [1, 5, 6, 2], 'bottom': [4, 0, 3, 7]
    }
    # list with bound box vertex indices in order LD, RD, RU, LU
    f = bound_box_faces[face_name]
    bb = obj.bound_box
    bb_verts = {
        'LD': np.array(bb[f[0]]), 'RD': np.array(bb[f[1]]),
        'RU': np.array(bb[f[2]]), 'LU': np.array(bb[f[3]]),
    }
    for face in obj.data.polygons:
        confirmed_vertices = {'LD': None, 'RD': None, 'RU': None, 'LU': None}
        for vertex_id, loop_id in zip(face.vertices, face.loop_indices):
            vertex = np.array(obj.data.vertices[vertex_id].co)
            for bbv_key , bbv_value in bb_verts.items():
                if np.allclose(vertex, bbv_value):
                    confirmed_vertices[bbv_key] = loop_id
        if all([i is not None for i in confirmed_vertices.values()]):
            return tp.cast(tp.Dict[str, int], confirmed_vertices)
    raise ValueError("Object is not a cube!")


def set_uv(
    obj: bpy_types.Object, uv_face: tp.Dict[str, int],
    crds: tp.Tuple[float, float], size: tp.Tuple[float, float]
):
    '''
    - obj - the mesh object with cube

    - uv_face - the dictionary with loop indices used to define which loops
      of the uv should be moved.
    - crds - value from 0 to 1 the position of the bottom left loop on blender
      uv mapping coordinates system.
    - size - value from 0 to 1 the size of the rectangle in blender uv mapping
      coordinates system.
    '''
    uv_data = obj.data.uv_layers.active.data
    
    uv_data[uv_face['LD']].uv = crds
    uv_data[uv_face['RD']].uv = (crds[0] + size[0], crds[1])
    uv_data[uv_face['RU']].uv = (crds[0] + size[0], crds[1] + size[1])
    uv_data[uv_face['LU']].uv = (crds[0], crds[1] + size[1])


def set_cube_uv(
    obj: bpy_types.Object, crds: tp.Tuple[float, float], width: float,
    depth: float, height: float
):
    '''
    - obj - the mesh object with cube
    - crds - value from 0 to 1 the position of the bottom left loop on blender
      uv mapping coordinates system.
    - width - value from 0 to 1 the width of the cube converted into blender
      uv mapping coordinates system.
    - depth - value from 0 to 1 the depth of the cube converted into blender
      uv mapping coordinates system.
    - height - value from 0 to 1 the height of the cube converted into blender
      uv mapping coordinates system.

    Sets the UV faces of a mesh object that represents a mccube in the same
    patter as minecraft UV mapping.
    '''
    
    set_uv(
        obj, get_uv_face(obj, 'right'), crds, (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'front'),
        (crds[0] + depth, crds[1]), (width, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'left'),
        (crds[0] + depth + width, crds[1]), (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'back'),
        (crds[0] + 2*depth + width, crds[1]), (width, height)
    )
    
    set_uv(
        obj, get_uv_face(obj, 'top'),
        (crds[0] + depth, crds[1] + height), (width, depth)
    )
    set_uv(
        obj, get_uv_face(obj, 'bottom'),
        (crds[0] + depth + width, crds[1] + height), (width, depth)
    )
