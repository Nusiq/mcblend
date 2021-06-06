'''
Import UV-group from source_path and export it to target_path.

This script is used for testing the import and export UV-group operators.
'''
import sys
import bpy


# Collect arguments after "--"
argv = sys.argv
argv = argv[argv.index("--") + 1:]


def main(source_path: str, target_path: str):
    # Load model from source file
    bpy.ops.nusiq_mcblend.import_uv_group(
        filepath=source_path)
    # Save model to target file
    bpy.ops.nusiq_mcblend.export_uv_group(
        filepath=target_path)

if __name__ == "__main__":
    main(argv[0], argv[1])
