'''
Custom Blender objects with properties of the resource pack.
'''
from typing import Any

import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, PointerProperty, StringProperty)

from .operator_func import reload_rp_entities
from .operator_func.molang import find_resources
from .common_data import (
    MCBLEND_EnumCache, MCBLEND_JustName,
    MCBLEND_NameValuePair)

# Resource pack (importer)
class MCBLEND_EntityProperties(bpy.types.PropertyGroup):
    '''
    Cached properties of an entity from resource pack.
    '''
    name: StringProperty(  # type: ignore
        name="", description="Name of the entity.",
        default="", maxlen=1024)

    render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_JustName, name='Textures')
    textures: CollectionProperty(  # type: ignore
        type=MCBLEND_NameValuePair, name='Textures')
    geometries: CollectionProperty(  # type: ignore
        type=MCBLEND_NameValuePair, name='Geometries')
    materials: CollectionProperty(  # type: ignore
        type=MCBLEND_NameValuePair, name='Materials')

def enum_rc_materials(self, context):
    '''Lists materials available to be used by render controller'''
    # Loading values from cache (optimal solution)
    if self.value_cache.is_cached:
        return [(i, i, i) for i in self.value_cache.values.keys()]
    # Suboptimal solution loading values from string
    # WARNING! The values can't be cached from this context. The
    # method that create cache must be called somewhere else or the enum will
    # always be generated from Molang string.
    owner = context.scene.mcblend_project.render_controllers[
        self.owner_name]
    return [
        (i, i, i) for i in
        sorted(find_resources(
            self.value_molang, 'material', owner.material_arrays))]

class MCBLEND_MaterialProperties(bpy.types.PropertyGroup):
    '''Properties of a material from a render controller'''
    name: StringProperty(  # type: ignore
        name="Pattern", description="Bone pattern of a material",
        default="", maxlen=1024)
    value_molang: StringProperty(  # type: ignore
        name="Pattern", description="The molang value of the material",
        default="", maxlen=1024)
    value: EnumProperty(  # type: ignore
        name="Texture", description=(
            "The texture used by the importer for this render controller"),
        items=enum_rc_materials)
    value_cache: PointerProperty(type=MCBLEND_EnumCache)  # type: ignore
    # Ugly hack to access the owner data
    owner_name: StringProperty(  # type: ignore
        name="Name", description=(
            "Name of the render controller that owns this materials "
            "properties"),
        default="", maxlen=1024)

    def try_reload_cached_values(self, context):
        '''
        Tries to load the list of the available material names from the
        value_molang into value_cache. If the value_cache is already
        loaded then does nothing.
        '''
        if self.value_cache.is_cached:
            return  # nothing to do
        owner = context.scene.mcblend_project.render_controllers[
            self.owner_name]
        resources = find_resources(
            self.value_molang, 'material', owner.material_arrays)
        for resource_name in sorted(resources):
            new_val = self.value_cache.values.add()
            new_val.name = resource_name
        self.value_cache.is_cached = True

class MCBLEND_RenderControllerArrayProperties(bpy.types.PropertyGroup):
    '''
    Propertis of an array in render controller (geometry, texture or material
    array)
    '''
    name: StringProperty(  # type: ignore
        name="Name", description="Name of the array",
        default="", maxlen=1024)
    items: CollectionProperty(  # type: ignore
        type=MCBLEND_JustName,
        description="The list of molang variables from the array")

def enum_rc_geometries(self, context):
    '''Lists geometries for render controller'''
    # pylint: disable=unused-argument
    # Loading values from cache (optimal solution)
    if self.geometry_cache.is_cached:
        return [(i, i, i) for i in self.geometry_cache.values.keys()]
    # Suboptimal solution loading values from string
    # WARNING! The values can't be cached from this context.
    return [
        (i, i, i) for i in
        sorted(find_resources(
            self.geometry_molang, 'geometry', self.geometry_arrays))]

def enum_rc_textures(self, context):
    '''Lists textures for render controller'''
    # pylint: disable=unused-argument
    # Loading values from cache (optimal solution)
    if self.texture_cache.is_cached:
        return [(i, i, i) for i in self.texture_cache.values.keys()]
    # Suboptimal solution loading values from string
    # WARNING! The values can't be cached from this context.
    return [
        (i, i, i) for i in
        sorted(find_resources(
            self.texture_molang, 'geometry', self.texture_arrays))]

