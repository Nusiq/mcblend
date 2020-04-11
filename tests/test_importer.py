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

# test_config file is lsited in .gitignore it should have only one variable
# called BLENDER_EXEC_PATH with absolute path of the blender executable file.
from .test_config import BLENDER_EXEC_PATH


def _get_models_to_compare(
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

    # Remove file target file if exists
    try:
        os.remove(target_path)
    except OSError:
        pass

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

# THE TESTS
def test_importer():
    models_path = "./tests/data/test_importer/models/"
    for dir_ in os.listdir(models_path):
        fp = os.path.join(models_path, dir_)
        if not os.path.isfile(fp):
            continue
        source_dict, target_dict, target_path = _get_models_to_compare(
            BLENDER_EXEC_PATH,
            fp, "./.tmp/test_importer"
        )
        print(dir_)
        assert (
            source_dict["minecraft:geometry"][0]['bones'] ==
            target_dict["minecraft:geometry"][0]['bones']
        )
