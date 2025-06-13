'''
This is a testing script for batch exporting animations. Exports animations
from blend file and compares them with the expected result.
'''
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from .common import blender_run_script

SCRIPT: Path = Path('blender_scripts/batch_export.py').resolve()
TMP: Path = Path('.tmp/test_batch_export').resolve()
DATA_DIR: Path = Path('tests/data/test_batch_export').resolve()
BLEND_PROJECT: Path = Path('tests/data/test_batch_export.blend').resolve()

def _prepare_target_file(source_file: str) -> Path:
    '''Copy base file to TMP'''
    TMP.mkdir(parents=True, exist_ok=True)
    src = DATA_DIR / source_file
    dst = TMP / 'batch_export.animation.json'
    shutil.copyfile(src, dst)
    return dst


def _run_blender(scene: str, target: Path) -> None:
    '''Run batch export in privoded scene and save to target file'''
    blender_run_script(
        SCRIPT.as_posix(),
        scene,
        target.as_posix(),
        blend_file_path=BLEND_PROJECT.as_posix(),
    )

def setup_module(module):  # pylint: disable=unused-argument
    '''Remove TMP before running the test-suite.'''
    if TMP.exists():
        shutil.rmtree(TMP)

# PYTEST FUNCTIONS
SCENES = [
    {
        'name': 'batch_export',
        'source': 'base.animation.json',
        'expected': 'result.animation.json',
    },
]

@pytest.fixture(params=SCENES)
def scene(request):  # type: ignore
    return request.param

# TESTS
def test_batch_export(scene):
    '''End-to-end validation of batch animation export.'''
    target_path = _prepare_target_file(scene['source'])
    _run_blender(scene['name'], target_path)

    expected_path = DATA_DIR / scene['expected']

    with target_path.open('r', encoding='utf8') as f:
        result_dict = json.load(f)
    with expected_path.open('r', encoding='utf8') as f:
        expected_dict = json.load(f)

    assert result_dict == expected_dict
