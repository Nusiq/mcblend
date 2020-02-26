import bpy
import math
import mathutils
import json
import numpy as np

from bpy.props import StringProperty
from bpy_extras import object_utils

MINECRAFT_SCALE_FACTOR = 16

# Names for temporary types of objects for the exporter
CUBE, BONE, BOTH = 'CUBE', 'BONE', "BOTH"


def cube_size(obj, translation):
    # 0. ---; 1. --+; 2. -++; 3. -+-; 4. +--; 5. +-+; 6. +++; 7. ++-
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return (np.array(obj.bound_box[6]) - np.array(obj.bound_box[0]))[[0, 2, 1]]


def cube_position(obj, translation):
    bound_box = obj.bound_box
    bound_box = [translation @ mathutils.Vector(i) for i in bound_box]
    return np.array(obj.bound_box[0])[[0, 2, 1]]


def get_local_matrix(parent_world_matrix, child_world_matrix):
    '''
    Returns translation matrix of child in relation to parent.
    In space defined by parent translation matrix.
    '''
    return (
        parent_world_matrix.inverted() @ child_world_matrix
    )


def pivot(obj):
    def local_crds(parent_matrix, child_matrix):
        parent_matrix = parent_matrix.normalized()  # eliminate scale
        child_matrix = child_matrix.normalized()  # eliminate scale
        return get_local_matrix(parent_matrix, child_matrix).to_translation()

    def _pivot(obj):
        if 'mc_parent' in obj:
            result = local_crds(
                obj['mc_parent'].matrix_world,
                obj.matrix_world
            )
            result += _pivot(obj['mc_parent'])
        else:
            result = obj.matrix_world.to_translation()
        return result

    return np.array(_pivot(obj).xzy)


def rotation(child_matrix, parent_matrix=None):
    def local_rotation(child_matrix, parent_matrix):
        parent_rot = parent_matrix.to_quaternion()
        child_rot = child_matrix.to_quaternion()

        return parent_rot.rotation_difference(child_rot).to_euler('XZY')

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


def json_vect(arr):
    return [round(i, 4) for i in arr]


def to_mc_bone(
    bone, cubes=None
):
    # mcbone - parent, pivot, rotation
    # mccube - origin, size, inflate, pivot, rotation, uv

    # For the first version I want to use only:
    # origin, size, rotation
    # for mccube

    # Helper functions
    def _scale(obj):
        '''Scale of a bone'''
        _, _, scale = obj.matrix_world.decompose()
        return np.array(scale.xzy)

    mcbone = {'name': bone.name, 'cubes': []}

    # Code
    if 'mc_parent' in bone:
        mcbone['parent'] = bone['mc_parent'].name
        b_rot = rotation(bone.matrix_world, bone['mc_parent'].matrix_world)  # NO TRANSLATION
    else:
        b_rot = rotation(bone.matrix_world)  # NO TRANSLATION

    b_pivot = pivot(bone) * MINECRAFT_SCALE_FACTOR  # NO TRANSLATION

    for cube in cubes:
        translation = get_local_matrix(
            bone.matrix_world, cube.matrix_world
        )

        _b_scale = _scale(cube)  # @ NO TRANSLATION

        c_size = cube_size(cube, translation) * _b_scale * MINECRAFT_SCALE_FACTOR # @ TRANSLATION
        c_pivot = pivot(cube) * MINECRAFT_SCALE_FACTOR
        c_origin = c_pivot + (
            cube_position(cube, translation) * _b_scale * MINECRAFT_SCALE_FACTOR  # @ TRANSLATION
        )
        c_rot = rotation(cube.matrix_world, bone.matrix_world)

        mcbone['cubes'].append({
            'uv': [0, 0],
            'size': json_vect(c_size),
            'origin': json_vect(c_origin),
            'pivot': json_vect(c_pivot),
            'rotation': json_vect(c_rot)
        })

    mcbone['pivot'] = json_vect(b_pivot)
    mcbone['rotation'] = json_vect(b_rot)
    return mcbone


def get_model_template(model_name, mc_bones):
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


