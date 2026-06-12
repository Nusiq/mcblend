'''
Testing script for exporting camera animations. Exports camera animation from
blend file and compares with expected result.
'''
import json
import shutil
from pathlib import Path
import typing as tp

import pytest

from .common import blender_run_script, compare_json_files

SCRIPT = Path('blender_scripts/export_camera_animation.py').resolve()
TMP = Path('.tmp/test_camera_export').resolve()
EXAMPLES = Path('tests/data/test_camera_export').resolve()
BLEND_PROJECT = Path('tests/test_camera_export.blend').resolve()


def load_camera_script_json(path: Path) -> tp.Dict:
    with path.open('r', encoding='utf8') as file:
        text = file.read().strip()
    if not text.startswith('export default '):
        raise ValueError(f'Unexpected camera script format in {path}')
    json_text = text.removeprefix('export default ').removesuffix(';').strip()
    return json.loads(json_text)


def make_comparison_files(scene: str, expected_file: str) -> tp.Tuple[tp.Dict, tp.Dict]:
    '''
    Opens blender file, selects scene and exports camera animation to tmp path.

    Returns the exported and expected JSON as dictionaries.
    '''
    TMP.mkdir(parents=True, exist_ok=True)
    output = TMP / expected_file
    expected = EXAMPLES / expected_file

    blender_run_script(
        SCRIPT.as_posix(), scene, output.as_posix(),
        blend_file_path=BLEND_PROJECT.as_posix()
    )

    return (
        load_camera_script_json(output),
        load_camera_script_json(expected),
    )


# Scene name in blend file -> expected output file name in EXAMPLES
SCENE_EXPECTED_FILES = {
    'GimbalLocks': 'gimbal_locks.js',
    'FovAndInterpolation': "fov_and_interpolation.js",
}


def setup_module(module):
    '''Runs before tests'''
    if TMP.exists():
        shutil.rmtree(TMP)


@pytest.fixture(params=list(SCENE_EXPECTED_FILES.items()), ids=lambda item: item[0])
def scene_config(request):
    scene, expected_file = request.param
    return {'scene': scene, 'expected_file': expected_file}


def test_camera_export(scene_config):
    result_dict, expected_dict = make_comparison_files(
        scene_config['scene'], scene_config['expected_file'])
    compare_json_files(expected_dict, result_dict)
