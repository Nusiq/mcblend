'''
Select scene passed in commandline arguments, select all, export animation
to path passed in arguments.

This script should be executed after opening testing file with a model that
have animation.
'''
import sys
import bpy


# Collect arguments after "--"
argv = sys.argv
argv = argv[argv.index("--") + 1:]


def main(scene_name: str, target_path: str):
    '''Main function.'''
    bpy.context.window.scene = bpy.data.scenes[scene_name]
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.nusiq_mcblend.export_animation(filepath=target_path)

if __name__ == "__main__":
    main(argv[0], argv[1])
