'''
Functions related to imoporting models from resource packs.
'''
from __future__ import annotations
import bpy_types
from typing import TypedDict, TYPE_CHECKING, cast


if TYPE_CHECKING:
    from ..resource_pack_data import MCBLEND_ProjectProperties
else:
    MCBLEND_ProjectProperties = None
    MCBLEND_ObjectProperties = None

class PksForEntityImport(TypedDict):
    '''
    A collection of all primary keys needed for database queries used to
    import an entity from a resource pack.

    The key names are the same as the names of the database tables.
    '''
    ClientEntity_pk: int
    render_controllers: list[PksForEntityRc]

class PksForEntityRc(TypedDict):
    '''
    Primary keys of one of the render controllers of an entity. Part of the
    EntityImportPks.

    The key names are the same as the names of the database tables.
    '''
    RenderController_pk: int
    TextureFile_pk: int
    Geometry_pk: int
    ClientEntityMaterialField_pk: int
    RenderControllerMaterialsField_pks: list[int]

def get_pks_for_entity_improt(
        context: bpy_types.Context) -> PksForEntityImport:
    '''
    Creates a dictionary of primary keys needed to import an entity from a
    resource pack based on the settings selected in the UI.
    '''
    # 1. Load cached data
    project = context.scene.mcblend_project
    project = cast(MCBLEND_ProjectProperties, project)

    entity_pk = project.entities[
        project.selected_entity].primary_key

    # 2. Build a dictionary with PKs of all of the queries needed to load the
    # data about the model
    query_data: PksForEntityImport = {}
    # Load client entity PK
    query_data['ClientEntity_pk'] = entity_pk
    query_data['render_controllers'] = []
    # Load all render controllers PKs
    for render_controller in project.entity_render_controllers:
        # Load render controller PK
        rc_pk = render_controller.primary_key
        query_data_rc = {}
        query_data['render_controllers'].append(query_data_rc)
        query_data_rc['RenderController_pk'] = rc_pk

        # Load texture PK
        try:
            texture_file_pk = int(render_controller.textures)
        except ValueError:
            texture_file_pk = -1
        query_data_rc['TextureFile_pk'] = texture_file_pk

        # Load geometry PK
        geo_pk = int(render_controller.geometries)
        query_data_rc['Geometry_pk'] = geo_pk

        # Load all materials PKs
        query_data_rc_materials = []
        query_data_rc['RenderControllerMaterialsField_pks'] = query_data_rc_materials
        query_data_rc['ClientEntityMaterialField_pk'] = -1
        if len(render_controller.material_patterns) > 0:
            # Materials loaded from render controller
            for material_pattern_obj in render_controller.material_patterns:
                rc_material_field_pk = int(material_pattern_obj.materials)
                query_data_rc_materials.append(rc_material_field_pk)
        else:
            # Materials loaded from the entity it's a fake render controller
            ce_material_field_pk = int(render_controller.fake_material_patterns)
            query_data_rc['ClientEntityMaterialField_pk'] = ce_material_field_pk
    return query_data
