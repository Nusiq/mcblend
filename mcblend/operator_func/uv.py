'''
Functions related to creating UV map.
'''
from __future__ import annotations

import typing as tp
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from .common import (
    MINECRAFT_SCALE_FACTOR, get_mcube_size, ObjectMcProperties
)


def get_uv_face(
        objprop: ObjectMcProperties, face_name: str
    ) -> tp.Dict[str, int]:
    '''
    Returns a dictionary with information about indices of 4 loops of the uv
    face. The keys of the dictionary are strings *LD*, *RD*, *RU* and *LU*
    (left down, right down, right up, left up) and the values of the dictionary
    are integer indices of the loops.

    # Arguments:
    - `objprop: ObjectMcProperties` - the properties of the Minecraft object
    - `face_name: str` - decides which face should be returned. Accepts
      *front*, *back*, *left*, *right*, *top*, *bottom*

    # Returns:
    `Dict[str, int]` - a UV-face represented by a dictionary.
    '''
    bound_box_faces = {
        'front': [0, 4, 5, 1], 'back': [7, 3, 2, 6], 'left': [4, 7, 6, 5],
        'right': [3, 0, 1, 2], 'top': [1, 5, 6, 2], 'bottom': [0, 4, 7, 3]
    }
    # list with bound box vertex indices in order LD, RD, RU, LU
    f = bound_box_faces[face_name]
    bound_box = objprop.bound_box()
    bb_verts = {
        'LD': np.array(bound_box[f[0]]), 'RD': np.array(bound_box[f[1]]),
        'RU': np.array(bound_box[f[2]]), 'LU': np.array(bound_box[f[3]]),
    }

    for face in objprop.data_polygons():
        confirmed_vertices = {'LD': None, 'RD': None, 'RU': None, 'LU': None}
        for vertex_id, loop_id in zip(face.vertices, face.loop_indices):
            vertex = np.array(objprop.data_vertices()[vertex_id].co)
            for bbv_key, bbv_value in bb_verts.items():
                if np.allclose(vertex, bbv_value):
                    confirmed_vertices[bbv_key] = loop_id
        if all([i is not None for i in confirmed_vertices.values()]):
            return tp.cast(tp.Dict[str, int], confirmed_vertices)
    raise ValueError("Object is not a cube!")


def set_uv(
        objprop: ObjectMcProperties, uv_face: tp.Dict[str, int],
        crds: tp.Tuple[float, float], size: tp.Tuple[float, float],
        mirror_y: bool, mirror_x: bool
    ):
    '''
    Moves the placement of the loops of given UV face of an object to match
    given coordinates and size of the face.

    # Arguments:
    - `objprop: ObjectMcProperties` - the properties of the Minecraft object.
    - `uv_face: tp.Dict[str, int]` - UV face dictionary.
    - `crds: tp.Tuple[float, float]` - value from 0 to 1 the position of the
      bottom left loop using Blender UV-mapping coordinates system.
    - `size: tp.Tuple[float, float]` - value from 0 to 1 the size of the
      rectangle using Blender UV-mapping coordinates system.
    - `mirror_y: bool` - if True mirrors top and bottom sides of the face.
    - `mirror_x: bool` - if True mirrors left and right sides of the face.
    '''
    uv_data = objprop.data_uv_layers_active_data()
    order = ['LD', 'RD', 'RU', 'LU']

    if mirror_x:
        order = [order[i] for i in [1, 0, 3, 2]]
    if mirror_y:
        order = [order[i] for i in [2, 3, 0, 1]]

    uv_data[uv_face[order[0]]].uv = crds
    uv_data[uv_face[order[1]]].uv = (crds[0] + size[0], crds[1])
    uv_data[uv_face[order[2]]].uv = (crds[0] + size[0], crds[1] + size[1])
    uv_data[uv_face[order[3]]].uv = (crds[0], crds[1] + size[1])


