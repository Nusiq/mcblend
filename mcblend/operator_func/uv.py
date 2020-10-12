'''
Functions related to creating UV map.
'''
from __future__ import annotations

from typing import (
    Dict, Tuple, List, Iterator, Collection, NamedTuple, Sequence)
from enum import Enum
from dataclasses import dataclass, field
from itertools import filterfalse
import numpy as np

import bpy
import bpy_types

from .texture_generator import Mask
from .exception import NotEnoughTextureSpace
from .json_tools import get_vect_json
from .common import (
    MINECRAFT_SCALE_FACTOR, McblendObject, McblendObjectGroup, CubePolygon)




class CoordinatesConverter:
    '''
    An object which allows conversion of coordinates defined by space_a to
    space_b (passed in the constructor).

    Example: [[1, 2], [3, 4], [5, 6]] is a 3D space first dimension in range
    from 1 to 2, second from 3 to 4 and third from 5 to 6. Both spaces should
    have the same number of dimensions.

    :param space_a: The spce to convert from.
    :param space_b: The space to convert to.
    '''
    def __init__(self, space_a: np.ndarray, space_b: np.ndarray):
        self.space_a = np.copy(space_a.T)
        self.space_b = np.copy(space_b.T)
        self.scale_a = self.space_a[1] - self.space_a[0]
        self.scale_b = self.space_b[1] - self.space_b[0]

    def convert(self, x: Collection[float]) -> Collection[float]:
        '''
        Performs a converison on coordinates passed to the function with
        x argument (from space_a to space_b).

        :param x: the vector with coordinates.
        :returns: converted vector.
        '''
        x = np.array(x).T
        return tuple(  # type: ignore
            (((x-self.space_a[0])/self.scale_a)*self.scale_b)+self.space_b[0]
        )


# (U, V) - 0, 0 = top left
class UvCorner(Enum):
    '''
    Used by the Suggestion object to point at corner of a UvBox.
    '''
    TOP_RIGHT = 'TOP_RIGHT'
    TOP_LEFT = 'TOP_LEFT'
    BOTTOM_RIGHT = 'BOTTOM_RIGHT'
    BOTTOM_LEFT = 'BOTTOM_LEFT'


class Suggestion(NamedTuple):
    '''
    A class used by UvBoxes to suggest free spaces on the texture during
    UV-mapping.

    :prop position: Position that other UvBox should touch with its corener.
    :prop corner: Which corner should touch the position.
    '''
    position: Tuple[int, int]
    corner: UvCorner

