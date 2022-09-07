'''
Custom Blender objects with properties of the resource pack.
'''
import bpy
from bpy.props import (
    CollectionProperty, EnumProperty, IntProperty, StringProperty)

from .common_data import MCBLEND_DbEntry
from .operator_func import reload_rp_entities
from .operator_func.db_handler import get_db


def enum_project_entities(self, context):
    '''List project entities as blender enum list.'''
    # pylint: disable=unused-argument
    connection = get_db()
    return [
        (str(i),j,k)  # It must be tuple of strings
        for i,j,k in connection.execute(
            '''
            SELECT ClientEntity_pk, identifier, identifier
            FROM ClientEntity;'''
        )]

# RENDER CONTROLLER'S MATERIAL FIELD
def enum_materials(self, context):
    q = '''
    SELECT
        ClientEntityMaterialField.identifier,
        ClientEntityMaterialField.shortName
    FROM
        RenderControllerMaterialsField
    JOIN
        ClientEntityMaterialField
        ON ClientEntityMaterialField.shortName = RenderControllerMaterialsField.shortName
    WHERE
        ClientEntityMaterialField.shortName = RenderControllerMaterialsField.shortName
        AND RenderControllerMaterialsField.RenderController_fk = ?
        AND ClientEntityMaterialField.ClientEntity_fk = ?
        AND RenderControllerMaterialsField.boneNamePattern = ?;
    '''
    connection = get_db()
    result = []
    for identifier, short_name in connection.execute(
            q, (self.active_rc_pk, self.active_entity_pk, self.pattern)):
        result.append((identifier, short_name, identifier))
    return result

class MCBLEND_RcMaterialPattern(bpy.types.PropertyGroup):
    '''
    Represents a material field in the render controller.
    '''
    # Reused properties from parent objects for quick access
    active_rc_pk: IntProperty()
    active_entity_pk: IntProperty()

    # Actual properties of the object
    pattern: StringProperty()
    materials: EnumProperty(
        items=enum_materials)

# RENDER CONTROLLER
def enum_geometries(self, context):
    # pylint: disable=unused-argument
    q = '''
    SELECT
        Geometry_pk,
        RenderControllerGeometryField.shortName,
        Geometry.identifier
    FROM
        ClientEntity
    JOIN ClientEntityRenderControllerField
        ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
    JOIN ClientEntityGeometryField
        ON ClientEntityGeometryField.ClientEntity_fk = ClientEntity_pk
    JOIN RenderController
        ON ClientEntityRenderControllerField.identifier = RenderController.identifier
    JOIN RenderControllerGeometryField
        ON RenderControllerGeometryField.RenderController_fk = RenderController_pk
    LEFT OUTER JOIN Geometry
        ON ClientEntityGeometryField.identifier = Geometry.identifier
    WHERE
        ClientEntityGeometryField.shortName == RenderControllerGeometryField.shortName
        -- AND ClientEntity.identifier == 'shapescape:citizen';
        AND RenderController_pk == ?
        AND ClientEntity_pk == ?;
    '''
    connection = get_db()
    entity_pk = self.active_entity_pk
    result = []
    for geo_pk, geo_short_name, geo_identifier in connection.execute(
            q, (self.primary_key, entity_pk)):
        result.append((str(geo_pk), geo_short_name, geo_identifier))
    return result

def enum_textures(self, context):
    # pylint: disable=unused-argument
    q = '''
    SELECT
        TextureFile_pk,
        RenderControllerTexturesField.shortName,
        TextureFile.path
    FROM
        ClientEntity
    JOIN ClientEntityRenderControllerField
        ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
    JOIN ClientEntityTextureField
        ON ClientEntityTextureField.ClientEntity_fk = ClientEntity_pk
    JOIN RenderController
        ON ClientEntityRenderControllerField.identifier = RenderController.identifier
    JOIN RenderControllerTexturesField
        ON RenderControllerTexturesField.RenderController_fk = RenderController_pk
    LEFT OUTER JOIN TextureFile
        ON ClientEntityTextureField.identifier = TextureFile.identifier
    WHERE
        ClientEntityTextureField.shortName == RenderControllerTexturesField.shortName
        AND RenderController_pk == ?
        AND ClientEntity_pk == ?;
    '''
    connection = get_db()
    entity_pk = self.active_entity_pk
    result = []
    for texture_pk, texture_short_name, texture_path in connection.execute(
            q, (self.primary_key, entity_pk)):
        val = (
            str(texture_pk),
            texture_short_name,
            texture_path.as_posix())
        result.append(val)
    return result

class MCBLEND_RenderController(bpy.types.PropertyGroup):
    '''
    Represents the properties to be selected in the render controller menu:
    geometry, texture, material
    '''
    # Reused properties from parent objects for quick access
    active_entity_pk: IntProperty()

    # Actual properties of the object
    primary_key: IntProperty()
    identifier: StringProperty()

    geometries: EnumProperty(  # type: ignore
        items=enum_geometries)
        # update=update_geometries)
    textures: EnumProperty(  # type: ignore
        items=enum_textures)
    material_patterns: CollectionProperty(
        type=MCBLEND_RcMaterialPattern)

# RESOURCE PACK (PROJECT)
def update_entity_names(self, context):
    '''
    Called on update of project.entity_names. Resets the values of selected
    enum items in 'entities' and 'render_controllers'. If necessary updates
    the cached values of selected entity and its render controllers.
    '''
    # pylint: disable=unused-argument

def update_selected_entity(self, context):
    '''
    Called on update of project.selected_entity.
    '''
    # pylint: disable=unused-argument
    q = '''
    SELECT
        RenderController_pk,
        RenderController.identifier
    FROM
        ClientEntity
    JOIN ClientEntityRenderControllerField
        ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
    LEFT OUTER JOIN RenderController
        ON ClientEntityRenderControllerField.identifier = RenderController.identifier
    WHERE
        ClientEntity_pk == ?;
    '''
    pk = self.entities[self.selected_entity].primary_key
    connection = get_db()
    self.render_controllers.clear()
    for rc_pk, rc_identifier in connection.execute(q, (pk,)):
        rc = self.render_controllers.add()
        rc.primary_key = rc_pk
        rc.identifier = rc_identifier
        rc.active_entity_pk = pk
        qq = '''
        SELECT DISTINCT boneNamePattern
        FROM RenderControllerMaterialsField
        WHERE RenderController_fk = ?;
        '''
        for pattern, in connection.execute(qq, (rc_pk,)):
            pattern_field = rc.material_patterns.add()
            pattern_field.pattern = pattern
            # Reused properties
            pattern_field.active_entity_pk = pk
            pattern_field.active_rc_pk = rc_pk


class MCBLEND_ProjectProperties(bpy.types.PropertyGroup):
    '''
    Represents top level selction in ResourcePack menu (the entity selection
    for importing).
    '''
    rp_path: StringProperty(  # type: ignore
        name="Resource pack path",
        description="Path to resource pack connected to this project",
        default="", subtype="DIR_PATH",
        update=lambda self, context: reload_rp_entities(context))
    selected_entity: StringProperty(   # type: ignore
        default="", update=update_selected_entity)
    entities: CollectionProperty(  # type: ignore
        type=MCBLEND_DbEntry)
    render_controllers: CollectionProperty(
        type=MCBLEND_RenderController)
    # entity_names: EnumProperty(  # type: ignore
    #     items=enum_project_entities,
    #     update=update_entity_names)

