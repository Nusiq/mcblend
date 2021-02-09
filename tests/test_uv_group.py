'''
This is a testing script for UV-group importer and exporter.

It imports UV-group, exports it and compares if the result is the same as
the original.
'''
# pylint: disable=missing-docstring
import os
import json
from pathlib import Path
import typing as tp
import shutil

import pytest
from .common import blender_run_script, compare_json_files

OUTPUT = "./.tmp/test_uv_group"

def make_comparison_files(
        source: str, tmp: str) -> tp.Tuple[tp.Dict, tp.Dict, str]:
    '''
    Loads UV-group from JSON to Blender using
    nusiq_mcblend_import_uv_group. Exports this model to tmp
    (to a file with the same name as source file).

    Returns two dictionaries:
    - the original UV-group
    - the exported UV-group
    '''
    source = os.path.abspath(source)
    tmp = os.path.abspath(tmp)
    target = os.path.join(tmp, os.path.split(source)[1])
    script = os.path.abspath('./blender_scripts/import_export_uv_group.py')

    # Windows uses weird path separators
    source = source.replace('\\', '/')
    tmp = tmp.replace('\\', '/')
    target = target.replace('\\', '/')
    script = script.replace('\\', '/')


    # Create tmp if not exists
    Path(tmp).mkdir(parents=True, exist_ok=True)

    # Run blender actions
    blender_run_script(script, source, target)

    # Get the results
    with open(source, 'r') as f:
        source_dict = json.load(f)
    with open(target, 'r') as f:
        target_dict = json.load(f)

    return source_dict, target_dict

# PYTEST FUNCTIONS
UV_GROUP_FILES = [
    # Import empties
    # TODO - The names of the test files here
    "test.uvgroup.json"
]


def setup_module(module):
    '''Runs before tests'''
    # pylint: disable=unused-argument
    tmp_path = OUTPUT
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


@pytest.fixture(params=UV_GROUP_FILES)
def import_properties(request):
    return request.param

# TESTS
def test_importer(import_properties: str):
    # pylint: disable=redefined-outer-name
    model_file = os.path.join(
        './tests/data/test_uv_group/import_export', import_properties)

    source_dict, target_dict = make_comparison_files(
        model_file, OUTPUT
    )
    compare_json_files(source_dict, target_dict, atol=0.01)
