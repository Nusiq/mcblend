'''
This is a testing script fomr model importer. It requires additional file
called test_config.json with following structure:
{
    "blender_exec_path": "Absolute/path/to/your/blender.exe"
}
'''
import os
import subprocess
import json
from pathlib import Path
import typing as tp
import pytest
import shutil


# test_config file is lsited in .gitignore it should have only one variable
# called BLENDER_EXEC_PATH with absolute path of the blender executable file.
from .test_config import BLENDER_EXEC_PATH


# HELPER FUNCTIONS
def make_comparison_files(
    blender_exe: str, source_path: str, tmp_path: str
) -> tp.Tuple[tp.Dict, tp.Dict, str]:
    '''
    Loads model from source_path to blender using nusiq_mcblend_import_operator
    Exports this model to tmp_path (to a file with the same name as
    source_path file).

    Returns two dictionaries and a string:
    - the original model
    - the exported model.
    - path to exported model temporary file
    '''
    source_path = os.path.abspath(source_path).replace('\\', '/')
    tmp_path = os.path.abspath(tmp_path).replace('\\', '/')
    target_path = os.path.join(
        tmp_path, os.path.split(source_path)[1]
    ).replace('\\', '/')

    # Create tmp_path if not exists
    Path(tmp_path).mkdir(parents=True, exist_ok=True)

    # Run blender actions
    subprocess.call([
        blender_exe, '-b', '--log-level', '0', '--python-expr',
        # Python commands separated with semicolons
        "import bpy;"
        "bpy.ops.object.select_all(action='SELECT');"
        "bpy.ops.object.delete(use_global=False);"

        f'bpy.ops.object.nusiq_mcblend_import_operator('
        f'filepath="{source_path}");'
        "bpy.ops.object.select_all(action='SELECT');"
        f'bpy.ops.object.nusiq_mcblend_export_operator('
        f'filepath="{target_path}")'
    ])

    # Validate results
    with open(source_path, 'r') as f:
        source_dict = json.load(f)
    with open(target_path, 'r') as f:
        target_dict = json.load(f)

    return (
        source_dict,
        target_dict,
        target_path
    )


def assert_is_vector(vect: tp. Any, length: int, types: tp.Tuple):
    assert type(vect) is list
    assert len(vect) == length
    assert all([isinstance(i, types) for i in vect])


def assert_is_model(a: tp.Dict):
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
        assert set(desc.keys()) == {'identifier', 'texture_width',
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
                'name', 'cubes', 'pivot', 'rotation', 'parent', 'locators'
            }
            assert set(bone.keys()) >= {  # obligatory keys
                'name', 'cubes', 'pivot', 'rotation'
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
                assert_is_vector(cube['uv'], 2, (int, float))
                assert_is_vector(cube['size'], 3, (int, float))
                assert_is_vector(cube['origin'], 3, (int, float))
                assert_is_vector(cube['pivot'], 3, (int, float))
                assert_is_vector(cube['rotation'], 3, (int, float))
                if 'mirror' in cube:
                    assert type(cube['mirror']) is bool


# PYTEST FUNCTIONS
MODEL_FILES = [
    "cube_translated.geo.json",
    "cube_with_offset_pivot.geo.json",
    "cube.geo.json",
    "single_bone_rotated_x.geo.json",
    "single_bone_rotated_xyz.geo.json",
    "single_bone_rotated_y.geo.json",
    "single_bone_rotated_z.geo.json",
    "single_bone_translated.geo.json",
    "single_bone.geo.json",
    "three_bones_rotated_x.geo.json",
    "three_bones.geo.json",
    "two_bones.geo.json",
    "battle_mech.geo.json",
]


def setup_module(module):
    tmp_path = "./.tmp/test_importer"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


@pytest.fixture(params=MODEL_FILES)
def model_file(request):
    return request.param


# TESTS
def test_importer(model_file):
    model_file = os.path.join('./tests/data/test_importer/models/', model_file)

    source_dict, target_dict, target_path = make_comparison_files(
        BLENDER_EXEC_PATH,
        model_file,
        "./.tmp/test_importer"
    )
    assert_is_model(target_dict)

    assert (
        source_dict == target_dict
    )
