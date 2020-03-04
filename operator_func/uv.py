import bpy
import numpy as np

# Additional imports for mypy
import bpy_types
import typing as tp


from .common import MINECRAFT_SCALE_FACTOR


# TODO - porper naming of the functions below
def get_uv_face(
    obj: bpy_types.Object, face_name: str
) -> tp.Dict[str, int]:
    '''
    - obj - the mesh object with cube
    - face_name - decides which face should be returned

    Returns a dictionary with list of integer indices of loops which are part
    of a UV of a cube.
    '''
    bound_box_faces = {
        'front': [0, 4, 5, 1], 'back': [7, 3, 2, 6], 'left': [4, 7, 6, 5],
        'right': [3, 0, 1, 2], 'top': [1, 5, 6, 2], 'bottom': [4, 0, 3, 7]
    }
    # list with bound box vertex indices in order LD, RD, RU, LU
    f = bound_box_faces[face_name]
    bb = obj.bound_box
    bb_verts = {
        'LD': np.array(bb[f[0]]), 'RD': np.array(bb[f[1]]),
        'RU': np.array(bb[f[2]]), 'LU': np.array(bb[f[3]]),
    }
    for face in obj.data.polygons:
        confirmed_vertices = {'LD': None, 'RD': None, 'RU': None, 'LU': None}
        for vertex_id, loop_id in zip(face.vertices, face.loop_indices):
            vertex = np.array(obj.data.vertices[vertex_id].co)
            for bbv_key , bbv_value in bb_verts.items():
                if np.allclose(vertex, bbv_value):
                    confirmed_vertices[bbv_key] = loop_id
        if all([i is not None for i in confirmed_vertices.values()]):
            return tp.cast(tp.Dict[str, int], confirmed_vertices)
    raise ValueError("Object is not a cube!")


def set_uv(
    obj: bpy_types.Object, uv_face: tp.Dict[str, int],
    crds: tp.Tuple[float, float], size: tp.Tuple[float, float]
):
    '''
    - obj - the mesh object with cube

    - uv_face - the dictionary with loop indices used to define which loops
      of the uv should be moved.
    - crds - value from 0 to 1 the position of the bottom left loop on blender
      uv mapping coordinates system.
    - size - value from 0 to 1 the size of the rectangle in blender uv mapping
      coordinates system.
    '''
    uv_data = obj.data.uv_layers.active.data
    
    uv_data[uv_face['LD']].uv = crds
    uv_data[uv_face['RD']].uv = (crds[0] + size[0], crds[1])
    uv_data[uv_face['RU']].uv = (crds[0] + size[0], crds[1] + size[1])
    uv_data[uv_face['LU']].uv = (crds[0], crds[1] + size[1])


def set_cube_uv(
    obj: bpy_types.Object, crds: tp.Tuple[float, float], width: float,
    depth: float, height: float
):
    '''
    - obj - the mesh object with cube
    - crds - value from 0 to 1 the position of the bottom left loop on blender
      uv mapping coordinates system.
    - width - value from 0 to 1 the width of the cube converted into blender
      uv mapping coordinates system.
    - depth - value from 0 to 1 the depth of the cube converted into blender
      uv mapping coordinates system.
    - height - value from 0 to 1 the height of the cube converted into blender
      uv mapping coordinates system.

    Sets the UV faces of a mesh object that represents a mccube in the same
    patter as minecraft UV mapping.
    '''
    
    set_uv(
        obj, get_uv_face(obj, 'right'), crds, (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'front'),
        (crds[0] + depth, crds[1]), (width, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'left'),
        (crds[0] + depth + width, crds[1]), (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'back'),
        (crds[0] + 2*depth + width, crds[1]), (width, height)
    )
    
    set_uv(
        obj, get_uv_face(obj, 'top'),
        (crds[0] + depth, crds[1] + height), (width, depth)
    )
    set_uv(
        obj, get_uv_face(obj, 'bottom'),
        (crds[0] + depth + width, crds[1] + height), (width, depth)
    )
