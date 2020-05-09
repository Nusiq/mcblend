'''
This is a testing script for exporting animations.
'''
import os
import shutil
import json
from pathlib import Path
import typing as tp

import pytest
from .common import assert_is_model, blender_run_script


def make_comparison_files(
        tmp: str, scene_name: str, blend_file_path: str,
    ) -> tp.Tuple[tp.Dict, str]:
    '''
    Opens blender file, selects_scene and exports animation from that to
    given tmp path.

    Returns the result JSON in a dictionary and the path to newly created file.
    '''
    tmp = os.path.abspath(tmp)
    target = os.path.join(tmp, f'{scene_name}.animation.json')
    expected_result_path = (
        f'./tests/data/test_animation_export/{scene_name}.animation.json'
    )

    script = os.path.abspath('./blender_scripts/export_animation.py')
    blend_file_path = os.path.abspath(blend_file_path)

    # Windows uses wierd path separators
    tmp = tmp.replace('\\', '/')
    target = target.replace('\\', '/')
    script = script.replace('\\', '/')


    # Create tmp if not exists
    Path(tmp).mkdir(parents=True, exist_ok=True)

    # Run blender actions
    blender_run_script(
        script, scene_name, target, blend_file_path=blend_file_path
    )

    # Return results
    with open(target, 'r') as f:
        target_dict = json.load(f)
    with open(expected_result_path, 'r') as f:
        expected_result = json.load(f)

    return target_dict, target, expected_result  # type: ignore

# PYTEST FUNCTIONS
SCENES = [
    'ObjectAnimation', 'ArmatureAnimation', 'BattleMech'
]


def setup_module(module):
    '''Runs before tests'''
    tmp_path = "./.tmp/test_animation_export"
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


@pytest.fixture(params=SCENES)
def scene(request):
    return request.param


# TESTS
def test_importer(scene):
    result_dict, result_path, expected_result = make_comparison_files(
        "./.tmp/test_animation_export", scene,
        './tests/data/tests_project.blend'
    )

    assert result_dict == expected_result
