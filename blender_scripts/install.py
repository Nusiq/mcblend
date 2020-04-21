'''
Installs mcblend from a zip path.

This script is used in github actions.
'''

import sys
import bpy


# Collect arguments after "--"
argv = sys.argv
argv = argv[argv.index("--") + 1:]

def main(zip_path):
    '''
    - zip_path - absolute path to zip file with mcblend.
    '''
    print(f'Installing the addon from {zip_path}')
    bpy.ops.preferences.addon_install(filepath=zip_path)

    print(f'Enabling module "mcblend"')
    bpy.ops.preferences.addon_enable(module="mcblend")
    bpy.ops.wm.save_userpref()

if __name__ == "__main__":
    main(argv[0])
