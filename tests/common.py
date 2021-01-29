'''
Common functions for tests.

This module uses additional file called config.py (located in the tests/
directory) which defines th BLENDER_EXEC_PATH - a string with a path to the
blender executable.

If BLENDER_EXEC_PATH is not specified the test script tries to run blender with
`blender` command.

The config.py file is blacklisted in .gitignore because it can be different on
different devices.
'''
import os
import json
from typing import Optional, Tuple, Dict, Any, Set
from pathlib import Path

import subprocess
try:
    from .config import BLENDER_EXEC_PATH
except:
    BLENDER_EXEC_PATH = 'blender'


def blender_run_script(
        script, *args, blend_file_path: Optional[str] = None
    ):
    '''
    Run blender script with *args arguments. You can pass optional argument
    blend_file_path if the scrupt should be executed in certain file path.
    '''
    if not blend_file_path:
        command = [BLENDER_EXEC_PATH, '-b', '--python', script, '--', *args]
    else:
        command = [
            BLENDER_EXEC_PATH, blend_file_path, '-b', '--python', script, '--',
            *args
        ]
    subprocess.call(command)

def assert_is_vector(vect: Any, length: int, types: Tuple):
    assert isinstance(vect, list)
    assert len(vect) == length
    assert all([isinstance(i, types) for i in vect])

def assert_is_model(a: Dict):
    '''Check if the input is a valid model'''
    assert type(a) is dict
    assert set(a.keys()) == {'format_version', 'minecraft:geometry'}

    assert a['format_version'] == "1.12.0"

    geometries = a['minecraft:geometry']
    assert type(geometries) is list
    assert len(geometries) > 0
    
    # minecraft:geometry
    for geometry in geometries:
        assert type(geometry) is dict
        assert set(geometry.keys()) == {'description', 'bones'}
        desc = geometry['description']
        bones = geometry['bones']

        # minecraft:geometry -> description
        assert type(desc) is dict
        assert set(desc.keys()) == {
            'identifier', 'texture_width',
            'texture_height', 'visible_bounds_width', 'visible_bounds_height',
            'visible_bounds_offset'
        }
        assert type(desc['identifier']) is str
        assert type(desc['texture_width']) is int
        assert type(desc['texture_height']) is int
        assert isinstance(desc['visible_bounds_width'], (float, int))
        assert isinstance(desc['visible_bounds_height'], (float, int))
        assert_is_vector(desc['visible_bounds_offset'], 3, (int, float))

        # minecraft:geometry -> bones
        assert type(bones) is list
        for bone in bones:
            assert type(bone) is dict

            assert set(bone.keys()) <= {  # acceptable keys
                'name', 'cubes', 'pivot', 'rotation', 'parent', 'locators',
                'poly_mesh'
            }
            assert set(bone.keys()) >= {  # obligatory keys
                'name', 'pivot', 'rotation'
            }
            assert type(bone['name']) is str

            assert_is_vector(bone['pivot'], 3, (int, float))
            assert_is_vector(bone['rotation'], 3, (int, float))
            if 'parent' in bone:
                assert type(bone['parent']) is str
            # minecraft:geometry -> bones -> locators
            if 'locators' in bone:
                assert type(bone['locators']) is dict
                for locator_name, locator in bone['locators'].items():
                    assert type(locator_name) is str
                    assert_is_vector(locator, 3, (int, float))
            # minecraft:geometry -> bones -> cubes
            if 'cubes' in bone:
                assert type(bone['cubes']) is list
                for cube in bone['cubes']:
                    assert type(cube) is dict
                    assert set(cube.keys()) <= {  # acceptable keys
                        'uv', 'size', 'origin', 'pivot', 'rotation',
                        'mirror'
                    }
                    assert set(cube.keys()) >= {  # obligatory keys
                        'uv', 'size', 'origin', 'pivot', 'rotation'
                    }
                    if isinstance(cube['uv'], list):  # Standard MC uv
                        assert_is_vector(cube['uv'], 2, (int, float))
                    elif isinstance(cube['uv'], dict):  # Per face UV mapping
                        assert set(cube['uv'].keys()) <= {  # acceptable keys
                            'north', 'south', 'east', 'west', 'up', 'down'}
                        for uv_face in cube['uv'].values():
                            assert set(uv_face.keys()) <= {'uv', 'uv_size'}  # acceptable keys
                            assert set(uv_face.keys()) >= {'uv'}  # obligatory keys
                            assert_is_vector(uv_face['uv'], 2, (float, int))
                            if 'uv_size' in uv_face:
                                assert_is_vector(
                                    uv_face['uv_size'], 2, (float, int))
                    assert_is_vector(cube['size'], 3, (int, float))
                    assert_is_vector(cube['origin'], 3, (int, float))
                    assert_is_vector(cube['pivot'], 3, (int, float))
                    assert_is_vector(cube['rotation'], 3, (int, float))
                    if 'mirror' in cube:
                        assert type(cube['mirror']) is bool
            # minecraft:geometry -> bones -> poly_mesh
            if 'poly_mesh' in bone:
                poly_mesh = bone['poly_mesh']
                assert isinstance(poly_mesh, dict)
                assert set(poly_mesh.keys()) <= {  # acceptable keys
                    'positions','normals','uvs','polys', 'normalized_uvs'}
                assert set(poly_mesh.keys()) >= {  # obligatory keys
                    'polys'}
                if 'positions' in poly_mesh:
                    assert isinstance(poly_mesh['positions'], list)
                    for position in poly_mesh['positions']:
                        assert_is_vector(position, 3, (int, float))
                if 'normals' in poly_mesh:
                    assert isinstance(poly_mesh['normals'], list)
                    for normal in poly_mesh['normals']:
                        assert_is_vector(normal, 3, (int, float))
                if 'uvs' in poly_mesh:
                    assert isinstance(poly_mesh['uvs'], list)
                    for uv in poly_mesh['uvs']:
                        assert_is_vector(uv, 2, (int, float))
                assert isinstance(poly_mesh['polys'], list)
                for poly in poly_mesh['polys']:
                    assert isinstance(poly, list)
                    assert 3 <= len(poly) <= 4
                    for poly_item in poly:
                        assert_is_vector(poly_item, 3, (int, float))
                if 'normalized_uvs' in poly_mesh:
                    assert isinstance(poly_mesh['normalized_uvs'], bool)