class MCBLEND_RenderControllersProperties(bpy.types.PropertyGroup):
    '''Properties of a render controller from resource pack.'''
    name: StringProperty(  # type: ignore
        name="Name", description="Name of the render controller",
        default="", maxlen=1024)
    geometry_arrays: CollectionProperty(  # type: ignore
        type=MCBLEND_RenderControllerArrayProperties)
    texture_arrays: CollectionProperty(  # type: ignore
        type=MCBLEND_RenderControllerArrayProperties)
    material_arrays: CollectionProperty(  # type: ignore
        type=MCBLEND_RenderControllerArrayProperties)

    geometry_molang: StringProperty(  # type: ignore
        name="Geometry molang",
        description=(
            "The Molang value of the geometry property straight from the "
            "resource pack"),
        default="", maxlen=1024)
    geometry: EnumProperty(  # type: ignore
        name="Geometry", description="The geometry used by the importer",
        items=enum_rc_geometries)
    geometry_cache: PointerProperty(type=MCBLEND_EnumCache)  # type: ignore
    texture_molang: StringProperty(  # type: ignore
        name="Texture molang",
        description=(
            "The Molang value of the texture property straight from the "
            "resource pack"),
        default="", maxlen=1024)
    texture: EnumProperty(  # type: ignore
        name="Texture", description=(
            "The texture used by the importer for this render controller"),
        items=enum_rc_textures)
    texture_cache: PointerProperty(type=MCBLEND_EnumCache)  # type: ignore
    materials: CollectionProperty(  # type: ignore
        type=MCBLEND_MaterialProperties)

    def try_reload_cached_values(self):
        '''
        Tries to load the values for the 'geometry' and 'texture' enums from
        the Molang in 'geometry_molang' and 'texture_molang' into the
        'geometry_cache' and 'texture_cache' or does nothing if the values
        are already loaded.
        '''
        # Load geometry if necessary
        if not self.geometry_cache.is_cached:
            resources = find_resources(
                self.geometry_molang, 'geometry', self.geometry_arrays)
            for resource_name in sorted(resources):
                new_val = self.geometry_cache.values.add()
                new_val.name = resource_name
            self.geometry_cache.is_cached = True
        # Load texture if necessary
        if not self.texture_cache.is_cached:
            resources = find_resources(
                self.texture_molang, 'texture', self.texture_arrays)
            for resource_name in sorted(resources):
                new_val = self.texture_cache.values.add()
                new_val.name = resource_name
            self.texture_cache.is_cached = True

def enum_project_entities(self, context):
    '''List project entities as blender enum list.'''
    # pylint: disable=unused-argument
    return [
        (i, i, i) for i in
        sorted(j.name for j in context.scene.mcblend_project.entities)
    ]

def update_entity_names(self, context):
    '''
    Called on update of project.entity_names. Resets the values of selected
    enum items in 'entities' and 'render_controllers'. If necessary updates
    the cached values of selected entity and its render controllers.
    '''
    # pylint: disable=unused-argument
    if self.entity_names not in self.entities:
        return
    entity = self.entities[self.entity_names]
    render_controller_names = entity.render_controllers.keys()
    # Reload all cached values of render controllers and their materials
    # set the enum propreties to first item from the list
    self.fake_render_controllers.clear()
    for rc_name in render_controller_names:
        if rc_name not in self.render_controllers.keys():  # Add fake RC
            self.add_fake_render_controller(rc_name, entity)
            continue
        rc = self.render_controllers[rc_name]
        rc.try_reload_cached_values()
        if len(rc.geometry_cache.values) > 0:
            rc.geometry = rc.geometry_cache.values[0].name
        if len(rc.texture_cache.values) > 0:
            rc.texture = rc.texture_cache.values[0].name
        for material in rc.materials:
            material.try_reload_cached_values(context)
            if len(material.value_cache.values) > 0:
                material.value = material.value_cache.values[0].name


class MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''
    The properties of the Resource Pack opened in this Blender project.
    '''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_EntityProperties)
    render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_RenderControllersProperties)
    fake_render_controllers: CollectionProperty(  # type: ignore
        type=MCBLEND_RenderControllersProperties,
        description=(
            "Render controllers not defined in the resource pack but with a "
            "reference from the active in GUI.")
        )
    entity_names: EnumProperty(  # type: ignore
        items=enum_project_entities,
        update=update_entity_names)

    def add_fake_render_controller(self, name: str , entity: Any):
        '''
        Populates a collection of fake_render_controllers with data from an
        entity in order to give the user an option to configure the display
        of render controllers that aren't defined in resource pack but
        are used by the entity.
        '''
        if name in self.fake_render_controllers.keys():
            return  # Already added
        fake_rc = self.fake_render_controllers.add()
        fake_rc.name = name
        # Add full list of geometries to cache
        fake_rc.geometry_cache.is_cached = True
        for geo in entity.geometries.keys():
            fake_rc.geometry_cache.values.add().name = geo
        # Add full list of textures to cache
        fake_rc.texture_cache.is_cached = True
        for texture in entity.textures.keys():
            fake_rc.texture_cache.values.add().name = texture
        # Add full list of materials to cache
        fake_material = fake_rc.materials.add()
        fake_material.name = '*'
        fake_material.value_cache.is_cached = True
        for material in entity.materials.keys():
            fake_material.value_cache.values.add().name = material