def set_cube_uv(
        objprop: ObjectMcProperties, uv: tp.Tuple[float, float], width: float,
        depth: float, height: float, texture_width: int, texture_height: int
    ):
    '''
    Moves the placement of all of loops of UV of an object (cuboid) in a same
    way that Minecraft does.

    # Arguments:
    - `objprop: ObjectMcProperties` - properties of the object.
    - `uv: tp.Tuple[float, float]` - value from 0 to 1 the position of the
      bottom left loop using Blenders UV-mapping coordinates system.
    - `width: float` - width of the object converted to value from 0 to 1 in
      Blenders UV-mapping coordinates system.
    - `depth: float` - depth of the object converted to value from 0 to 1 in
      Blenders UV-mapping coordinates system.
    - `height: float` - height of the object converted to value from 0 to 1 in
      Blenders UV-mapping coordinates system.
    - `texture_width: int` - texture width for scaling.
    - `texture_height: int` - texture height for scaling.
    '''
    uv = (uv[0], texture_height-uv[1]-depth-height)
    if objprop.has_mc_mirror():
        set_uv(
            objprop, get_uv_face(objprop, 'left'),
            (uv[0]/texture_width, uv[1]/texture_height),
            (depth/texture_width, height/texture_height), False, True
        )
        set_uv(
            objprop, get_uv_face(objprop, 'front'),
            ((uv[0] + depth)/texture_width, uv[1]/texture_height),
            (width/texture_width, height/texture_height), True, False
        )
        set_uv(
            objprop, get_uv_face(objprop, 'right'),
            ((uv[0] + depth + width)/texture_width, uv[1]/texture_height),
            (depth/texture_width, height/texture_height), False, True
        )
        set_uv(
            objprop, get_uv_face(objprop, 'back'),
            ((uv[0] + 2*depth + width)/texture_width, uv[1]/texture_height),
            (width/texture_width, height/texture_height), True, False
        )

        set_uv(
            objprop, get_uv_face(objprop, 'top'),
            ((uv[0] + depth)/texture_width, (uv[1] + height)/texture_height),
            (width/texture_width, depth/texture_height), False, True
        )
        set_uv(
            objprop, get_uv_face(objprop, 'bottom'),
            ((uv[0] + depth + width)/texture_width, (uv[1] + height)/texture_height),
            (width/texture_width, depth/texture_height), False, True
        )
    else:
        set_uv(
            objprop, get_uv_face(objprop, 'right'),
            (uv[0]/texture_width, uv[1]/texture_height),
            (depth/texture_width, height/texture_height), False, False
        )
        set_uv(
            objprop, get_uv_face(objprop, 'front'),
            ((uv[0] + depth)/texture_width, uv[1]/texture_height),
            (width/texture_width, height/texture_height), False, False
        )
        set_uv(
            objprop, get_uv_face(objprop, 'left'),
            ((uv[0] + depth + width)/texture_width, uv[1]/texture_height),
            (depth/texture_width, height/texture_height), False, False
        )
        set_uv(
            objprop, get_uv_face(objprop, 'back'),
            ((uv[0] + 2*depth + width)/texture_width, uv[1]/texture_height),
            (width/texture_width, height/texture_height), False, False
        )

        set_uv(
            objprop, get_uv_face(objprop, 'top'),
            ((uv[0] + depth)/texture_width, (uv[1] + height)/texture_height),
            (width/texture_width, depth/texture_height), False, False
        )
        set_uv(
            objprop, get_uv_face(objprop, 'bottom'),
            ((uv[0] + depth + width)/texture_width, (uv[1] + height)/texture_height),
            (width/texture_width, depth/texture_height), False, False
        )

# (U, V) - 0, 0 = top left
class UvCorner(Enum):
    '''
    During UV-mapping UVBox objects use this enum combined with coordinates
    to suggest possible free space positions on the texture.

    For example a pair ((1, 2), UvCorner.TOP_RIGHT) represents a suggestion
    that there might be some free space for UvBox at (1, 2) pixel and that
    this the UvBox should touch this free space with its top right corner.
    '''
    TOP_RIGHT = 'TOP_RIGHT'
    TOP_LEFT = 'TOP_LEFT'
    BOTTOM_RIGHT = 'BOTTOM_RIGHT'
    BOTTOM_LEFT = 'BOTTOM_LEFT'