def make_comparable_json(
        jsonable: Any, set_paths: Set[Tuple], curr_path=None):
    '''
    Replaces some of the lists in JSON with frozen sets so the objects can
    be safely compared and the order doesn't matter. Dictionaries are replaced
    with tuples of key value pairs because dictionaries are mutable and can't
    be part of a frozenset.
    '''
    if curr_path is None:
        curr_path = []

    if isinstance(jsonable, dict):
        result = [
            (k, make_comparable_json(v, set_paths, curr_path+[k]))
            for k, v in jsonable.items()]
        return frozenset(result)
    if isinstance(jsonable, list):
        result = [
            make_comparable_json(i, set_paths, curr_path+[0])
            for i in jsonable]
        if tuple(curr_path) in set_paths:
            return frozenset(result)
        return tuple(result)
    if isinstance(jsonable, (type(None), bool, int, float, str)):
        return jsonable

def run_import_export_comparison(
        source: str, tmp: str, use_empties: bool
    ) -> Tuple[Dict, Dict, str]:
    '''
    Loads model from source to blender using nusiq_mcblend_import_operator
    Exports this model to tmp (to a file with the same name as source file).

    Returns two dictionaries and a string:
    - the original model
    - the exported model.
    - path to exported model temporary file
    '''
    source = os.path.abspath(source)
    tmp = os.path.abspath(tmp)
    target = os.path.join(tmp, os.path.split(source)[1])
    script = os.path.abspath('./blender_scripts/import_export.py')

    # Windows uses wierd path separators
    source = source.replace('\\', '/')
    tmp = tmp.replace('\\', '/')
    target = target.replace('\\', '/')
    script = script.replace('\\', '/')


    # Create tmp if not exists
    Path(tmp).mkdir(parents=True, exist_ok=True)

    # Run blender actions
    if use_empties:
        blender_run_script(script, source, target, "use_empties")
    else:
        blender_run_script(script, source, target)

    # Validate results
    with open(source, 'r') as f:
        source_dict = json.load(f)
    with open(target, 'r') as f:
        target_dict = json.load(f)

    return (
        source_dict,
        target_dict,
        target
    )