def set_mc_obj_types():
    '''
    Loops through bpy.context.selected_objects and assigns custom poperty
    "mc_obj_type_tmp" with value "CUBE" or "BONE" or "BOTH".

    Also adds "mc_children_tmp" properties for easy access to reverse relation
    of "mc_parent".
    '''
    clear_mc_obj_tmp_properties()
    for obj in bpy.context.selected_objects:
        if "mc_parent" in obj:
            if "mc_children_tmp" in obj["mc_parent"]:
                # obj["mc_parent"]["mc_children_tmp"].append(obj)
                # Custom properties seam to be unmutable
                # TODO - create custom dictionary to store
                # object relations
                children = obj["mc_parent"]["mc_children_tmp"].copy()
                children.append(obj)
                obj["mc_parent"]["mc_children_tmp"] = children
            else:
                obj["mc_parent"]["mc_children_tmp"] = [obj]

    for obj in bpy.context.selected_objects:
        if obj.type == 'EMPTY':
            obj['mc_obj_type_tmp'] = BONE
        elif obj.type == 'MESH':
            if "mc_children_tmp" in obj:
                obj['mc_obj_type_tmp'] = BOTH
            elif "mc_is_bone" in obj and obj["mc_is_bone"] is True:
                obj["mc_obj_type_tmp"] = BOTH
            elif "mc_parent" in obj:
                obj["mc_obj_type_tmp"] = CUBE
            else:  # Not connected to anything
                obj["mc_obj_type_tmp"] = BOTH
    # Objects other than EMPTY and MESH are ignored.


def clear_mc_obj_tmp_properties():
    '''
    Removes temportary custom properties from selected objects
    assigned during export process.
    '''
    for obj in bpy.context.selected_objects:
        if "mc_obj_type_tmp" in obj:
            del obj["mc_obj_type_tmp"]
        if "mc_children_tmp" in obj:
            obj["mc_children_tmp"].clear()
            del obj["mc_children_tmp"]


class OBJECT_OT_ExportOperator(bpy.types.Operator):
    bl_idname = "object.export_operator"
    bl_label = "Export Bedrock model."
    bl_description = "Exports selected objects from scene to bedrock model."

    def execute(self, context):
        set_mc_obj_types()

        mc_bones = []
        output = context.scene.bedrock_exporter.path
        model_name = context.scene.bedrock_exporter.model_name

        for obj in bpy.context.selected_objects:
            if (
                'mc_obj_type_tmp' in obj and
                obj['mc_obj_type_tmp'] in [BONE, BOTH]
            ):
                # Create cubes list
                if obj['mc_obj_type_tmp'] == BOTH:
                    cubes = [obj]
                elif obj['mc_obj_type_tmp'] == BONE:
                    cubes = []
                if 'mc_children_tmp' in obj:
                    for child in obj['mc_children_tmp']:
                        if (
                            'mc_obj_type_tmp' in child and
                            child['mc_obj_type_tmp'] == CUBE
                        ):
                            cubes.append(child)

                mcbone = to_mc_bone(obj, cubes)
                mc_bones.append(mcbone)

        result = get_model_template(model_name, mc_bones)

        clear_mc_obj_tmp_properties()

        with open(output, 'w') as f:
            json.dump(result, f, indent=4)

        return {'FINISHED'}


def get_transformations():
    '''
    For each mcbone returns matrix that represents the transformation of
    it in relation to its parent. If there is no paren than returns
    matrix_world.

    Result is a dictionary with name of the bone as a key and the matrix
    as the value.
    '''
    transformations = {}
    for obj in bpy.context.selected_objects:
        if (
            'mc_obj_type_tmp' in obj and
            obj['mc_obj_type_tmp'] in [BONE, BOTH]
        ):
            if 'mc_parent' in obj:
                # Calculate translation in parent axis
                location = get_local_matrix(
                    obj['mc_parent'].matrix_world.normalized(),
                    obj.matrix_world.normalized()
                ).to_translation()
                # Add result
                transformations[obj.name] = {
                    'matrix': get_local_matrix(
                        obj['mc_parent'].matrix_world, obj.matrix_world
                    ),
                    'scale': (
                        np.array(obj.matrix_world.to_scale()) /
                        np.array(obj['mc_parent'].matrix_world.to_scale())
                    ),
                    'location': location
                }
            else:
                transformations[obj.name] = {
                    'matrix': obj.matrix_world.copy(),
                    'scale': np.array(obj.matrix_world.to_scale()),
                    'location': np.array(obj.matrix_world.to_translation())
                }
    return transformations


