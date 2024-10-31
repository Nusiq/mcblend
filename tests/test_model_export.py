'''
This is a testing script for exporting models. Exports model from
blend file and compares them with the expected result.
'''
import os
import shutil
import json
from pathlib import Path
import typing as tp

import pytest
from .common import assert_is_model, blender_run_script, compare_json_files


SCRIPT = Path('blender_scripts/export_model.py').resolve()
TMP = Path(".tmp/test_model_export").resolve()
EXAMPLES = Path(f'tests/data/test_model_export').resolve()
BLEND_PROJECT = Path('tests/data/tests_project.blend').resolve()


def make_comparison_files(scene: str) -> tp.Tuple[tp.Dict, tp.Dict]:
    '''
    Opens blender file, selects_scene and exports model from that to
    given tmp path.

    Returns the result JSON in a dictionary and the path to newly created file.
    '''
    TMP.mkdir(parents=True, exist_ok=True)
    output = TMP / f'{scene}.geo.json'
    expected = EXAMPLES / f'{scene}.geo.json'

    # Run blender actions
    blender_run_script(
        SCRIPT.as_posix(), scene, output.as_posix(),
        blend_file_path=BLEND_PROJECT.as_posix()
    )

    # Return results
    with output.open('r') as f:
        output_dict = json.load(f)
    with expected.open('r') as f:
        expected_dict = json.load(f)

    return output_dict, expected_dict  # type: ignore

# PYTEST FUNCTIONS
SCENES = [
    # Incorrect object positioning when parent scale is not 1
    'issue62',

    # This model was exported using 'ArmatureAnimation' scene, but the
    # 'ArmatureAnimation_ArmatureOrigin' scene uses the same model but with
    # armature transormations. The origin mode is set to ARMATURE, so the
    # transformations should be irrelevant.
    'ArmatureAnimation_ArmatureOrigin',

    # Issue 116 - incorrect normals export for polymesh models
    'issue116',
]


def setup_module(module):
    '''Runs before tests'''
    if TMP.exists():
        shutil.rmtree(TMP)


@pytest.fixture(params=SCENES)
def scene(request):
    return request.param


# TESTS
def test_importer(scene):
    result, expected_result = make_comparison_files(scene)

    assert_is_model(result)
    set_paths = {
        ("minecraft:geometry"),
        ("minecraft:geometry", int, "bones"),
        ("minecraft:geometry", int, "bones", int, "cubes"),
        ("minecraft:geometry", int, "bones", int, "cubes", int, "locators"),
    }

    compare_json_files(
        expected_result, result, atol=0.01,
        ignore_order_paths=set_paths)