class UvBox:
    '''Rectangular space on the texture.'''
    def __init__(
            self, size: Tuple[int, int],
            uv: Tuple[int, int] = None
        ):
        if uv is None:
            uv = (0, 0)
            self.is_mapped = False
        else:
            self.is_mapped = True

        self.size: Tuple[int, int] = size
        self.uv: Tuple[int, int] = uv

    def collides(self, other: UvBox):
        '''
        Returns True if this UvBox is colliding with other UvBox. Otherwise
        returns False.

        :param other: The other UvBox to test the collision.
        :returns: True if there is a collision.
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

    def suggest_positions(self) -> List[Suggestion]:
        '''
        Returns list of positions touching this UvBox for other UvBox without
        overlappnig.

        :returns: list of suggestions for other UV-box to try while looking
            for empty space on the texture.
        '''
        size = (self.size[0]-1, self.size[1]-1)
        uv = self.uv
        # (near which wall?, which side of the wall?)
        return [
            # U, V-1 BOTTOM_LEFT (top left)
            Suggestion((uv[0], uv[1] - 1), UvCorner.BOTTOM_LEFT),
            # U+S, V-1 BOTTOM_RIGHT (top right)
            Suggestion((uv[0] + size[0], uv[1] - 1), UvCorner.BOTTOM_RIGHT),
            # U+S+1, V TOP_LEFT (right top)
            Suggestion((uv[0] + size[0] + 1, uv[1]), UvCorner.TOP_LEFT),
            # U+S+1, V+S BOTTOM_LEFT (right bottom)
            Suggestion(
                (uv[0] + size[0] + 1, uv[1] + size[1]), UvCorner.BOTTOM_LEFT
            ),
            # U+S, V+S+1 TOP_RIGHT (bottom right)
            Suggestion(
                (uv[0] + size[0], uv[1] + size[1] + 1), UvCorner.TOP_RIGHT
            ),
            # U, V+S+1 TOP_LEFT (bottom left)
            Suggestion((uv[0], uv[1] + size[1] + 1), UvCorner.TOP_LEFT),
            # U-1, V+S BOTTOM_RIGHT (left bottom)
            Suggestion((uv[0] - 1, uv[1] + size[1]), UvCorner.BOTTOM_RIGHT),
            # U-1,V TOP_RIGHT (left top)
            Suggestion((uv[0] - 1, uv[1]), UvCorner.TOP_RIGHT),
        ]

    def apply_suggestion(self, suggestion: Suggestion):
        '''
        Uses a suggestion to set the UV for this UvBox.

        :param suggestion: the suggestion.
        '''
        size = (self.size[0]-1, self.size[1]-1)
        if suggestion.corner == UvCorner.TOP_LEFT:
            self.uv = suggestion.position
        elif suggestion.corner == UvCorner.TOP_RIGHT:
            self.uv = (
                suggestion.position[0] - size[0], suggestion.position[1]
            )
        elif suggestion.corner == UvCorner.BOTTOM_LEFT:
            self.uv = (
                suggestion.position[0], suggestion.position[1] - size[1]
            )
        elif suggestion.corner == UvCorner.BOTTOM_RIGHT:
            self.uv = (
                suggestion.position[0] - size[0],
                suggestion.position[1] -size[1]
            )

    def paint_texture(
            self, arr: np.ndarray, resolution: int = 1
        ):
        '''
        Paints the UvBox on the texture represented by the numpy array.

        :param arr: the texture array.
        :param resolution: the resolution of the Minecraft texture. Where 1 is
            standard Minecrft texture resolution (16 pixels for one block).
        '''
        min1 = int(arr.shape[0]/resolution)-int(self.uv[1]+self.size[1])
        max1 = int(arr.shape[0]/resolution)-int(self.uv[1])
        min2, max2 = int(self.uv[0]), int(self.uv[0]+self.size[0])
        min1 = min1 * resolution
        min2 = min2 * resolution
        max1 = max1 * resolution
        max2 = max2 * resolution

        # Alway paint white
        texture_part = arr[min1:max1, min2:max2]
        texture_part[...] = 1  # Set RGBA white

class McblendObjUvBox(UvBox):
    '''
    An UvBox that holds reference to an McblendObject and provides a method
    to set it's UV.
    '''
    def new_uv_layer(self):
        '''Adds new UV-layer to contained McblendObject.'''
        raise NotImplementedError()

    def set_blender_uv(self, converter: CoordinatesConverter):
        '''
        Sets the UV of a blender object.

        :param converter: The coordinates converter used to convert from
            Minecraft UV coordinates (used internally by this object) to
            Blender UV coordinates.
        '''
        raise NotImplementedError()

    def clear_uv_layers(self):
        '''
        Clears the uv layers from the wrapped McblendObject.
        '''
        raise NotImplementedError()

class UvMcCubeFace(UvBox):
    '''
    A single face in the UvBox.
    '''
    def __init__(
            self, cube: UvMcCube, cube_polygon: CubePolygon,
            size: Tuple[int, int], masks: Sequence[Mask],
            uv: Tuple[int, int]=None):
        super().__init__(size, uv=uv)
        self.cube = cube
        self.cube_polygon = cube_polygon
        self.masks = masks

    def set_blender_uv(self, converter: CoordinatesConverter):
        '''
        Sets the UV of a blender object.

        :param converter: the coordinates converter used to convert from
            Minecraft UV coordinates (used internally by this object) to
            Blender UV coordinates.
        '''
        # Order of the faces for: left_down, right_down, right_up, left_up

        # Cube polygon data
        cp_loop_indices = self.cube_polygon.side.loop_indices
        cp_order = self.cube_polygon.order

        left_down = cp_loop_indices[cp_order[0]]
        right_down = cp_loop_indices[cp_order[1]]
        right_up = cp_loop_indices[cp_order[2]]
        left_up = cp_loop_indices[cp_order[3]]

        uv_data = self.cube.thisobj.obj_data.uv_layers.active.data

        uv_data[left_down].uv = converter.convert(
            (self.uv[0], self.uv[1] + self.size[1]))
        uv_data[right_down].uv = converter.convert(
            (self.uv[0] + self.size[0], self.uv[1] + self.size[1]))
        uv_data[right_up].uv = converter.convert(
            (self.uv[0] + self.size[0], self.uv[1]))
        uv_data[left_up].uv = converter.convert(self.uv)

    def paint_texture(
            self, arr: np.ndarray, resolution: int = 1
        ):
        '''
        Paints the UvBox on the texture.

        :param arr: the texture array.
        :param resolution: the resolution of the Minecraft texture. Where 1 is
            standard Minecrft texture resolution (16 pixels for one block).
        '''
        min1 = int(arr.shape[0]/resolution)-int(self.uv[1]+self.size[1])
        max1 = int(arr.shape[0]/resolution)-int(self.uv[1])
        min2, max2 = int(self.uv[0]), int(self.uv[0]+self.size[0])
        min1 = min1 * resolution
        min2 = min2 * resolution
        max1 = max1 * resolution
        max2 = max2 * resolution

        # Alway paint white
        texture_part = arr[min1:max1, min2:max2]
        texture_part[...] = 1.0  # Set RGBA white

        texture_part = texture_part[..., :3]  # No alpha channel filters yet
        for mask in self.masks:
            mask.apply(texture_part)

class UvMcCube(McblendObjUvBox):
    '''
    Class that Combiens Six UvMcCubeFaces grouped together to represent space
    on the texture needed for UV mapping of single cube in Minecraft model.
    '''
    def __init__(
            self, width: int, depth: int, height: int,
            thisobj: McblendObject):
        size = (
            2*depth + 2*width,
            height + depth
        )
        self.depth = depth
        self.height = height
        self.width = width
        self.thisobj = thisobj

        cube_polygons = self.thisobj.cube_polygons()

        if self.thisobj.mirror:
            cp1, cp3 = cube_polygons.west, cube_polygons.east
        else:
            cp1, cp3 = cube_polygons.east, cube_polygons.west
        # right/left
        self.side1 = UvMcCubeFace(
            self, cp1, (depth, height),
            thisobj.side1_uv_masks, uv=(0, depth))
        # front
        self.side2 = UvMcCubeFace(
            self, cube_polygons.north, (width, height),
            thisobj.side2_uv_masks, uv=(depth, depth))
        # left/right
        self.side3 = UvMcCubeFace(
            self, cp3, (depth, height),
            thisobj.side3_uv_masks, uv=(depth + width, depth))
        # back
        self.side4 = UvMcCubeFace(
            self, cube_polygons.south, (width, height),
            thisobj.side4_uv_masks, uv=(2*depth + width, depth))
        # top
        self.side5 = UvMcCubeFace(
            self, cube_polygons.up, (width, depth),
            thisobj.side5_uv_masks, uv=(depth, 0))
        # bottom
        self.side6 = UvMcCubeFace(
            self, cube_polygons.down, (width, depth),
            thisobj.side6_uv_masks, uv=(depth + width, 0))
        super().__init__(size, None)

    @property  # type: ignore
    def uv(self) -> Tuple[int, int]:  # type: ignore
        '''UV of the object.'''
        return self._uv

    @uv.setter
    def uv(self, uv: Tuple[int, int]):
        self._uv = uv
        self.side1.uv = (uv[0], uv[1] + self.depth)
        self.side2.uv = (uv[0] + self.depth, uv[1] + self.depth)
        self.side3.uv = (uv[0] + self.depth + self.width, uv[1] + self.depth)
        self.side4.uv = (uv[0] + 2*self.depth + self.width, uv[1] + self.depth)

        self.side5.uv = (uv[0] + self.depth, uv[1])
        self.side6.uv = (uv[0] + self.depth + self.width, uv[1])

    def collides(self, other: UvBox):
        for i in [
                self.side1, self.side2, self.side3, self.side4, self.side5,
                self.side6
            ]:
            if i.collides(other):
                return True
        return False

    def suggest_positions(self) -> List[Suggestion]:
        '''
        Returns list of positions next to this UV box that can be used
        by other UV box to set the UV that doesn't overlap this object.

        :returns: list of suggestions for other UV-box to try while looking for
            empty space on the texture.
        '''
        # 0. (top left) 1. (top right) 2. (right top) 3. (right bottom)
        # 4. (bottom right) 5. (bottom left) 6. (left bottom) 7. (left top)
        result = []
        result.extend([
            s for i, s  in enumerate(self.side1.suggest_positions())
            if i in  [0, 5, 6]
        ])
        result.extend([
            s for i, s  in enumerate(self.side5.suggest_positions())
            if i in  [0, 6, 7]
        ])
        result.extend([
            s for i, s  in enumerate(self.side6.suggest_positions())
            if i in  [1, 2, 3]
        ])
        result.extend([
            s for i, s  in enumerate(self.side4.suggest_positions())
            if i in  [1, 3, 4]
        ])
        return result

    def set_blender_uv(self, converter: CoordinatesConverter):
        self.side1.set_blender_uv(converter)
        self.side2.set_blender_uv(converter)
        self.side3.set_blender_uv(converter)
        self.side4.set_blender_uv(converter)
        self.side5.set_blender_uv(converter)
        self.side6.set_blender_uv(converter)

    def clear_uv_layers(self):
        while len(self.thisobj.obj_data.uv_layers) > 0:
            self.thisobj.obj_data.uv_layers.remove(
                self.thisobj.obj_data.uv_layers[0]
            )

    def paint_texture(
            self, arr: np.ndarray, resolution: int = 1
        ):
        self.side1.paint_texture(arr, resolution)
        self.side2.paint_texture(arr, resolution)
        self.side3.paint_texture(arr, resolution)
        self.side4.paint_texture(arr, resolution)
        self.side5.paint_texture(arr, resolution)
        self.side6.paint_texture(arr, resolution)

    def new_uv_layer(self):
        self.thisobj.obj_data.uv_layers.new()

class UvGroup(McblendObjUvBox):
    '''
    A colleciton of McblendObjUvBoxes that have the same UV mapping.

    Internally all of the properties are read from the first box on the list.
    The set_blender_uv function applies changes to all of the objects.
    '''
    def __init__(self, main_object: McblendObjUvBox):
        # pylint: disable=super-init-not-called
        self._objects: List[McblendObjUvBox] = [main_object]

    def append(self, obj: McblendObjUvBox):
        '''Adds another McblendObjjUvBox to this group.'''
        obj.uv = self.uv  # type: ignore
        obj.is_mapped = self.is_mapped  # type: ignore
        obj.size = self.size
        self._objects.append(obj)

    @property  # type: ignore
    def uv(self) -> Tuple[int, int]:  # type: ignore
        '''Uv of the object.'''
        return self._objects[0].uv

    @uv.setter
    def uv(self, uv: Tuple[int, int]):
        for obj in self._objects:
            obj.uv = uv

    @property  # type: ignore
    def size(self) -> Tuple[int, int]:  # type: ignore
        '''Size of the object.'''
        return self._objects[0].size

    @size.setter
    def size(self, size: Tuple[int, int]):
        for obj in self._objects:
            obj.size = size

    @property  # type: ignore
    def is_mapped(self) -> bool:  # type: ignore
        '''Returns whether the object has assigned UV-mapping.'''
        return self._objects[0].is_mapped

    @is_mapped.setter
    def is_mapped(self, val: bool):
        for obj in self._objects:
            obj.is_mapped = val

    def collides(self, other: UvBox) -> bool:
        return self._objects[0].collides(other)

    def suggest_positions(
            self
        ) -> List[Suggestion]:
        return self._objects[0].suggest_positions()

    def apply_suggestion(
            self, suggestion: Suggestion
        ):
        for obj in self._objects:
            obj.apply_suggestion(suggestion)

    def set_blender_uv(self, converter: CoordinatesConverter):
        for obj in self._objects:
            obj.set_blender_uv(converter)

    def clear_uv_layers(self):
        for obj in self._objects:
            obj.clear_uv_layers()

    def paint_texture(self, arr: np.ndarray, resolution: int = 1):
        # They mapped to one place (paint only one)
        # for obj in self._objects:
        if len(self._objects) > 0 :
            self._objects[0].paint_texture(arr, resolution)

    def new_uv_layer(self):
        for obj in self._objects:
            obj.new_uv_layer()

@dataclass
class UvMapper:
    '''
    A class that helps with UV-mapping.
    '''
    width: int
    height: int
    uv_boxes: List[McblendObjUvBox] = field(default_factory=list)

    def load_uv_boxes(
            self, object_properties: McblendObjectGroup,
            context: bpy_types.Context
        ):
        # pylint: disable=duplicate-code
        '''
        Populates the uv_boxes dictionary.

        # Properties:
        :prop object_properties: The properties of all of the Minecraft cubes
            and bones.
        :prop context: The context of running the operator.
        '''
        bpy.ops.screen.animation_cancel()
        original_frame = context.scene.frame_current
        try:
            context.scene.frame_set(0)

            # Dictionary identifed by width, depth, height, group name
            cube_uv_groups: Dict[Tuple[int, int, int, str], UvGroup] = {}

            objprop: McblendObject
            for objprop in object_properties.values():
                if objprop.obj_type != 'MESH':
                    continue
                scale = (
                    objprop.mcube_size *
                    # scale
                    np.array(objprop.obj_matrix_world.decompose()[2].xzy) *
                    MINECRAFT_SCALE_FACTOR
                )

                if objprop.inflate != 0:
                    scale = scale - objprop.inflate * 2

                # width, height, depth - rounded down to int
                # first round with get_json_vect to avoid numerical errors and
                # than round down to int (like minecraft does).
                width, height, depth = [
                    int(i) for i in get_vect_json(scale)]
                if objprop.uv_group != '':
                    curr_key = (width, depth, height, objprop.uv_group)
                    if curr_key in cube_uv_groups:
                        cube_uv_groups[curr_key].append(
                            UvMcCube(width, depth, height, objprop)
                        )
                    else:
                        cube_uv_groups[curr_key] = UvGroup(
                            UvMcCube(width, depth, height, objprop)
                        )
                        self.uv_boxes.append(cube_uv_groups[curr_key])
                else:
                    self.uv_boxes.append(
                        UvMcCube(width, depth, height, objprop)
                    )
        finally:
            context.scene.frame_set(original_frame)

    def plan_uv(self, allow_expanding: bool):
        '''
        Plans UVs for all of the boxes on the list. Uses self.width and
        self.height to limit the area unless the anllow_expanding is set to
        True. Raises NotEnoughTextureSpace when the texture width and height
        wasn't big enough to map all of the boxes.

        :param allow_expanding: Whether the texture space can be expanded to
            fit all of the objects in it.
        '''
        self.uv_boxes.sort(key=lambda box: box.size[0], reverse=True)

        if allow_expanding and len(self.uv_boxes) > 0:
            self.width = max([self.width, self.uv_boxes[0].size[0]])

        suggestions: List[Suggestion] = [Suggestion((0, 0), UvCorner.TOP_LEFT)]

        authors: List[UvBox] = []  # authors of the suggestions
        mapped_boxes = []
        unmapped_boxes = []
        for box in self.uv_boxes:
            if box.is_mapped:
                mapped_boxes.append(box)
            else:
                unmapped_boxes.append(box)

        def _is_out_of_bounds(uv, size=(0, 0)):
            return (
                uv[0] < 0 or uv[1] < 0 or uv[0] + size[0] > self.width or
                (not allow_expanding and uv[1] + size[1] > self.height)
            )

        # pylint: disable=too-many-nested-blocks
        for box in unmapped_boxes:
            suggestion_i = -1
            while len(suggestions) > suggestion_i + 1:
                suggestion_i += 1
                # Apply suggestion
                box.apply_suggestion(suggestions[suggestion_i])

                # Test if box in texture space
                if not _is_out_of_bounds(box.uv, box.size):
                    # Test if suggestion doesn't collide
                    for other_box in mapped_boxes:
                        if box.collides(other_box):  # Bad suggestion. Find more
                            if other_box not in authors:
                                authors.append(other_box)
                                suggestions.extend(filterfalse(
                                    lambda x: _is_out_of_bounds(x.position),
                                    other_box.suggest_positions()
                                ))
                            break
                    else:  # didn't found collisions. Good suggestion, break the loop
                        box.is_mapped = True
                        mapped_boxes.append(box)
                        suggestions.extend(filterfalse(
                            lambda x: _is_out_of_bounds(x.position),
                            box.suggest_positions()
                        ))
                        del suggestions[suggestion_i]
                        break
            else:  # No good suggestion found for current box.
                box.uv = (0, 0)
                raise NotEnoughTextureSpace()

    def __iter__(self) -> Iterator[McblendObjUvBox]:
        for i in self.uv_boxes:
            yield i