def get_next_keyframe():
    '''
    Returns the index of next keyframe from selected objects.
    Returns None if there is no more keyframes to chose.
    '''
    curr = bpy.context.scene.frame_current
    next_keyframe = None
    for obj in bpy.context.selected_objects:
        for fcurve in obj.animation_data.action.fcurves:
            for kframe_point in fcurve.keyframe_points:
                time = kframe_point.co[0]
                if time > curr:
                    if next_keyframe is None:
                        next_keyframe = time
                    else:
                        next_keyframe = min(time, next_keyframe)
    return next_keyframe


def is_translated(matrix_a, matrix_b):
    '''
    Takes two translation matrices and compares location, rotation
    and scale to test if they are different (with certain error margin)

    Returns 3 boolean values - loc_changed, rot_changed, scale_changed
    '''
    prev_loc, prev_rot, prev_scale = get_local_matrix(
        matrix_a,
        matrix_b
    ).decompose()
    prev_rot = prev_rot.to_euler()
    prev_rot = np.array([math.degrees(i) for i in prev_rot])

    loc_changed, rot_changed, scale_changed = (
        not np.allclose(prev_loc, [0, 0, 0], atol=0.0001),
        not np.allclose(prev_rot, [0, 0, 0], atol=0.0001),
        not np.allclose(prev_scale, [1, 1, 1], atol=0.0001)
    )
    return loc_changed, rot_changed, scale_changed


def to_mc_translation_vectors(
    parent, child,
    parent_scale, child_scale,
    parent_loc, child_loc
):
    '''
    Takes translation matrix and returns 3 numpy arrays for location, rotation
    and scale in minecraft friendly format.
    '''
    child_scale = child_scale[[0, 2, 1]]
    parent_scale = parent_scale[[0, 2, 1]]
    scale = child_scale / parent_scale
    scale = scale
    # parent = parent.normalized()
    # child = child.normalized()


    loc = child_loc - parent_loc
    loc = np.array(loc) * MINECRAFT_SCALE_FACTOR
    loc = loc[[0, 2, 1]] / parent_scale

    parent_rot = parent.to_quaternion()
    child_rot = child.to_quaternion()
    rot = parent_rot.rotation_difference(child_rot).to_euler('XZY')
    rot = np.array(rot)[[0, 2, 1]]
    rot = rot * np.array([1, -1, 1])
    rot = rot * 180/math.pi  # math.degrees() for array

    # matrix = get_local_matrix(parent, child)
    # loc, rot, scale = matrix.decompose()

    # loc = np.array(loc.xzy) * MINECRAFT_SCALE_FACTOR

    # scale = np.array(scale.xzy)

    # rot = rot.to_euler('XZY')
    # rot = np.array(rot)[[0, 2, 1]]
    # rot = rot * np.array([1, -1, 1])
    # rot = rot * 180/math.pi  # math.degrees() for array

    return loc, rot, scale


def get_animation_template(name, length):
    return {
        "format_version": "1.8.0",
        "animations": {
            f"animation.{name}": {
                "animation_length": (length-1)/bpy.context.scene.render.fps,
                "bones": {
                }
            }
        }
    }


def pick_closest_rotation(modify, close_to):
    '''
    Takes two numpy.arrays that represent rotation in
    euler rotation mode (using degrees). Modifies the
    values of 'modify' vector to get different representations
    of the same rotation. Picks the vector which is the
    closest to 'close_to' vector (euclidean distance).
    '''
    def _pick_closet_location(modify, close_to):
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



