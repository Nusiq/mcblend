import bpy
import numpy as np
from enum import Enum
from collections import defaultdict, deque

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
    obj: bpy_types.Object, uv: tp.Tuple[float, float], width: float,
    depth: float, height: float
):
    '''
    - obj - the mesh object with cube
    - uv - value from 0 to 1 the position of the bottom left loop on blender
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
        obj, get_uv_face(obj, 'right'), uv, (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'front'),
        (uv[0] + depth, uv[1]), (width, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'left'),
        (uv[0] + depth + width, uv[1]), (depth, height)
    )
    set_uv(
        obj, get_uv_face(obj, 'back'),
        (uv[0] + 2*depth + width, uv[1]), (width, height)
    )
    
    set_uv(
        obj, get_uv_face(obj, 'top'),
        (uv[0] + depth, uv[1] + height), (width, depth)
    )
    set_uv(
        obj, get_uv_face(obj, 'bottom'),
        (uv[0] + depth + width, uv[1] + height), (width, depth)
    )

# (U, V) - 0, 0 = top left
class UvCorner(Enum):
    TOP_RIGHT = 'TOP_RIGHT'
    TOP_LEFT = 'TOP_LEFT'
    BOTTOM_RIGHT = 'BOTTOM_RIGHT'
    BOTTOM_LEFT = 'BOTTOM_LEFT'


class UvBox(object):
    def __init__(
        self, size: tp.Tuple[int, int],
        uv: tp.Tuple[int, int] = None
    ):
        if uv is None:
            uv = (0, 0)
            self.is_mapped = False
        else:
            self.is_mapped = True

        self.size: tp.Tuple[int, int] = size
        self.uv: tp.Tuple[int, int] = uv

    @property
    def uv(self):
        return self._uv

    @uv.setter
    def uv(self, uv):
        self._uv = uv

    def collides(self, other: "UvBox"):
        '''
        Returns True if this UvBox is colliding with another. Otherwise returns
        False.
        '''
        # min max
        self_x = (self.uv[0], self.uv[0] + self.size[0])
        self_y = (self.uv[1], self.uv[1] + self.size[1])
        other_x = (other.uv[0], other.uv[0] + other.size[0])
        other_y = (other.uv[1], other.uv[1] + other.size[1])
        return (
            self_x[0] < other_x[1] and
            other_x[0] < self_x[1] and
            self_y[0] < other_y[1] and
            other_y[0] < self_y[1]
        )

    def suggest_positions(
        self
    ) -> tp.List[tp.Tuple[tp.Tuple[int, int], UvCorner]]:
        '''
        Returns list of positions touching this UvBox for other UvBox without
        overlappnig.

        The order of returned points:
        0. (top left) 1. (top right) 2. (right top) 3. (right bottom)
        4. (bottom right) 5. (bottom left) 6. (left bottom) 7. (left top)
        '''
        ss = (self.size[0]-1, self.size[1]-1)
        uv = self.uv
        # (near which wall?, which side of the wall?)
        return [
            # U, V-1 BOTTOM_LEFT (top left)
            ((uv[0], uv[1] - 1), UvCorner.BOTTOM_LEFT),
            # U+S, V-1 BOTTOM_RIGHT (top right)
            ((uv[0] + ss[0], uv[1] - 1), UvCorner.BOTTOM_RIGHT),
            # U+S+1, V TOP_LEFT (right top)
            ((uv[0] + ss[0] + 1,  uv[1]), UvCorner.TOP_LEFT),
            # U+S+1, V+S BOTTOM_LEFT (right bottom)
            ((uv[0] + ss[0] + 1, uv[1] + ss[1]), UvCorner.BOTTOM_LEFT),
            # U+S, V+S+1 TOP_RIGHT (bottom right)
            ((uv[0] + ss[0], uv[1] + ss[1] + 1), UvCorner.TOP_RIGHT),
            # U, V+S+1 TOP_LEFT (bottom left)
            ((uv[0], uv[1] + ss[1] + 1), UvCorner.TOP_LEFT),
            # U-1, V+S BOTTOM_RIGHT (left bottom)
            ((uv[0] - 1, uv[1] + ss[1]), UvCorner.BOTTOM_RIGHT),
            # U-1,V TOP_RIGHT (left top)
            ((uv[0] - 1, uv[1]), UvCorner.TOP_RIGHT),
        ]

    def apply_suggestion(
        self, suggestion: tp.Tuple[tp.Tuple[int, int], UvCorner]
    ):
        ss = (self.size[0]-1, self.size[1]-1)
        if suggestion[1] == UvCorner.TOP_LEFT:
            self.uv = suggestion[0]
        elif suggestion[1] == UvCorner.TOP_RIGHT:
            self.uv = (suggestion[0][0] - ss[0], suggestion[0][1])
        elif suggestion[1] == UvCorner.BOTTOM_LEFT:
            self.uv = (suggestion[0][0], suggestion[0][1] - ss[1])
        elif suggestion[1] == UvCorner.BOTTOM_RIGHT:
            self.uv = (suggestion[0][0] - ss[0], suggestion[0][1] -ss[1])


class UvMcCube(UvBox):
    def __init__(
        self, width: int, depth: int, height: int,
        uv: tp.Tuple[int, int] = None
    ):
        size = (
            2*depth + 2*width,
            height + depth
        )
        self.depth = depth
        self.height = height
        self.width = width

        self.right = UvBox((depth, height), (0, depth))
        self.front = UvBox((width, height), (depth, depth))
        self.left = UvBox((depth, height), (depth + width, depth))
        self.back = UvBox((width, height),(2*depth + width, depth))
        self.top = UvBox((width, depth), (depth, 0))
        self.bottom = UvBox((width, depth), (depth + width, 0))
        super().__init__(size, uv)

    @UvBox.uv.setter
    def uv(self, uv):
        self._uv = uv
        self.right.uv = (uv[0], uv[1] + self.depth)
        self.front.uv = (uv[0] + self.depth, uv[1] + self.depth)
        self.left.uv = (uv[0] + self.depth + self.width, uv[1] + self.depth)
        self.back.uv = (uv[0] + 2*self.depth + self.width, uv[1] + self.depth)

        self.top.uv = (uv[0] + self.depth, uv[1])
        self.bottom.uv = (uv[0] + self.depth + self.width, uv[1])

    def collides(self, other: "UvBox"):
        '''
        Returns True if this UvBox is colliding with another. Otherwise returns
        False.
        '''
        
        for i in [
            self.right, self.front, self.left, self.back, self.top, self.bottom
        ]:
            if i.collides(other):
                return True
        return False

    def suggest_positions(
        self
    ) -> tp.List[tp.Tuple[tp.Tuple[int, int], UvCorner]]:
        '''
        Returns list of positions touching this UvBox for other UvBox without
        overlappnig.
        '''
        # 0. (top left) 1. (top right) 2. (right top) 3. (right bottom)
        # 4. (bottom right) 5. (bottom left) 6. (left bottom) 7. (left top)
        result = []
        result.extend([
            s for i, s  in enumerate(self.right.suggest_positions())
            if i in  [0, 5, 6]
        ])
        result.extend([
            s for i, s  in enumerate(self.top.suggest_positions())
            if i in  [0, 6, 7]
        ])
        result.extend([
            s for i, s  in enumerate(self.bottom.suggest_positions())
            if i in  [1, 2, 3]
        ])
        result.extend([
            s for i, s  in enumerate(self.back.suggest_positions())
            if i in  [1, 3, 4]
        ])
        return result


def plan_uv(boxes: tp.List[UvBox], width: int, height: int=None) -> bool:
    '''
    Plans UVs for all of the boxes on the list. The size of the texture is
    limited by width and optionally by height.

    Returns success result.
    '''
    boxes.sort(key=lambda box: box.size[0], reverse=True)

    suggestions: tp.List[
        tp.Tuple[tp.Tuple[int, int], UvCorner]
    ] = [((0, 0), UvCorner.TOP_LEFT)]

    authors: tp.List[UvBox] = []  # authors of the suggestions
    mapped_boxes = []
    unmapped_boxes = []
    for box in boxes:
        if box.is_mapped:
            mapped_boxes.append(box)
        else:
            unmapped_boxes.append(box)

    def _is_out_of_bounds(uv, size=(0, 0)):
        return (
            uv[0] < 0 or uv[1] < 0 or uv[0] + size[0] > width or
            (height is not None and uv[1] + size[1] > height)
        )

    for box in unmapped_boxes:
        suggestion_i = -1
        while len(suggestions) > suggestion_i + 1:
            suggestion_i += 1
            # Apply suggestion
            box.apply_suggestion(suggestions[suggestion_i])

            # Test if suggestion in texture space, if no - delete and try again
            if _is_out_of_bounds(suggestions[suggestion_i][0]):
                del suggestions[suggestion_i]
                suggestion_i -= 1

            # Test if box in texture space
            elif not _is_out_of_bounds(box.uv, box.size):
                # Test if suggestion doesn't collide
                for other_box in mapped_boxes:
                    if box.collides(other_box):  # Bad suggestion. Find more
                        if other_box not in authors:
                            authors.append(other_box)
                            suggestions.extend(other_box.suggest_positions())
                        break
                else:  # didn't found collisions. Good suggestion, break the loop
                    box.is_mapped = True
                    mapped_boxes.append(box)
                    suggestions.extend(box.suggest_positions())
                    del suggestions[suggestion_i]
                    break
        else:  # No good suggestion found for current box.
            box.uv = (0, 0)
            return False
    return True
