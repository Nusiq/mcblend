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

def get_context_selected_objects(context):
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

def get_data_images():
    '''
    Returns the images from data

    >>> bpy.data.images
    '''
    return bpy.data.images

def set_image_pixels(image, pixels):
    '''
    Sets the pixels of the image

    >>> image.pixels = pixels
    '''
    image.pixels = pixels

def get_object_mcblend(object):
    '''
    Returns the mcblend property from object

    >>> object.mcblend
    '''
    return object.mcblend

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

def get_collection_objects(collection):
    '''
    Returns the objects from collection

    >>> collection.objects
    '''
    return collection.objects

def get_collection_children(collection):
    '''
    Returns the children from collection

    >>> collection.children
    '''
    return collection.children

def get_view_layer_objects(view_layer):
    '''
    Returns the objects from view layer

    >>> view_layer.objects
    '''
    return view_layer.objects

def get_object_material_slots(object):
    '''
    Returns the material slots from object

    >>> object.material_slots
    '''
    return object.material_slots

def get_object_data_materials(object):
    '''
    Returns the materials from object

    >>> object.data.materials
    '''
    return object.data.materials

def get_armature_data_bones(armature):
    '''
    Returns bones of the armature object.
    This function works under the assumption that the object is an armature.

    >>> armature.data.bones
    '''
    return armature.data.bones

def set_constraint_property(constraint, name, value):
    '''
    Sets the property of the constraint

    >>> constraint.<name> = value
    '''
    constraint.__setattr__(name, value)

def get_object_constraints(object):
    '''
    Returns the constraints from object

    >>> object.constraints
    '''
    return object.constraints

def get_object_children(object):
    '''
    Returns the children from object

    >>> object.children
    '''
    return object.children

def get_object_parent(object):
    '''
    Returns the parent from object

    >>> object.parent
    '''
    return object.parent

def set_object_parent(object, value):
    '''
    Sets the parent of the object

    >>> object.parent = value
    '''
    object.parent = value

def get_pose_bone_constraints(pose_bone):
    '''
    Returns the constraints from pose bone

    >>> pose_bone.constraints
    '''
    return pose_bone.constraints

def set_pose_bone_constraint_property(constraint, name, value):
    '''
    Sets the property of the constraint

    >>> constraint.<name> = value
    '''
    constraint.__setattr__(name, value)

def set_object_matrix_world(object, matrix):
    '''
    Sets the world matrix of the object

    >>> object.matrix_world = matrix
    '''
    object.matrix_world = matrix

def get_object_matrix_world(object):
    '''
    Returns the world matrix of the object

    >>> object.matrix_world
    '''
    return object.matrix_world

def set_object_matrix_parent_inverse(object, matrix):
    '''
    Sets the parent inverse matrix of the object

    >>> object.matrix_parent_inverse = matrix
    '''
    object.matrix_parent_inverse = matrix

def get_object_matrix_parent_inverse(object):
    '''
    Returns the parent inverse matrix of the object

    >>> object.matrix_parent_inverse
    '''
    return object.matrix_parent_inverse