class OBJECT_OT_ExportAnimationOperator(bpy.types.Operator):
    bl_idname = "object.export_animation_operator"
    bl_label = "Export animation for bedrock model."
    bl_description = (
        "Exports animation of selected objects to bedrock entity animation "
        "format."
    )
    _timer = None
    _start_frame = None
    _animation_dict = None
    _animation_name = None

    def add_keyframe(self, bone, frame, type_, value):
        bones = self._animation_dict['animations'][
            f"animation.{self._animation_name}"
        ]["bones"]
        if bone not in bones:
            bones[bone] = {}
        if type_ not in ['rotation', 'position', 'scale']:
            print(
                f'WARNING! Unknown translation type - {type_}. Use rotation, '
                'position or scale instead.'
            )
        if type_ not in bones[bone]:
            bones[bone][type_] = {}
        bones[bone][type_][
            f'{round((frame-1)/bpy.context.scene.render.fps, 4)}'
        ] = json_vect(value)

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            # Back to the start frame
            bpy.context.scene.frame_current = self._start_frame
            return {'CANCELLED'}
        elif event.type == 'TIMER':
            # Do some stuff
            if bpy.context.scene.frame_current == 0:
                self.default_translation = get_transformations()
                self.prev_rotation = {
                    name:np.zeros(3)
                    for name in self.default_translation.keys()
                }
            else:
                current_translations = get_transformations()
                for d_key, d_val in self.default_translation.items():
                    # Get the difference from original
                    loc, rot, scale = to_mc_translation_vectors(
                        d_val['matrix'], current_translations[d_key]['matrix'],
                        d_val['scale'], current_translations[d_key]['scale'],
                        d_val['location'], current_translations[d_key]['location']
                    )


                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='position', value=loc
                    )
                    
                    rot = pick_closest_rotation(
                        rot, self.prev_rotation[d_key]
                    )
                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='rotation', value=rot
                    )

                    # TODO - solve scaling problems with animations
                    # (export_test_7)
                    self.add_keyframe(
                        bone=d_key, frame=bpy.context.scene.frame_current,
                        type_='scale', value=scale
                    )

                    self.prev_rotation[d_key] = rot  # Save previous rotation

            # Finish loop
            next_keyframe = get_next_keyframe()
            if next_keyframe is None:
                # Back to the start frame
                clear_mc_obj_tmp_properties()
                bpy.context.scene.frame_current = self._start_frame
                context.window_manager.event_timer_remove(self._timer)
                output = context.scene.bedrock_exporter.path_animation
                with open(output, 'w') as f:
                    json.dump(self._animation_dict, f, indent=4)
                return {'FINISHED'}
            else:
                bpy.context.scene.frame_current = math.ceil(next_keyframe)

        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager

        set_mc_obj_types()
        self._timer = wm.event_timer_add(0.5, window=context.window)
        self._start_frame = bpy.context.scene.frame_current
        self._animation_name = context.scene.bedrock_exporter.animation_name

        self._animation_dict = get_animation_template(
            self._animation_name,
            bpy.context.scene.frame_end
        )

        # Stop animation if running & jump to the first frame
        bpy.ops.screen.animation_cancel()
        bpy.context.scene.frame_current = 0

        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        clear_mc_obj_tmp_properties()
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


# Aditional operators
class OBJECT_OT_BedrockParentOperator(bpy.types.Operator):
    """Add parent child relation for bedrock model exporter."""
    bl_idname = "object.parent_operator"
    bl_label = "Parent bedrock bone"
    bl_description = "Parent object for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) < 2:
            return False
        elif not bpy.context.object.select_get():
            return False
        return True

    def execute(self, context):
        def _is_parent_loop(this, start):
            if 'mc_parent' in this:
                if this['mc_parent'] is start:
                    return True
                return _is_parent_loop(this['mc_parent'], start)
            return False

        # Check looped parents
        for obj in bpy.context.selected_objects:
            if obj is not bpy.context.object:
                if _is_parent_loop(bpy.context.object, obj):
                    self.report({'ERROR'}, "Loop in parents")
                    return {'CANCELLED'}
        # No loops detected
        for obj in bpy.context.selected_objects:
            if obj is not bpy.context.object:
                obj['mc_parent'] = bpy.context.object

        return {'FINISHED'}


def menu_bedrock_parent(self, context):
    '''Used for registration of OBJECT_OT_BedrockParentOperator class'''
    self.layout.operator(
        OBJECT_OT_BedrockParentOperator.bl_idname,
        text=OBJECT_OT_BedrockParentOperator.bl_label, icon="PLUGIN"
    )


class OBJECT_OT_BedrockParentClearOperator(bpy.types.Operator):
    """Clear parent child relation for bedrock model exporter."""
    bl_idname = "object.parent_clear_operator"
    bl_label = "Clear parent from bedrock bone"
    bl_description = "Clear parent for bedrock model exporter."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if len(context.selected_objects) >= 1:
            return True
        return False

    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if 'mc_parent' in obj:
                del obj['mc_parent']
        return {'FINISHED'}


def menu_bedrock_parent_clear(self, context):
    '''Used for registration of OBJECT_OT_BedrockParentClearOperator class'''
    self.layout.operator(
        OBJECT_OT_BedrockParentClearOperator.bl_idname,
        text=OBJECT_OT_BedrockParentClearOperator.bl_label, icon="PLUGIN"
    )
