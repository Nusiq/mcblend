'''
This is a testing script for exporting animations. Exports animations from
blend file and compares them with the expected result.
'''
import os
import shutil
import json
from pathlib import Path
import typing as tp

import pytest
from .common import blender_run_script

SCRIPT = Path('blender_scripts/export_animation.py').resolve()
TMP=Path(".tmp/test_animation_export").resolve()
EXAMPLES = Path(f'tests/data/test_animation_export').resolve()
BLEND_PROJECT = Path('tests/data/tests_project.blend').resolve()

def make_comparison_files(scene: str) -> tp.Tuple[tp.Dict, str]:
    '''
    Opens blender file, selects_scene and exports animation from that to
    given tmp path.

    Returns the result JSON in a dictionary and the path to newly created file.
    '''
    TMP.mkdir(parents=True, exist_ok=True)
    output = TMP / f'{scene}.animation.json'
    expected = EXAMPLES / f'{scene}.animation.json'

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
    # 'armature_transformation_test',  # TODO - investigate unexpected results

    'ArmatureAnimation',

    # Exactly the same as 'ArmatureAnimation' but with different name, the
    # ArmatureAnimation_ArmatureOrigin scene uses transformed armature and
    # ARMATURE origin mode (so result should be the same).
    'ArmatureAnimation_ArmatureOrigin',

    'animation_interpolation'
]

def setup_module(module):
    '''Runs before tests'''
    if TMP.exists():
        shutil.rmtree(TMP)

@pytest.fixture(params=SCENES)
def scene(request):
    return request.param

# TESTS
def test_animation_export(scene):
    result_dict, expected_result = make_comparison_files(scene)
    assert result_dict == expected_result
