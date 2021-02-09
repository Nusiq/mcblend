'''
Import model from source_path and export it to target_path.

This script is used for testing the import and export operators.
'''
import sys
import bpy


# Collect arguments after "--"
argv = sys.argv
argv = argv[argv.index("--") + 1:]


def main(source_path: str, target_path: str):
    # Remove all starting objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Load model from source file
    bpy.ops.nusiq_mcblend.import_model(
        filepath=source_path,
        replace_bones_with_empties="use_empties" in argv)

    # Save model to target file
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.nusiq_mcblend.export_model(filepath=target_path)


if __name__ == "__main__":
    main(argv[0], argv[1])
