'''
This is a testing script for model importer. Imports file, exports imported
content and than compares the exported file with the original.
'''
import os
import json
from pathlib import Path
from typing import Dict, Tuple
import shutil

import pytest
from .common import assert_is_model, blender_run_script, make_comparable_json

OUTPUT = "./.tmp/test_importer"

def make_comparison_files(
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

# PYTEST FUNCTIONS
MODEL_FILES = [
    # Import empties
    ("cube_translated.geo.json", True),
    ("cube_with_offset_pivot.geo.json", True),
    ("cube.geo.json", True),
    ("single_bone_rotated_x.geo.json", True),
    ("single_bone_rotated_xyz.geo.json", True),
    ("single_bone_rotated_y.geo.json", True),
    ("single_bone_rotated_z.geo.json", True),
    ("single_bone_translated.geo.json", True),
    ("single_bone.geo.json", True),
    ("three_bones_rotated_x.geo.json", True),
    ("three_bones.geo.json", True),
    ("two_bones.geo.json", True),
    ("battle_mech.geo.json", True),

    # Import bones
    ("cube_translated.geo.json", True),
    ("cube_with_offset_pivot.geo.json", True),
    ("cube.geo.json", True),
    # ("single_bone_rotated_x.geo.json", True),  # Single bones not supported by export
    # ("single_bone_rotated_xyz.geo.json", True),
    # ("single_bone_rotated_y.geo.json", True),
    # ("single_bone_rotated_z.geo.json", True),
    # ("single_bone_translated.geo.json", True),
    ("single_bone.geo.json", True),
    ("three_bones_rotated_x.geo.json", True),
    ("three_bones.geo.json", True),
    ("two_bones.geo.json", True),
    ("battle_mech.geo.json", True),

    # Polymesh
    ('flat_monkey_smooth_monkey.geo.json', True),
    ('flat_monkey_smooth_monkey.geo.json', False),
]


def setup_module(module):
    '''Runs before tests'''
    tmp_path = OUTPUT
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


@pytest.fixture(params=MODEL_FILES)
def import_properties(request):
    return request.param


# TESTS
def test_importer(import_properties):
    model_file = os.path.join('./tests/data/test_importer/models/', import_properties[0])
    use_empties = import_properties[1]

    source_dict, target_dict, target = make_comparison_files(
        model_file, OUTPUT, use_empties
    )

    print(target)
    assert_is_model(target_dict)
    set_paths = {
        ("minecraft:geometry"),
        ("minecraft:geometry", 0, "bones"),
        ("minecraft:geometry", 0, "bones", 0, "cubes"),
    }
    source_comparable = make_comparable_json(source_dict, set_paths)
    target_comparable = make_comparable_json(target_dict, set_paths)

    assert source_comparable == target_comparable
