from __future__ import annotations

from pathlib import Path
from .sqlite_bedrock_packs import load_rp, create_db
from typing import Optional

# Don't use lru_cache(maxsize=1) sometimes there are more than 1 lists of the
# same type shown in the UI. Just make sure to call cache_clear() when you can.
from functools import cache

@cache
def get_db_handler() -> DbHandler:
    '''Singleton for the database handler'''
    return DbHandler()

class DbHandler:
    def __init__(self):
        self.db = create_db()
    
    def delete_db(self):
        '''Delete all data from the database.'''
        self.db.execute('DELETE FROM ResourcePack;')
        self.gui_enum_materials_from_db.cache_clear()
        self.gui_enum_geometries_from_db.cache_clear()
        self.gui_enum_textures_from_db.cache_clear()
        self.list_render_controllers_from_db.cache_clear()
        self.list_bone_name_patterns_from_rc.cache_clear()
        self.list_entities_with_models_and_rc_from_db.cache_clear()

    def load_resource_pack(self, path: Path):
        '''Load a resource pack into the database'''
        load_rp(
            self.db, path,
            selection_mode='include',
            client_entities=True,
            attachables=True,
            geometries=True,
            render_controllers=True,
            textures=True,
        )

    @cache
    def gui_enum_materials_from_db(
            self, rc_pk: int, entity_pk: int,
            bone_name_pattern: str) -> list[tuple[str, str, str]]:
        '''
        Lists all materials from the database, which are connected to the given
        render controller via the given bone name pattern, and have a
        definition in given entity. The results are tuples that contain
        - full identifier of the material
        - the short name used by RC and entity

        The actual result is: ("short_name;identifier", short_name, identifier)

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            ClientEntityMaterialField.shortName || ';' || ClientEntityMaterialField.identifier,
            ClientEntityMaterialField.shortName,
            ClientEntityMaterialField.identifier
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
        return [
            (str(identifier), str(name), str(description))
            for identifier, name, description in
            self.db.execute(query, (rc_pk, entity_pk, bone_name_pattern))
        ]

    @cache
    def gui_enum_fake_material_patterns_from_db(
            self, entity_pk: int):
        '''
        Lists all of the materials from the database, which are connected to
        give entity. The results are tuples that contain.
        - full identifier of the material
        - the short name used by RC and entity

        The actual result is: ("short_name;identifier", short_name, identifier)

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            ClientEntityMaterialField.shortName || ';' || ClientEntityMaterialField.identifier,
            ClientEntityMaterialField.shortName,
            ClientEntityMaterialField.identifier
        FROM
            ClientEntityMaterialField
        WHERE
            ClientEntityMaterialField.ClientEntity_fk = ?;
        '''
        return [
            (str(identifier), str(name), str(description))
            for identifier, name, description in
            self.db.execute(query, (entity_pk,))
        ]


    @cache
    def gui_enum_geometries_from_db(
            self, rc_pk: int, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the geometries from the database, which are connected to
        the given render controller and entity. The results are tuples that
        contain:
        - primary key of geometry
        - short name used by RC and entity
        - full identifier.

        The first value (geometry primary key) contains a string that
        can be converted to int. The geometry must be valid, if client entity
        and RC have references to geometries that don't exist, they won't be
        listed here.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            Geometry_pk,
            ClientEntityGeometryField.shortName,
            ClientEntityGeometryField.identifier
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
        JOIN Geometry
            ON ClientEntityGeometryField.identifier = Geometry.identifier
        WHERE
            ClientEntityGeometryField.shortName == RenderControllerGeometryField.shortName
            AND RenderController_pk == ?
            AND ClientEntity_pk == ?;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.execute(query, (rc_pk, entity_pk))
        ]

    @cache
    def gui_enum_geometries_for_fake_rc_from_db(
            self, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the geometries from the database, which are connected to
        given entity. The results are tuples that contain:
        - primary key of the geometry
        - short name used by the entity
        - full identifier.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            Geometry_pk,
            ClientEntityGeometryField.shortName,
            ClientEntityGeometryField.identifier
        FROM
            ClientEntity
        JOIN ClientEntityGeometryField
            ON ClientEntityGeometryField.ClientEntity_fk = ClientEntity_pk
        JOIN Geometry
            ON ClientEntityGeometryField.identifier = Geometry.identifier
        WHERE
            ClientEntity_pk == ?;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.execute(query, (entity_pk,))
        ]

    @cache
    def gui_enum_textures_from_db(
            self, rc_pk: int, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the textures from the database, which are connected to the
        given render controller and entity. The results are tuples that
        contain:
        - primary key of texture file
        - short name used by RC and entity
        - full path to the texture file

        The texture file might not exist, in this case the primary key is
        "-1".

        The values are cached and prepared to be used as an enum property in
        GUI.
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
        return [
            (
                "-1" if texture_pk is None else str(texture_pk),
                str(short_name),
                path.as_posix()
            )
            for texture_pk, short_name, path in
            self.db.execute(query, (rc_pk, entity_pk))
        ]

    @cache
    def gui_enum_textures_for_fake_rc_from_db(
            self, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the textures from the database, which are connected to the
        given entity. The results are tuples that contain:
        - primary key of texture file
        - short name used by entity
        - full path to the texture file

        The texture file might not exist, in this case the primary key is
        "-1".

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT
            TextureFile_pk,
            ClientEntityTextureField.shortName,
            TextureFile.path
        FROM
            ClientEntity
        JOIN ClientEntityTextureField
            ON ClientEntityTextureField.ClientEntity_fk = ClientEntity_pk
        LEFT OUTER JOIN TextureFile
            ON ClientEntityTextureField.identifier = TextureFile.identifier
        WHERE
            ClientEntity_pk == ?;
        '''
        return [
            (
                "-1" if texture_pk is None else str(texture_pk),
                str(short_name),
                path.as_posix()
            )
            for texture_pk, short_name, path in
            self.db.execute(query, (entity_pk,))
        ]

    @cache
    def list_render_controllers_from_db(
            self, entity_pk: int) -> list[tuple[Optional[int], str]]:
        '''
        Lists all of the render controllers from the database, which are
        connected to the given entity. The results are tuples that contain:
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
        return [
            (rc_pk, identifier)
            for rc_pk, identifier in
            self.db.execute(query, (entity_pk,))
        ]

    @cache
    def list_bone_name_patterns_from_rc(
            self, render_controller_pk: int) -> list[str]:
        '''
        Lists all of the bone name patterns from the given render controller.
        The result is a string with the bone name pattern.
        '''
        query = '''
        SELECT DISTINCT boneNamePattern
        FROM RenderControllerMaterialsField
        WHERE RenderController_fk = ?;
        '''
        return [
            bone_name_pattern
            for bone_name_pattern, in
            self.db.execute(query, (render_controller_pk,))
        ]

    @cache
    def list_entities_with_models_and_rc_from_db(
            self) -> list[tuple[int, str]]:
        '''
        Lists all of the all of the  entities from database that use geometries
        and render_controlelrs fields. There must be at least one 
        geometry in the database that connects to the geometry field. The
        render controller don't have to exist but there must be a render
        controller field in the client entity file.

        The results are tuples that contain:

        - primary key of the entity
        - identifier of the entity

        Results are ordered by identifier
        '''

        # DISTINCT in SELECT is needed, because there can be multiple geometry
        # or rc fields in one entity
        query = '''
        SELECT DISTINCT
            ClientEntity_pk, ClientEntity.identifier
        FROM
            ClientEntity
        JOIN ClientEntityGeometryField
            ON ClientEntityGeometryField.ClientEntity_fk = ClientEntity_pk
        JOIN ClientEntityRenderControllerField
            ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
        JOIN  -- Geometry file must exist
            Geometry
            ON Geometry.identifier = ClientEntityGeometryField.identifier
        ORDER BY ClientEntity.identifier;
        '''
        return [
            (entity_pk, identifier)
            for entity_pk, identifier in
            self.db.execute(query)
        ]

    def get_texture_file_path(self, texture_file_pk: int) -> Path:
        '''
        Returns the path to the texture file with the given primary key.
        '''
        query = '''
        SELECT path
        FROM TextureFile
        WHERE TextureFile_pk == ?;
        '''
        return self.db.execute(query, (texture_file_pk,)).fetchone()[0]

    def get_geometry(self, geometry_pk: int) -> tuple[Path, str]:
        '''
        Returns pair of the path to the geometry file and its identifier
        based on the geometry primary key from the database.
        '''
        query = '''
        SELECT
            GeometryFile.path,
            Geometry.identifier
        FROM
            Geometry
        JOIN
            GeometryFile
            ON Geometry.GeometryFile_fk == GeometryFile_pk
        WHERE
            Geometry_pk == ?;
        '''
        return tuple(self.db.execute(query, (geometry_pk,)).fetchone())