class UvBox:
    '''Rectangular space on the texture.'''
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
        '''The uv coordinates of the UvBox (bottom left corner).'''
        return self._uv

    @uv.setter
    def uv(self, uv):
        self._uv = uv

    def collides(self, other: UvBox):
        '''
        Returns True if this UvBox is colliding with another. Otherwise returns
        False.

        # Arguments:
        - `other: UvBox` - the other UvBox to test the collision.
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

        # Returns:
        `List[Tuple[Tuple[int, int], UvCorner]]` - list of suggestions for
        other UV-box to try while looking for empty space on the texture.
        '''
        size = (self.size[0]-1, self.size[1]-1)
        uv = self.uv
        # (near which wall?, which side of the wall?)
        return [
            # U, V-1 BOTTOM_LEFT (top left)
            ((uv[0], uv[1] - 1), UvCorner.BOTTOM_LEFT),
            # U+S, V-1 BOTTOM_RIGHT (top right)
            ((uv[0] + size[0], uv[1] - 1), UvCorner.BOTTOM_RIGHT),
            # U+S+1, V TOP_LEFT (right top)
            ((uv[0] + size[0] + 1, uv[1]), UvCorner.TOP_LEFT),
            # U+S+1, V+S BOTTOM_LEFT (right bottom)
            ((uv[0] + size[0] + 1, uv[1] + size[1]), UvCorner.BOTTOM_LEFT),
            # U+S, V+S+1 TOP_RIGHT (bottom right)
            ((uv[0] + size[0], uv[1] + size[1] + 1), UvCorner.TOP_RIGHT),
            # U, V+S+1 TOP_LEFT (bottom left)
            ((uv[0], uv[1] + size[1] + 1), UvCorner.TOP_LEFT),
            # U-1, V+S BOTTOM_RIGHT (left bottom)
            ((uv[0] - 1, uv[1] + size[1]), UvCorner.BOTTOM_RIGHT),
            # U-1,V TOP_RIGHT (left top)
            ((uv[0] - 1, uv[1]), UvCorner.TOP_RIGHT),
        ]

    def apply_suggestion(
            self, suggestion: tp.Tuple[tp.Tuple[int, int], UvCorner]
        ):
        '''
        Uses a suggestion (pair of coordinates and UvCorner) to set the UV for
        this UvBox.

        # Arguments:
        - `suggestion: Tuple[Tuple[int, int], UvCorner]` - the suggestion.
        '''
        size = (self.size[0]-1, self.size[1]-1)
        if suggestion[1] == UvCorner.TOP_LEFT:
            self.uv = suggestion[0]
        elif suggestion[1] == UvCorner.TOP_RIGHT:
            self.uv = (suggestion[0][0] - size[0], suggestion[0][1])
        elif suggestion[1] == UvCorner.BOTTOM_LEFT:
            self.uv = (suggestion[0][0], suggestion[0][1] - size[1])
        elif suggestion[1] == UvCorner.BOTTOM_RIGHT:
            self.uv = (suggestion[0][0] - size[0], suggestion[0][1] -size[1])


