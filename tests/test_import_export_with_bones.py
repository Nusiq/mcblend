'''
This is a testing script for model importer. Imports file, exports imported
content and than compares the exported file with the original.
'''
import os
import shutil

import pytest
from .common import (
    assert_is_model, compare_json_files, run_import_export_comparison)

OUTPUT = "./.tmp/test_import_with_bones"

MODEL_FILES = [
    # Import bones
    "cube_translated.geo.json",
    "cube_with_offset_pivot.geo.json",
    "cube.geo.json",
    "per_face_uv.geo.json",
    # "single_bone_rotated_x.geo.json",  # Single bones not supported by export
    # "single_bone_rotated_xyz.geo.json",
    # "single_bone_rotated_y.geo.json",
    # "single_bone_rotated_z.geo.json",
    # "single_bone_translated.geo.json",
    # "single_bone.geo.json",
    "three_bones_rotated_x.geo.json",
    "three_bones.geo.json",
    "two_bones.geo.json",
    "battle_mech.geo.json",
    "rotated_locators.geo.json",
    'flat_monkey_smooth_monkey.geo.json',
    "binding_test.geo.json",
]


def setup_module(module):
    '''Runs before tests'''
    tmp_path = OUTPUT
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


# TESTS
@pytest.fixture(params=MODEL_FILES)
def model_files_properties(request):
    return request.param

def test_bones_importer(model_files_properties):
    model_file = os.path.join(
        './tests/data/test_importer/models/', model_files_properties)

    source_dict, target_dict, target = run_import_export_comparison(
        model_file, OUTPUT)

    print(target)
    assert_is_model(target_dict)
    set_paths = {
        ("minecraft:geometry"),
        ("minecraft:geometry", int, "bones"),
        ("minecraft:geometry", int, "bones", int, "cubes"),
    }
    compare_json_files(
        source_dict, target_dict, atol=0.01,
        ignore_order_paths=set_paths)
