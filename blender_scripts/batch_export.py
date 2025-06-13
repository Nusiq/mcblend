'''
Run batch export operator for all animations of the first armature found in a
specified scene.
'''
import sys
import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:]

def main(scene_name: str, target_path: str):
    """Switch to *scene_name* then run the batch-export operator."""
    bpy.context.window.scene = bpy.data.scenes[scene_name]
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            bpy.context.view_layer.objects.active = obj
            break

    bpy.ops.mcblend.batch_export_animation(filepath=target_path)


if __name__ == "__main__":
    main(argv[0], argv[1])