class UvMcCube(UvBox):
    '''
    Extends the UvBox by combining Six UvBoxes grouped together to represent
    space on the texture needed for UV mapping of single cube in Minecraft
    model.
    '''
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
        self.back = UvBox((width, height), (2*depth + width, depth))
        self.top = UvBox((width, depth), (depth, 0))
        self.bottom = UvBox((width, depth), (depth + width, 0))
        super().__init__(size, uv)

    @UvBox.uv.setter  # type: ignore
    def uv(self, uv):
        self._uv = uv
        self.right.uv = (uv[0], uv[1] + self.depth)
        self.front.uv = (uv[0] + self.depth, uv[1] + self.depth)
        self.left.uv = (uv[0] + self.depth + self.width, uv[1] + self.depth)
        self.back.uv = (uv[0] + 2*self.depth + self.width, uv[1] + self.depth)

        self.top.uv = (uv[0] + self.depth, uv[1])
        self.bottom.uv = (uv[0] + self.depth + self.width, uv[1])

    def collides(self, other: UvBox):
        '''
        Returns True if this UvBox is colliding with another. Otherwise returns
        False.

        # Arguments:
        - `other: UvBox` - the other UvBox to test the collision.
        '''
        for i in [
                self.right, self.front, self.left, self.back, self.top,
                self.bottom
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

        # Returns:
        `List[Tuple[Tuple[int, int], UvCorner]]` - list of suggestions for
        other UV-box to try while looking for empty space on the texture.
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


def plan_uv(boxes: tp.List[UvMcCube], width: int, height: int = None) -> bool:
    '''
    Plans UVs for all of the boxes on the list. The size of the texture is
    limited by width and optionally by height. Returns success result.

    # Arguments:
    - `boxes: List[UvMcCube]` - the list of the UvMcCubes.
    - `width: int` - the width of the texture.
    - `height: int` - the height of the texture (optional).

    # Returns:
    `bool` - True on succes. False when the texture width and height wasn't big
    enough to map all of the boxes.
    '''
    boxes = list(set(boxes))
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


@dataclass
class _UvGroup:
    '''
    Stores information about one UvGroup in get_uv_mc_cubes() function.

    This class has one value `items` - a dictionary that uses
    (width, depth, height) tuple as a key and has a UvMcCube as a value.

    Its used to make sure that the cubes with same mc_uv_groups and size use
    the same UvMcCube mapping.
    '''
    items: tp.Dict[tp.Tuple[int, int, int], UvMcCube] = field(
        default_factory=lambda: {}
    )


def get_uv_mc_cubes(
        objprops: tp.List[ObjectMcProperties],
        read_existing_uvs: bool
    ) -> tp.Dict[str, UvMcCube]:
    '''
    Creates UvMcCube for every object from objprops and returns the dictionary
    of that uses the names of the objects as keys and UvMcCubes as values.

    # Properties:
    - `objprops: List[ObjectMcProperties]` - list of the properties of the
      objects.
    - `read_existing_uvs: bool` - if set to True it sets the UV value in
      UvMcCube to a value read from the mc_uv property of the object.

    # Returns:
    `Dict[str, UvMcCube]` - a dictionary with UvMcCube for every object.
    '''
    def _scale(objprop: ObjectMcProperties) -> np.ndarray:
        '''Scale of a bone'''
        _, _, scale = objprop.matrix_world().decompose()
        return np.array(scale.xzy)

    # defaultdict(lambda: _UvGroup())
    uv_groups: tp.Dict[str, _UvGroup] = defaultdict(_UvGroup)
    result = {}

    for objprop in objprops:
        scale = (
            get_mcube_size(objprop) * _scale(objprop) *
            MINECRAFT_SCALE_FACTOR
        )

        if objprop.has_mc_inflate():
            scale = scale - objprop.get_mc_inflate()*2

        # width, height, depth
        width, height, depth = tuple([round(i) for i in scale])

        if read_existing_uvs and objprop.has_uv():
            result[objprop.name()] = UvMcCube(
                width, depth, height,
                objprop.get_mc_uv()
            )
        else:
            if (
                    objprop.has_mc_uv_group() and
                    (width, depth, height) in
                    uv_groups[objprop.get_mc_uv_group()].items
                ):
                result[objprop.name()] = uv_groups[
                    objprop.get_mc_uv_group()
                ].items[(width, depth, height)]
            else:
                result[objprop.name()] = UvMcCube(width, depth, height)
                if objprop.has_mc_uv_group():
                    uv_groups[
                        objprop.get_mc_uv_group()
                    ].items[(width, depth, height)] = result[objprop.name()]
    return result
