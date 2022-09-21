'''
This module provides functions to access certain objects from bpy module and
still have type hints. This is necessary because the stub modules for bpy
like fake-bpy-module aren't perfect and they often miss some attibutes or
annotations.

This is by no means an optimal solution, but it makes the static type checking
possible and the code easier to maintain.

The functions from this module are annotated in typed_bpy_access.pyi
'''
import bpy

def get_context_object(context):
    '''
    Returns the object from the context
    
    >>> context.object
    '''
    return context.object

def get_context_scene_mcblend_project(context):
    '''
    Returns the project properties from context
    
    >>> context.scene.mcblend_project
    '''
    return context.scene.mcblend_project

def get_context_scene_mcblend_events(context):
    '''
    Returns the events properties from context
    
    >>> context.scene.mcblend_events
    '''
    return context.scene.mcblend_events

def get_context_scene_mcblend_active_event(context):
    '''
    Returns the active event id from context
    
    >>> context.scene.mcblend_active_event
    '''
    return context.scene.mcblend_active_event

def set_context_scene_mcblend_active_event(context, value):
    '''
    Sets the active event id in context

    >>> context.scene.mcblend_active_event = value
    '''
    context.scene.mcblend_active_event = value

def get_context_scene_mcblend_uv_groups(context):
    '''
    Returns the uv groups from context
    
    >>> context.scene.mcblend_uv_groups
    '''
    return context.scene.mcblend_uv_groups

def get_selected_objects(context):
    '''
    Returns selected objects list from context

    >>> context.selected_objects
    '''
    return context.selected_objects

def get_data_objects():
    '''
    Returns the objects from data

    >>> bpy.data.objects
    '''
    return bpy.data.objects

def get_data_meshes():
    '''
    Returns the objects from data

    >>> bpy.data.meshes
    '''
    return bpy.data.meshes

def get_data_images():
    '''
    Returns the images from data

    >>> bpy.data.images
    '''
    return bpy.data.images

def set_pixels(obj, pixels):
    '''
    >>> obj.pixels = pixels
    '''
    obj.pixels = pixels

def get_mcblend(obj):
    '''
    >>> obj.mcblend
    '''
    return obj.mcblend

def set_operator_property(operator, name, value):
    '''
    Sets the property of the operator

    >>> operator.<name> = value
    '''
    operator.__setattr__(name, value)

def new_colection(name):
    '''
    Creates new collection with given name

    >>> bpy.data.collections.new(name)
    '''
    return bpy.data.collections.new(name)

def get_objects(obj):
    '''
    >>> obj.objects
    '''
    return obj.objects

def get_material_slots(obj):
    '''
    >>> obj.material_slots
    '''
    return obj.material_slots

def get_data_materials(obj):
    '''
    >>> obj.data.materials
    '''
    return obj.data.materials

def get_data_uv_layers(obj):
    '''
    >>> obj.data.uv_layers
    '''
    return obj.data.uv_layers

def get_uv_layers(obj):
    '''
    >>> obj.uv_layers
    '''
    return obj.uv_layers

def get_data(obj):
    '''
    >>> obj.data
    '''
    return obj.data

def get_data_bones(obj):
    '''
    >>> obj.data.bones
    '''
    return obj.data.bones

def get_data_edit_bones(obj):
    '''
    >>> obj.data.edit_bones
    '''
    return obj.data.edit_bones

def get_pose_bones(obj):
    '''
    >>> obj.pose.bones
    '''
    return obj.pose.bones

def set_matrix(obj, matrix):
    '''
    >>> obj.matrix = matrix
    '''
    obj.matrix = matrix

def set_constraint_property(constraint, name, value):
    '''
    Sets the property of the constraint

    >>> constraint.<name> = value
    '''
    constraint.__setattr__(name, value)

def get_constraints(object):
    '''
    >>> object.constraints
    '''
    return object.constraints

def get_children(obj):
    '''
    >>> obj.children
    '''
    return obj.children

def get_parent(obj):
    '''
    >>> obj.parent
    '''
    return obj.parent

def set_parent(obj, value):
    '''
    >>> obj.parent = value
    '''
    obj.parent = value

def set_pose_bone_constraint_property(constraint, name, value):
    '''
    Sets the property of the constraint

    >>> constraint.<name> = value
    '''
    constraint.__setattr__(name, value)

def set_matrix_world(obj, matrix):
    '''
    >>> obj.matrix_world = matrix
    '''
    obj.matrix_world = matrix

def get_matrix_world(obj):
    '''
    >>> obj.matrix_world
    '''
    return obj.matrix_world

def get_matrix_local(obj):
    '''
    >>> obj.matrix_local
    '''
    return obj.matrix_local

def set_matrix_parent_inverse(obj, matrix):
    '''
    >>> obj.matrix_parent_inverse = matrix
    '''
    obj.matrix_parent_inverse = matrix

def get_matrix_parent_inverse(obj):
    '''
    >>> obj.matrix_parent_inverse
    '''
    return obj.matrix_parent_inverse

def get_loop_indices(obj):
    '''
    >>> obj.loop_indices
    '''
    return obj.loop_indices

def get_rotation_euler(obj):
    '''
    >>> obj.rotation_euler
    '''
    return obj.rotation_euler

def get_location(obj):
    '''
    >>> obj.location
    '''
    return obj.location

def set_location(obj, value):
    '''
    >>> obj.location = value
    '''
    obj.location = value

def get_data_vertices(obj):
    '''
    >>> obj.data.vertices
    '''
    return obj.data.vertices

def get_data_polygons(obj):
    '''
    >>> obj.data.polygons
    '''
    return obj.data.polygons

def get_head(obj):
    '''
    >>> obj.head
    '''
    return obj.head

def get_tail(obj):
    '''
    >>> obj.tail
    '''
    return obj.tail

def add(obj1, obj2):
    '''
    >>> obj1 + obj2
    '''
    return obj1 + obj2

def subtract(obj1, obj2):
    '''
    >>> obj1 - obj2
    '''
    return obj1 - obj2

def matmul(obj1, obj2):
    '''
    >>> obj1 @ obj2
    '''
    return obj1 @ obj2

def get_timeline_markers(obj):
    '''
    >>> obj.timeline_markers
    '''
    return obj.timeline_markers

def get_fcurves(obj):
    '''
    >>> obj.fcurves
    '''
    return obj.fcurves

def get_keyframe_points(obj):
    '''
    >>> obj.keyframe_points
    '''
    return obj.keyframe_points

def get_nla_tracks(obj):
    '''
    >>> obj.nla_tracks
    '''
    return obj.nla_tracks


def get_strips(obj):
    '''
    >>> obj.strips
    '''
    return obj.strips

def cross(a, b):
    '''
    >>> a.cross(b)
    '''
    return a.cross(b)

def neg(a):
    '''
    >>> -a
    '''
    return -a

def get_co(obj):
    '''
    >>> obj.co
    '''
    return obj.co


def set_co(obj, co):
    '''
    >>> obj.co = co
    '''
    obj.co = co

def decompose(obj):
    '''
    >>> obj.decompose()
    '''
    return obj.decompose()
