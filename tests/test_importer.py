'''
This is a testing script fomr model importer.
'''
import os
import subprocess
import json
from pathlib import Path
import typing as tp
import pytest
import shutil
from .common import assert_is_model, blender_run_script


def make_comparison_files(
    source: str, tmp: str
) -> tp.Tuple[tp.Dict, tp.Dict, str]:
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
    '''Runs before tests'''
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
        model_file, "./.tmp/test_importer"
    )

    assert_is_model(target_dict)
    assert source_dict == target_dict
