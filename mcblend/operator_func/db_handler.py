'''
The module that defines the classes and functions that are used to interact
with the database while loading data from resource packs.
'''
# pylint: disable=method-cache-max-size-none
from __future__ import annotations

from pathlib import Path
# load_rp
from typing import Optional
# Don't use lru_cache(maxsize=1) sometimes there are more than 1 lists of the
# same type shown in the UI. Just make sure to call cache_clear() when you can.
from functools import cache

from .sqlite_bedrock_packs import Database

@cache
def get_db_handler() -> DbHandler:
    '''Singleton for the database handler'''
    return DbHandler()

class DbHandler:
    '''
    A singleton class that is used to interact with the database that loads
    and stores the data from resource packs.
    '''
    def __init__(self):
        self.db = Database.create()
        self.is_loaded = False

    def load_db_from_file(self, path: Path):
        '''Loads existing database from a file.'''
        self.db.close()
        self.db = Database.open(path)  # type: ignore
        self.is_loaded = True

    def _clear_cache(self):
        '''Clears all of the cached values.'''
        # pylint: disable=no-member
        self.gui_enum_entity_materials.cache_clear()
        self.gui_enum_entity_fake_material_patterns.cache_clear()
        self.gui_enum_entity_geometries.cache_clear()
        self.gui_enum_entity_geometries_for_fake_rc.cache_clear()
        self.gui_enum_entity_textures.cache_clear()
        self.gui_enum_entity_textures_for_fake_rc.cache_clear()
        self.list_entity_render_controllers.cache_clear()
        self.list_entities_with_models_and_rc.cache_clear()

        self.gui_enum_attachable_materials.cache_clear()
        self.gui_enum_attachable_fake_material_patterns.cache_clear()
        self.gui_enum_attachable_geometries.cache_clear()
        self.gui_enum_attachable_geometries_for_fake_rc.cache_clear()
        self.gui_enum_attachable_textures.cache_clear()
        self.gui_enum_attachable_textures_for_fake_rc.cache_clear()
        self.list_attachable_render_controllers.cache_clear()
        self.list_attachables_with_models_and_rc.cache_clear()

        self.list_bone_name_patterns.cache_clear()

    def delete_db(self):
        '''Delete all data from the database.'''
        self._clear_cache()
        self.db.connection.execute('DELETE FROM ResourcePack;')
        self.is_loaded = False

    def load_resource_pack(self, path: Path):
        '''Load a resource pack into the database'''
        # If the RP is already loaded, reload it. It must be deleted because
        # otherwise load_rp() function would fail if the RP with that path is
        # already loaded.
        self._clear_cache()
        self.db.connection.execute(
            'DELETE FROM ResourcePack WHERE path = ?;', (path.as_posix(),))
        self.db.load_rp(
            path, include=(
                "client_entities",
                "attachables",
                "geometries",
                "render_controllers",
                "textures")
        )
        self.is_loaded = True

    @cache
    def gui_enum_entity_materials(
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

        # There is no need to add additional constraints to the query to make
        # it select the most recent resource pack because the query already
        # requires the primary keys of RC and enity, which are unique.
        query = '''
        SELECT DISTINCT
            RenderControllerMaterialsField_pk,
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
            self.db.connection.execute(query, (rc_pk, entity_pk, bone_name_pattern))
        ]

    @cache
    def gui_enum_attachable_materials(
            self, rc_pk: int, attachable_pk: int,
            bone_name_pattern: str) -> list[tuple[str, str, str]]:
        '''
        Lists all materials from the database, which are connected to the given
        render controller via the given bone name pattern, and have a
        definition in given attachable. The results are tuples that contain
        - full identifier of the material
        - the short name used by RC and attachable

        The actual result is: ("short_name;identifier", short_name, identifier)

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''

        # There is no need to add additional constraints to the query to make
        # it select the most recent resource pack because the query already
        # requires the primary keys of RC and enity, which are unique.
        query = '''
        SELECT DISTINCT
            RenderControllerMaterialsField_pk,
            AttachableMaterialField.shortName,
            AttachableMaterialField.identifier
        FROM
            RenderControllerMaterialsField
        JOIN
            AttachableMaterialField
            ON AttachableMaterialField.shortName = RenderControllerMaterialsField.shortName
        WHERE
            AttachableMaterialField.shortName = RenderControllerMaterialsField.shortName
            AND RenderControllerMaterialsField.RenderController_fk = ?
            AND AttachableMaterialField.Attachable_fk = ?
            AND RenderControllerMaterialsField.boneNamePattern = ?;
        '''
        return [
            (str(identifier), str(name), str(description))
            for identifier, name, description in
            self.db.connection.execute(query, (rc_pk, attachable_pk, bone_name_pattern))
        ]

    @cache
    def gui_enum_entity_fake_material_patterns(
            self, entity_pk: int):
        '''
        Lists all of the materials from the database, which are connected to
        give entity. The results are tuples that contain.
        - full identifier of the material
        - the short name used by RC and entity

        The actual result is: (ClientEntityMaterialField_pk, short_name, identifier)

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            ClientEntityMaterialField_pk,
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
            self.db.connection.execute(query, (entity_pk,))
        ]

    @cache
    def gui_enum_attachable_fake_material_patterns(
            self, attachable_pk: int):
        '''
        Lists all of the materials from the database, which are connected to
        give attachable. The results are tuples that contain.
        - full identifier of the material
        - the short name used by RC and attachable

        The actual result is: (AttachableMaterialField_pk, short_name, identifier)

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT DISTINCT
            AttachableMaterialField_pk,
            AttachableMaterialField.shortName,
            AttachableMaterialField.identifier
        FROM
            AttachableMaterialField
        WHERE
            AttachableMaterialField.Attachable_fk = ?;
        '''
        return [
            (str(identifier), str(name), str(description))
            for identifier, name, description in
            self.db.connection.execute(query, (attachable_pk,))
        ]

    @cache
    def gui_enum_entity_geometries(
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
        SELECT pk, shortName, identifier || '\n' || path FROM (
            SELECT
                Geometry_pk AS pk,
                ClientEntityGeometryField.shortName AS shortName,
                ClientEntityGeometryField.identifier AS identifier,
                GeometryFile.path AS path
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
            JOIN GeometryFile
                ON Geometry.GeometryFile_fk = GeometryFile_pk
            WHERE
                ClientEntityGeometryField.shortName == RenderControllerGeometryField.shortName
                AND RenderController_pk == ?
                AND ClientEntity_pk == ?
            ORDER BY
                Geometry_pk DESC
        )
        GROUP BY
            shortName,
            identifier;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.connection.execute(query, (rc_pk, entity_pk))
        ]

    @cache
    def gui_enum_attachable_geometries(
            self, rc_pk: int, attachable_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the geometries from the database, which are connected to
        the given render controller and attachable. The results are tuples that
        contain:
        - primary key of geometry
        - short name used by RC and attachable
        - full identifier.

        The first value (geometry primary key) contains a string that
        can be converted to int. The geometry must be valid, if client attachable
        and RC have references to geometries that don't exist, they won't be
        listed here.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, identifier || '\n' || path FROM (
            SELECT
                Geometry_pk AS pk,
                AttachableGeometryField.shortName AS shortName,
                AttachableGeometryField.identifier AS identifier,
                GeometryFile.path AS path
            FROM
                Attachable
            JOIN AttachableRenderControllerField
                ON AttachableRenderControllerField.Attachable_fk = Attachable_pk
            JOIN AttachableGeometryField
                ON AttachableGeometryField.Attachable_fk = Attachable_pk

            JOIN RenderController
                ON AttachableRenderControllerField.identifier = RenderController.identifier
            JOIN RenderControllerGeometryField
                ON RenderControllerGeometryField.RenderController_fk = RenderController_pk

            JOIN Geometry
                ON AttachableGeometryField.identifier = Geometry.identifier
            JOIN GeometryFile
                ON Geometry.GeometryFile_fk = GeometryFile_pk
            WHERE
                AttachableGeometryField.shortName == RenderControllerGeometryField.shortName
                AND RenderController_pk == ?
                AND Attachable_pk == ?
            ORDER BY
                Geometry_pk DESC
        )
        GROUP BY
            shortName,
            identifier;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.connection.execute(query, (rc_pk, attachable_pk))
        ]

    @cache
    def gui_enum_entity_geometries_for_fake_rc(
            self, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the geometries from the database, which are connected to
        given entity. The results are tuples that contain:
        - primary key of the geometry
        - short name used by the entity
        - full identifier and a path to the geometry file separated with new
          line character.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, identifier || '\n' || path FROM (
            SELECT
                Geometry_pk AS pk,
                ClientEntityGeometryField.shortName AS shortName,
                ClientEntityGeometryField.identifier AS identifier,
                GeometryFile.path AS path
            FROM
                ClientEntityGeometryField
            JOIN Geometry
                ON ClientEntityGeometryField.identifier = Geometry.identifier
            JOIN GeometryFile
                ON Geometry.GeometryFile_fk = GeometryFile_pk
            WHERE
                ClientEntityGeometryField.ClientEntity_fk == ?
            ORDER BY
                Geometry_pk DESC
        )
        GROUP BY
            shortName,
            identifier;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.connection.execute(query, (entity_pk,))
        ]

    @cache
    def gui_enum_attachable_geometries_for_fake_rc(
            self, attachable_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the geometries from the database, which are connected to
        given attachable. The results are tuples that contain:
        - primary key of the geometry
        - short name used by the attachable
        - full identifier and a path to the geometry file separated with new
          line character.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, identifier || '\n' || path FROM (
            SELECT
                Geometry_pk AS pk,
                AttachableGeometryField.shortName AS shortName,
                AttachableGeometryField.identifier AS identifier,
                GeometryFile.path AS path
            FROM
                AttachableGeometryField
            JOIN Geometry
                ON AttachableGeometryField.identifier = Geometry.identifier
            JOIN GeometryFile
                ON Geometry.GeometryFile_fk = GeometryFile_pk
            WHERE
                AttachableGeometryField.Attachable_fk == ?
            ORDER BY
                Geometry_pk DESC
        )
        GROUP BY
            shortName,
            identifier;
        '''
        return [
            (str(geometry_pk), str(short_name), str(identifier))
            for geometry_pk, short_name, identifier in
            self.db.connection.execute(query, (attachable_pk,))
        ]

    @cache
    def gui_enum_entity_textures(
            self, rc_pk: int, entity_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the textures from the database, which are connected to the
        given render controller and entity. The results are tuples that
        contain:
        - primary key of texture file
        - short name used by RC and entity
        - full path to the texture file

        The texture file might not exist, in this case the primary key is
        based on a pattern: not_found_<number>.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, path FROM (
            SELECT
                TextureFile_pk AS pk,
                RenderControllerTexturesField.shortName AS shortName,
                TextureFile.path AS path,
                ClientEntityTextureField.identifier AS identifier
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
                AND ClientEntity_pk == ?
            ORDER BY
                TextureFile_pk DESC
        )
        GROUP BY
            identifier,
            shortName
        ORDER BY
            shortName;
        '''
        result: list[tuple[str, str, str]] = []
        not_found_counter = 0
        for texture_pk, short_name, path in self.db.connection.execute(
                query, (rc_pk, entity_pk)):
            if texture_pk is None:
                texture_pk = f'not_found_{not_found_counter}'
                not_found_counter += 1
                path = "Unknown file path"
            else:
                path = path.as_posix()
            result.append(
                (str(texture_pk), str(short_name), path)
            )
        return result

    @cache
    def gui_enum_attachable_textures(
            self, rc_pk: int, attachable_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the textures from the database, which are connected to the
        given render controller and attachable. The results are tuples that
        contain:
        - primary key of texture file
        - short name used by RC and attachable
        - full path to the texture file

        The texture file might not exist, in this case the primary key is
        based on a pattern: not_found_<number>.

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, path FROM (
            SELECT
                TextureFile_pk AS pk,
                RenderControllerTexturesField.shortName AS shortName,
                TextureFile.path AS path,
                AttachableTextureField.identifier AS identifier
            FROM
                Attachable
            JOIN AttachableRenderControllerField
                ON AttachableRenderControllerField.Attachable_fk = Attachable_pk
            JOIN AttachableTextureField
                ON AttachableTextureField.Attachable_fk = Attachable_pk
            JOIN RenderController
                ON AttachableRenderControllerField.identifier = RenderController.identifier
            JOIN RenderControllerTexturesField
                ON RenderControllerTexturesField.RenderController_fk = RenderController_pk
            LEFT OUTER JOIN TextureFile
                ON AttachableTextureField.identifier = TextureFile.identifier
            WHERE
                AttachableTextureField.shortName == RenderControllerTexturesField.shortName
                AND RenderController_pk == ?
                AND Attachable_pk == ?
            ORDER BY
                TextureFile_pk DESC
        )
        GROUP BY
            identifier,
            shortName
        ORDER BY
            shortName;
        '''
        result: list[tuple[str, str, str]] = []
        not_found_counter = 0
        for texture_pk, short_name, path in self.db.connection.execute(
                query, (rc_pk, attachable_pk)):

            if texture_pk is None:
                texture_pk = f'not_found_{not_found_counter}'
                not_found_counter += 1
                path = "Unknown file path"
            else:
                path = path.as_posix()

            result.append(
                (str(texture_pk), str(short_name), path)
            )
        return result

    @cache
    def gui_enum_entity_textures_for_fake_rc(
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
        SELECT pk, shortName, path FROM (
            SELECT
                TextureFile_pk AS pk,
                ClientEntityTextureField.shortName AS shortName,
                TextureFile.path AS path,
                ClientEntityTextureField.identifier AS identifier
            FROM
                ClientEntity
            JOIN ClientEntityTextureField
                ON ClientEntityTextureField.ClientEntity_fk = ClientEntity_pk
            LEFT OUTER JOIN TextureFile
                ON ClientEntityTextureField.identifier = TextureFile.identifier
            WHERE
                ClientEntity_pk == ?
            ORDER BY
                TextureFile_pk DESC
        )
        GROUP BY
            identifier,
            shortName;
        '''
        return [
            (
                "-1" if texture_pk is None else str(texture_pk),
                str(short_name),
                path.as_posix()
            )
            for texture_pk, short_name, path in
            self.db.connection.execute(query, (entity_pk,))
        ]

    @cache
    def gui_enum_attachable_textures_for_fake_rc(
            self, attachable_pk: int) -> list[tuple[str, str, str]]:
        '''
        Lists all of the textures from the database, which are connected to the
        given attachable. The results are tuples that contain:
        - primary key of texture file
        - short name used by attachable
        - full path to the texture file

        The texture file might not exist, in this case the primary key is
        "-1".

        The values are cached and prepared to be used as an enum property in
        GUI.
        '''
        query = '''
        SELECT pk, shortName, path FROM (
            SELECT
                TextureFile_pk AS pk,
                AttachableTextureField.shortName AS shortName,
                TextureFile.path AS path,
                AttachableTextureField.identifier AS identifier
            FROM
                Attachable
            JOIN AttachableTextureField
                ON AttachableTextureField.Attachable_fk = Attachable_pk
            LEFT OUTER JOIN TextureFile
                ON AttachableTextureField.identifier = TextureFile.identifier
            WHERE
                Attachable_pk == ?
            ORDER BY
                TextureFile_pk DESC
        )
        GROUP BY
            identifier,
            shortName;
        '''
        return [
            (
                "-1" if texture_pk is None else str(texture_pk),
                str(short_name),
                path.as_posix()
            )
            for texture_pk, short_name, path in
            self.db.connection.execute(query, (attachable_pk,))
        ]

    @cache
    def list_entity_render_controllers(
            self, entity_pk: int) -> list[tuple[Optional[int], str]]:
        '''
        Lists all of the render controllers from the database, which are
        connected to the given entity. The results are tuples that contain:
        - primary key of render controller
        - full identifier of render controller

        The primary key of the render controller can be None, if the render
        controller is not defined in the database.
        If the render controllers have duplicated identifiers, the last one is
        used (this means that if there is multiple resource packs, the pack
        loaded last will be used). If a pack has multiple render controllers
        with the same identifier (which is not allowed), the last one is used.
        '''
        # pylint: disable=unnecessary-comprehension
        query = '''
        SELECT pk, identifier FROM (
            SELECT DISTINCT
                RenderController_pk AS pk,
                ClientEntityRenderControllerField.identifier AS identifier,
                ClientEntityRenderControllerField_pk AS field_pk
            FROM
                ClientEntity
            JOIN ClientEntityRenderControllerField
                ON ClientEntityRenderControllerField.ClientEntity_fk = ClientEntity_pk
            LEFT OUTER JOIN RenderController
                ON ClientEntityRenderControllerField.identifier = RenderController.identifier
            WHERE
                ClientEntity_pk == ?
            ORDER BY
                RenderController_pk DESC
        )
        GROUP BY
            identifier,
            field_pk;
        '''
        # field_pk is for a rare case when the entity uses the same render
        # controller twice
        return [
            (rc_pk, identifier)
            for rc_pk, identifier in
            self.db.connection.execute(query, (entity_pk,))
        ]

    @cache
    def list_attachable_render_controllers(
            self, attachable_pk: int) -> list[tuple[Optional[int], str]]:
        '''
        Lists all of the render controllers from the database, which are
        connected to the given attachable. The results are tuples that contain:
        - primary key of render controller
        - full identifier of render controller

        The primary key of the render controller can be None, if the render
        controller is not defined in the database.
        If the render controllers have duplicated identifiers, the last one is
        used (this means that if there is multiple resource packs, the pack
        loaded last will be used). If a pack has multiple render controllers
        with the same identifier (which is not allowed), the last one is used.
        '''
        # pylint: disable=unnecessary-comprehension
        query = '''
        SELECT pk, identifier FROM (
            SELECT DISTINCT
                RenderController_pk AS pk,
                AttachableRenderControllerField.identifier AS identifier,
                AttachableRenderControllerField_pk AS field_pk
            FROM
                Attachable
            JOIN AttachableRenderControllerField
                ON AttachableRenderControllerField.Attachable_fk = Attachable_pk
            LEFT OUTER JOIN RenderController
                ON AttachableRenderControllerField.identifier = RenderController.identifier
            WHERE
                Attachable_pk == ?
            ORDER BY
                RenderController_pk DESC
        )
        GROUP BY
            identifier,
            field_pk;
        '''
        # field_pk is for a rare case when the attachable uses the same render
        # controller twice
        return [
            (rc_pk, identifier)
            for rc_pk, identifier in
            self.db.connection.execute(query, (attachable_pk,))
        ]

    @cache
    def list_bone_name_patterns(self, render_controller_pk: int) -> list[str]:
        '''
        Lists all of the distinct bone name patterns from the given
        render controller. The result is a string with the bone name pattern.
        '''
        # pylint: disable=unnecessary-comprehension
        query = '''
        SELECT DISTINCT boneNamePattern
        FROM RenderControllerMaterialsField
        WHERE RenderController_fk = ?;
        '''
        return [
            bone_name_pattern
            for bone_name_pattern, in
            self.db.connection.execute(query, (render_controller_pk,))
        ]

    @cache
    def list_entities_with_models_and_rc(self) -> list[tuple[int, str]]:
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
        # pylint: disable=unnecessary-comprehension

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
            self.db.connection.execute(query)
        ]

    @cache
    def list_attachables_with_models_and_rc(self) -> list[tuple[int, str]]:
        '''
        Lists all of the all of the  attachables from database that use
        geometries and render_controlelrs fields. There must be at least one
        geometry in the database that connects to the geometry field. The
        render controller don't have to exist but there must be a render
        controller field in the attachable file.

        The results are tuples that contain:

        - primary key of the attachable
        - identifier of the attachable

        Results are ordered by identifier
        '''
        # pylint: disable=unnecessary-comprehension

        # DISTINCT in SELECT is needed, because there can be multiple geometry
        # or rc fields in one attachable
        query = '''
        SELECT DISTINCT
            Attachable_pk, Attachable.identifier
        FROM
            Attachable
        JOIN AttachableGeometryField
            ON AttachableGeometryField.Attachable_fk = Attachable_pk
        JOIN AttachableRenderControllerField
            ON AttachableRenderControllerField.Attachable_fk = Attachable_pk
        JOIN  -- Geometry file must exist
            Geometry
            ON Geometry.identifier = AttachableGeometryField.identifier
        ORDER BY Attachable.identifier;
        '''
        return [
            (entity_pk, identifier)
            for entity_pk, identifier in
            self.db.connection.execute(query)
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
        return self.db.connection.execute(query, (texture_file_pk,)).fetchone()[0]

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
        return tuple(  # type: ignore
            self.db.connection.execute(query, (geometry_pk,)
        ).fetchone())

    def get_entity_material_pattern_and_material(
            self, entity_pk: int, rc_material_field_pk: int) -> tuple[str, str]:
        '''
        Returns tuple with the material pattern and full material identifier
        based on matching entity and render controller material field primary
        keys from the database.
        '''
        # The rc_material_field_pk also unambiguously identifies the render
        # controller
        query = '''
        SELECT DISTINCT
            RenderControllerMaterialsField.boneNamePattern,
            ClientEntityMaterialField.identifier
        FROM
            RenderControllerMaterialsField
        JOIN ClientEntityMaterialField
            ON ClientEntityMaterialField.shortName = RenderControllerMaterialsField.shortName
        WHERE
            ClientEntityMaterialField.ClientEntity_fk = ?
            AND RenderControllerMaterialsField_pk = ?;
        '''
        return tuple(self.db.connection.execute(  # type: ignore
            query,
            (entity_pk, rc_material_field_pk)).fetchone()
        )

    def get_attachable_material_pattern_and_material(
            self, attachable_pk: int, rc_material_field_pk: int) -> tuple[str, str]:
        '''
        Returns tuple with the material pattern and full material identifier
        based on matching attachable and render controller material field primary
        keys from the database.
        '''
        # The rc_material_field_pk also unambiguously identifies the render
        # controller
        query = '''
        SELECT DISTINCT
            RenderControllerMaterialsField.boneNamePattern,
            AttachableMaterialField.identifier
        FROM
            RenderControllerMaterialsField
        JOIN AttachableMaterialField
            ON AttachableMaterialField.shortName = RenderControllerMaterialsField.shortName
        WHERE
            AttachableMaterialField.Attachable_fk = ?
            AND RenderControllerMaterialsField_pk = ?;
        '''
        return tuple(self.db.connection.execute(  # type: ignore
            query,
            (attachable_pk, rc_material_field_pk)).fetchone()
        )

    def get_full_material_identifier(self, material_field_pk: int) -> str:
        '''
        Returns the full material identifier based on the material field
        primary key from the database.
        '''
        query = '''
        SELECT
            ClientEntityMaterialField.identifier
        FROM
            ClientEntityMaterialField
        WHERE
            ClientEntityMaterialField_pk = ?;
        '''
        return self.db.connection.execute(query, (material_field_pk,)).fetchone()[0]
