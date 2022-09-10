from pathlib import Path
from sqlite3 import Connection
from .sqlite_bedrock_packs import load_rp, create_db
from functools import cache
from typing import Optional, Iterator

@cache
def get_db() -> Connection:
    '''Singleton for the database'''
    return create_db()

def delete_db():
    '''Delete all data from the database.'''
    db = get_db()
    db.execute('DELETE FROM ResourcePack;')

def load_resource_pack(path: Path):
    '''Load a resource pack into the database'''
    db = get_db()
    load_rp(
        db, path,
        selection_mode='include',
        client_entities=True,
        attachables=True,
        geometries=True,
        render_controllers=True,
        textures=True,
    )

def yield_materials_from_db(
        rc_pk: int, entity_pk: int,
        bone_name_pattern: str) -> Iterator[tuple[str, str]]:
    '''
    Yield all materials from the database, which are connected to the given
    render controller via the given bone name pattern, and have a definition
    in given entity. The results are tuples that contain
    - full identifier of the material
    - the short name used by RC and entity
    '''
    query = '''
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
    db = get_db()
    for identifier, short_name in db.execute(
            query, (rc_pk, entity_pk, bone_name_pattern)):
        yield short_name, identifier


def yield_geometries_from_db(
        rc_pk: int, entity_pk: int) -> Iterator[tuple[int, str, str]]:
    '''
    Yields all of the geometries from the database, which are connected to the
    given render controller and entity. The results are tuples that contain
    - primary key of geometry
    - short name used by RC and entity
    - full identifier.
    '''
    query = '''
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
        AND RenderController_pk == ?
        AND ClientEntity_pk == ?;
    '''
    db = get_db()
    for geometry_pk, short_name, identifier in db.execute(
            query, (rc_pk, entity_pk)):
        yield geometry_pk, short_name, identifier

def yield_textures_from_db(
        rc_pk: int, entity_pk: int) -> Iterator[tuple[int, str, Path]]:
    '''
    Yields all of the textures from the database, which are connected to the
    given render controller and entity. The results are tuples that contain:
    - primary key of texture file
    - short name used by RC and entity
    - full path to the texture file
    '''
    query = '''
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
    db = get_db()
    for texture_pk, short_name, path in db.execute(
            query, (rc_pk, entity_pk)):
        yield texture_pk, short_name, path

def yield_render_controllers_from_db(
        entity_pk: int) -> Iterator[tuple[Optional[int], str]]:
    '''
    Yields all of the render controllers from the database, which are connected
    to the given entity. The results are tuples that contain:
    - primary key of render controller
    - full identifier of render controller

    The primary key of the render controller can be None, if the render
    controller is not defined in the database.
    '''
    query = '''
    SELECT
        RenderController_pk,
        ClientEntityRenderControllerField.identifier
    FROM
        ClientEntity
    JOIN ClientEntityRenderControllerField
        ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
    LEFT OUTER JOIN RenderController
        ON ClientEntityRenderControllerField.identifier = RenderController.identifier
    WHERE
        ClientEntity_pk == ?;
    '''
    db = get_db()
    for rc_pk, identifier in db.execute(
            query, (entity_pk,)):
        yield rc_pk, identifier

def yield_bone_name_patterns_from_rc(
        render_controller_pk: int) -> Iterator[str]:
    '''
    Yields all of the bone name patterns from the given render controller.
    The result is a string with the bone name pattern.
    '''
    query = '''
    SELECT DISTINCT boneNamePattern
    FROM RenderControllerMaterialsField
    WHERE RenderController_fk = ?;
    '''
    db = get_db()
    for bone_name_pattern, in db.execute(query, (render_controller_pk,)):
        yield bone_name_pattern

def yield_entities_from_db() -> Iterator[tuple[int, str]]:
    '''
    Yields all of the entities from the database. The results are tuples that
    contain:
    - primary key of the entity
    - identifier of the entity
    Results are ordered by identifier
    '''
    query = '''
    SELECT ClientEntity_pk, identifier
    FROM ClientEntity
    ORDER BY identifier;
    '''
    db = get_db()
    for entity_pk, identifier in db.execute(query):
        yield entity_pk, identifier
