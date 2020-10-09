'''
This module contains all of the panels for mcblend GUI.
'''
# don't import future annotations Blender needs that
from typing import Tuple, List, Optional
from dataclasses import dataclass

import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty, FloatProperty,
    FloatVectorProperty, PointerProperty, CollectionProperty,
    EnumProperty, PointerProperty, IntVectorProperty
)
from .operator_func.texture_generator import (
    list_mask_types_as_blender_enum, UvMaskTypes,
    list_mix_mask_modes_as_blender_enum)


class OBJECT_NusiqMcblendStripeProperties(bpy.types.PropertyGroup):
    width: IntProperty(  # type: ignore
        name='Width', default=1)
    width_relative: FloatProperty(  # type: ignore
        name='Width', min=0.0, max=1.0, default=0.1)
    strength: FloatProperty(  # type: ignore
        name='Strength', min=0.0, max=1.0, default=1.0)

class OBJECT_NusiqMcblendColorProperties(bpy.types.PropertyGroup):
    color: FloatVectorProperty(  # type: ignore
        name='Color',  subtype='COLOR',
        min=0, max=1, step=1000, default=(1.0, 1.0, 1.0))

class OBJECT_NusiqMcblendUvMaskProperties(bpy.types.PropertyGroup):
    ui_collapsed: BoolProperty(  # type: ignore
        name='Collapse', default=False)
    mask_type: EnumProperty(  # type: ignore
        items=list_mask_types_as_blender_enum,
        name='Mask type')

    # mode: str  # MixMask
    mode: EnumProperty(  # type: ignore
        items=list_mix_mask_modes_as_blender_enum,
        name='Mix mode')
    # MixMask
    children: IntProperty(  # type: ignore
        name='Number of children', min=1, default=2)
    # colors: List[Color]  # ColorPalletteMask
    colors: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendColorProperties,
        name='Colors')
    # interpolate: bool  # ColorPalletteMask
    interpolate: BoolProperty(  # type: ignore
        name='Interpolate')
    # normalize: bool  # ColorPalletteMask
    normalize: BoolProperty(  # type: ignore
        name='Normalize')
    # p1: Tuple[float, float]  # GradientMask ElipseMask RectangleMask
    p1_relative: FloatVectorProperty(  # type: ignore
        name='Point A', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p2: Tuple[float, float]  # GradientMask ElipseMask RectangleMask
    p2_relative: FloatVectorProperty(  # type: ignore
        name='Point B', min=0.0, max=1.0, default=(0.0, 0.0), size=2)
    # p1: Tuple[float, float]  # GradientMask ElipseMask RectangleMask
    p1: IntVectorProperty(  # type: ignore
        name='Point A', default=(0.1, 0.1), size=2)
    # p2: Tuple[float, float]  # GradientMask ElipseMask RectangleMask
    p2: IntVectorProperty(  # type: ignore
        name='Point B', default=(0.9, 0.9), size=2)
    # stripes: List[Stripe]  # GradientMask StripesMask
    stripes: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendStripeProperties,
        name='Stripes')
    # relative_boundries: bool  # GradientMask ElipseMask RectangleMask StripesMask
    relative_boundries: BoolProperty(  # type: ignore
        name='Relative boundries')
    # expotent: float  # GradientMask ElipseMask RectangleMask RandomMask
    #  MixMask
    expotent: FloatProperty(  # type: ignore
        name='Expotent', default=1.0, soft_min=-10.0, soft_max=10.0)
    # strength: Tuple[float, float]  # ElipseMask RectangleMask RandomMask
    #  MixMask
    strength: FloatVectorProperty(  # type: ignore
        min=0.0, max=1.0, default=(0.0, 1.0), size=2)
    # hard_edge: bool  # ElipseMask RectangleMask
    hard_edge: BoolProperty(  # type: ignore
        name='Hard edge')
    # horizontal: bool  # StripesMask
    horizontal: BoolProperty(  # type: ignore
        name='Horizontal')
    # seed: Optional[int]  # RandomMask
    use_seed: BoolProperty(  # type: ignore
        name='Use seed')
    seed: IntProperty(  # type: ignore
        name='Seed')
    # color: Tuple[float, float, float]  # ColorMask
    color: PointerProperty(  # type: ignore
        type=OBJECT_NusiqMcblendColorProperties,
        name='Color')

def get_unused_uv_group_name(base_name: str, i=1):
    uv_groups = bpy.context.scene.nusiq_mcblend_uv_groups
    name = base_name  # f'{base_name}.{i:04}'
    while name in uv_groups.keys():
        name = f'{base_name}.{i:04}'
        i += 1
    return name

def update_uv_group_name(uv_group, new_name: str):
    # Update the names of all of the meshes
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            obj_props = obj.nusiq_mcblend_object_properties
            if obj_props.uv_group == uv_group.name:
                obj_props.uv_group = new_name
    # Update the name of the UV group
    uv_group['name'] = new_name

def set_uv_group_name(self, value):
        old_name = self.name

        groups = bpy.context.scene.nusiq_mcblend_uv_groups

        
        # Empty name is no allowed
        if value == '':
            return

        # If name already in use rename the other uv group
        for other_group in groups:
            if (  # Change the of the duplicate if there is one
                    other_group.path_from_id() != self.path_from_id() and
                    other_group.name == value):
                # Get starting name index
                i = 1
                base_name = value
                split_name = value.split('.')
                try:
                    prev_i = int(split_name[-1])
                    i = i if prev_i <= 0 else prev_i
                    base_name = '.'.join(split_name[:-1])
                except ValueError:
                    pass
                other_new_name = get_unused_uv_group_name(base_name, i)
                update_uv_group_name(other_group, other_new_name)
                break
        update_uv_group_name(self, value)

def get_uv_group_name(self):
    return self['name']


class OBJECT_NusiqMcblendUvGroupProperties(bpy.types.PropertyGroup):
    name: StringProperty(  # type: ignore
        name="Name",
        description='The name of the UV group.',
        # The Add operator overwrites default value on creation to trigger the
        # update function
        default='',
        maxlen=1024, set=set_uv_group_name, get=get_uv_group_name)
    side1: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side1 of the cuboid.')
    side2: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side2 of the cuboid.')
    side3: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side3 of the cuboid.')
    side4: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side4 of the cuboid.')
    side5: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side5 of the cuboid.')
    side6: CollectionProperty(  # type: ignore
        type=OBJECT_NusiqMcblendUvMaskProperties,
        description='Collection of the filters for side6 of the cuboid.')

class OBJECT_NusiqMcblendObjectProperties(bpy.types.PropertyGroup):
    mirror: BoolProperty(  # type: ignore
        name="Mirror",
        description="Defines how to layout the UV during UV generation.",
        default=False,
    )
    uv_group: StringProperty(  # type: ignore
        name="UV group",
        description=(
            "Objects with the same UV group can be mapped to the same spot on "
            "the texture if they have the same dimensions. Empty string means "
            "that the object doesn't belong to any UV group."),
        default="",
        maxlen=1024
    )
    is_bone: BoolProperty(  # type: ignore
        name="Export as bone",
        description=(
            "If true than this object will be exported as minecraft bone."),
        default=False,
    )
    inflate: FloatProperty(  # type: ignore
        name="Inflate",
        description="The inflate value of this object.",
        default=0.0
    )

class OBJECT_NusiqMcblendAnimationProperties(bpy.types.PropertyGroup):
    name: StringProperty(  # type: ignore
        name="Name",
        description="Name of the animation.", default="animation",
        maxlen=1024
    )
    single_frame: BoolProperty(  # type: ignore
        name="Single frame",
        description="Exports current pose as single frame animation",
        default=False,
    )
    anim_time_update: StringProperty(  # type: ignore
        name="anim_time_update",
        description="Adds anim_time_update value unless is left empty",
        default="",
        maxlen=1024
    )
    loop: BoolProperty(  # type: ignore
        name="Loop",
        description="Decides if animation should be looped",
        default=True,
    )
    frame_start: IntProperty(  # type: ignore
        name="Frame start",
        description="The first frame of the animation.",
        default=0,
        min=0
    )
    frame_current: IntProperty(  # type: ignore
        name="Frame current",
        description="The current frame of the animation.",
        default=100,
        min=0
    )
    frame_end: IntProperty(  # type: ignore
        name="Frame end",
        description="The last frame of the animation.",
        default=100,
        min=0
    )

class OBJECT_NusiqMcblendExporterProperties(bpy.types.PropertyGroup):
    '''Global properties used by Mcblend for user settings configuration.'''
    model_name: StringProperty(  # type: ignore
        name="",
        description="Name of the model",
        default="model",
        maxlen=1024
    )
    visible_bounds_offset: FloatVectorProperty(  # type: ignore
        name="Visible bounts offset",
        description="visible_bounds_offset of the model",
        default=(0.0, 0.0, 0.0)
    )
    visible_bounds_width: FloatProperty(  # type: ignore
        name="Visible bounds width",
        description="visible_bounds_width of the model",
        default=1.0
    )
    visible_bounds_height: FloatProperty(  # type: ignore
        name="Visible bounds height",
        description="visible_bounds_height of the model",
        default=1.0
    )
    texture_width: IntProperty(  # type: ignore
        name="",
        description="Minecraft UV parameter width.",
        default=64,
        min=1
    )
    texture_height: IntProperty(  # type: ignore
        name="",
        description=(
            "Minecraft UV parameter height. If you set it to 0 than the height"
            " of the texture will be picked automatically for you."
        ),
        default=64,
        min=1
    )
    texture_template_resolution: IntProperty(  # type: ignore
        name="Template texture resolution",
        description=(
            'Sets the resolution of the template texture.'
            'describes how many pixels on the image is represented by one '
            'texture_widht or texture_height unit in model definition. '
            'The value of 1 gives the standard minecraft texture '
            'resolution.'
        ),
        default=1,
        min=1,
        soft_max=5,
    )
    allow_expanding: BoolProperty(  # type: ignore
        name="Allow Texture Expanding",
        description="Allows expanding texture during texture generation.",
        default=True,
    )
    generate_texture: BoolProperty(  # type: ignore
        name="Generate texture",
        description="Generates texture during UV mapping.",
        default=True,
    )

# Panels
class OBJECT_UL_NusiqMcblendUVGroupList(bpy.types.UIList):
    def draw_item(
            self, context, layout, data, item, icon, active_data,
            active_propname):
        '''
        Drawing OBJECT_NusiqMcblendUvGroupProperties in a list.

        - `context` - the contexto of operator
        - `layout: bpy.types.UILayout` - layout in which the object is drawn
        - `data` - the RNA object containing the collection
        - `item` - the item currently drawn in the collection
        - `icon` - not used - "the "computed" icon for the item" (?)
        - `active_data` - the RNA object containing the active property for the
          collection.
        - `active_propname` - the name of the active property.

        For more info see the UI Template called: "UI List Simple".
        '''
        if self.layout_type in {'DEFAULT', 'COMPACT', 'CENTER'}:
            # No rename functionality:
            # layout.label(text=item.name, translate=False)

            # With rename functionality:
            layout.prop(item, "name", text="", emboss=False)

@dataclass
class _UIStackItem():
    '''Used for drawing some items in UVGroupPanel'''
    ui: Optional[bpy.types.UILayout]  # None if parent is collapsed
    depth: int

class OBJECT_PT_NusiqMcblendUVGroupPanel(bpy.types.Panel):
    '''Panel that lets edit UV groups'''
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_label = "Mcblend UV groups"

    def draw_colors(self, mask, mask_index: int, col: bpy.types.UILayout):
        box = col.box()
        row = box.row()
        row.label(text='Colors')
        op_props = row.operator(
            "object.nusiq_mcblend_add_uv_mask_color", text="", icon='ADD')
        op_props.mask_index = mask_index

        colors_len = len(mask.colors)
        for color_index, color in enumerate(mask.colors):
            row = box.row()
            row.prop(color, "color", text="")
            up_down_row = row.row(align=True)
            # Move down
            if color_index - 1 >= 0:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_color", icon='TRIA_UP', text='')
                op_props.mask_index = mask_index
                op_props.move_from = color_index
                op_props.move_to = color_index - 1
            # Move up
            if color_index + 1 < colors_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_color", icon='TRIA_DOWN', text='')
                op_props.mask_index = mask_index
                op_props.move_from = color_index
                op_props.move_to = color_index + 1
            # Delete button
            op_props = row.operator(
                "object.nusiq_mcblend_remove_uv_mask_color", icon='X', text='')
            op_props.mask_index = mask_index
            op_props.color_index = color_index

    def draw_stripes(self, mask, mask_index: int, col: bpy.types.UILayout):
        box = col.box()
        row = box.row()
        row.label(text='Stripes')
        op_props = row.operator(
            "object.nusiq_mcblend_add_uv_mask_stripe", text="", icon='ADD')
        op_props.mask_index = mask_index

        stripes_len = len(mask.stripes)
        for stripe_index, stripe in enumerate(mask.stripes):
            row = box.row()
            if (
                    mask.relative_boundries and
                    mask.mask_type != UvMaskTypes.GRADIENT_MASK.value):
                    # Gradient mask always uses absolute values
                row.prop(stripe, "width_relative")
            else:
                row.prop(stripe, "width")
            row.prop(stripe, "strength")
            up_down_row = row.row(align=True)
            # Move down
            if stripe_index - 1 >= 0:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_stripe", icon='TRIA_UP', text='')
                op_props.mask_index = mask_index
                op_props.move_from = stripe_index
                op_props.move_to = stripe_index - 1
            # Move up
            if stripe_index + 1 < stripes_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_stripe", icon='TRIA_DOWN', text='')
                op_props.mask_index = mask_index
                op_props.move_from = stripe_index
                op_props.move_to = stripe_index + 1
            # Delete button
            op_props = row.operator(
                "object.nusiq_mcblend_remove_uv_mask_stripe", icon='X', text='')
            op_props.mask_index = mask_index
            op_props.stripe_index = stripe_index

    def draw_mask_properties(
            self, mask, index: int, col: bpy.types.UILayout, *,
            colors=False, interpolate=False,
            normalize=False, p1p2=False, stripes=False,
            relative_boundries=False, expotent=False, strength=False,
            hard_edge=False, horizontal=False, seed=False,color=False,
            children=False, mode=False):
        if colors:
            self.draw_colors(mask, index, col)  # colors
        if interpolate:
            col.prop(mask, "interpolate")
        if normalize:
            col.prop(mask, "normalize")
        if p1p2:
            row = col.row()
            if mask.relative_boundries:
                row.prop(mask, "p1_relative")
                row = col.row()
                row.prop(mask, "p2_relative")
            else:
                row.prop(mask, "p1")
                row = col.row()
                row.prop(mask, "p2")
        if relative_boundries:
            col.prop(mask, "relative_boundries")
        if stripes:
            self.draw_stripes(mask, index, col)  # stripes
        if expotent:
            col.prop(mask, "expotent")
        if strength:
            col.row().prop(mask, "strength")
        if hard_edge:
            col.prop(mask, "hard_edge")
        if horizontal:
            col.prop(mask, "horizontal")
        if seed:
            row = col.row()
            row.prop(mask, "use_seed")
            if mask.use_seed:
                row.prop(mask, "seed")
        if color:
            col.prop(mask.color, "color")
        if mode:
            col.prop(mask, "mode")
        if children:
            col.prop(mask, "children")

    def draw_mask(
            self, mask, index: int, masks_len: int,
            ui_stack: List[_UIStackItem]):

        # If parent is collapsed dont draw anyghing
        if ui_stack[-1].ui is not None:
            col = ui_stack[-1].ui
            box = col.box()
            # box.scale_x = True
            col = box.column()
            row = col.row()
            if mask.ui_collapsed:
                row.prop(
                    mask, "ui_collapsed", text="", icon='DISCLOSURE_TRI_RIGHT',
                    emboss=False)
            else:
                row.prop(
                    mask, "ui_collapsed", text="", icon='DISCLOSURE_TRI_DOWN',
                    emboss=False)
            row.label(text=f'{mask.mask_type}')
            up_down_row = row.row(align=True)
            # Move down
            if index - 1 >= 0:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask", icon='TRIA_UP', text='')
                op_props.move_from = index
                op_props.move_to = index - 1
            # Move up
            if index + 1 < masks_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask", icon='TRIA_DOWN', text='')
                op_props.move_from = index
                op_props.move_to = index + 1
            # Delete button
            op_props = row.operator(
                "object.nusiq_mcblend_remove_uv_mask", icon='X', text='')
            op_props.target = index

            # Drawing the mask itself unless collapsed
            if not mask.ui_collapsed:
                if mask.mask_type == UvMaskTypes.COLOR_PALLETTE_MASK.value:
                    if len(ui_stack) > 1:
                        col.label(
                            text="This mask can't be put inside mix mask",
                            icon='ERROR')
                    else:
                        self.draw_mask_properties(
                            mask, index, col,
                            colors=True, interpolate=True, normalize=True)
                if mask.mask_type == UvMaskTypes.GRADIENT_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        p1p2=True, stripes=True, relative_boundries=True,
                        expotent=True)
                if mask.mask_type == UvMaskTypes.ELIPSE_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        p1p2=True, relative_boundries=True, expotent=True,
                        strength=True, hard_edge=True)
                if mask.mask_type == UvMaskTypes.RECTANGLE_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        p1p2=True, relative_boundries=True, expotent=True,
                        strength=True, hard_edge=True)
                if mask.mask_type == UvMaskTypes.STRIPES_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        stripes=True, relative_boundries=True, horizontal=True)
                if mask.mask_type == UvMaskTypes.RANDOM_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        strength=True, expotent=True, seed=True)
                if mask.mask_type == UvMaskTypes.COLOR_MASK.value:
                    self.draw_mask_properties(mask, index, col, color=True)
                if mask.mask_type == UvMaskTypes.MIX_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        children=True, strength=True, expotent=True,
                        mode=True)

        if mask.mask_type == UvMaskTypes.MIX_MASK.value:
            # mask.children+1 because it counts itself as a member
            if not mask.ui_collapsed:
                ui_stack.append(_UIStackItem(
                    col.box(), mask.children+1))
            else:
                ui_stack.append(_UIStackItem(
                    None, mask.children+1))

    def draw(self, context):
        col = self.layout.column(align=True)

        row = col.row()

        # Add group
        row.operator(
            "object.nusiq_mcblend_add_uv_group", text="New UV group",
            icon='ADD'
        )
        active_uv_group_id = bpy.context.scene.nusiq_mcblend_active_uv_group
        uv_groups = bpy.context.scene.nusiq_mcblend_uv_groups
        col.template_list(
            listtype_name="OBJECT_UL_NusiqMcblendUVGroupList",
            list_id="", dataptr=context.scene,
            propname="nusiq_mcblend_uv_groups",
            active_dataptr=context.scene,
            active_propname="nusiq_mcblend_active_uv_group")
        if active_uv_group_id < len(uv_groups):
            active_uv_group = uv_groups[active_uv_group_id]

            # Delete group
            operator_propeties = row.operator(
                "object.nusiq_mcblend_remove_uv_group",
                text="Delete this UV group", icon='X')
            # Select side
            row = col.row()
            row.label(text='Side:')
            row.prop(
                context.scene, "nusiq_mcblend_active_uv_groups_side",
                text="")
            col.separator()
            col.operator(
                'object.nusiq_mcblend_copy_uv_group_side',
                text='Copy current UV face', icon='DUPLICATE')
            
            # Add mask
            col.operator_menu_enum(
                "object.nusiq_mcblend_add_uv_mask", "mask_type",
                text="Add mask", icon="ADD")
            # Draw selected side
            sides = [
                active_uv_group.side1, active_uv_group.side2,
                active_uv_group.side3, active_uv_group.side4,
                active_uv_group.side5, active_uv_group.side6
            ]
            masks = sides[
                int(context.scene.nusiq_mcblend_active_uv_groups_side)]
            # Stack of UI items to draw in
            ui_stack: List[_UIStackItem] = [
                _UIStackItem(col, 0)]
            for i, mask in enumerate(masks):
                col.separator(factor=0.5)
                self.draw_mask(mask, i, len(masks), ui_stack)
                # Remove empty ui containers from top of ui_stack
                while len(ui_stack) > 1:  # Except the first one
                    ui_stack[-1].depth -= 1
                    if ui_stack[-1].depth <= 0:
                        ui_stack.pop()
                    else:
                        break

class OBJECT_PT_NusiqMcblendObjectPropertiesPanel(bpy.types.Panel):
    '''Panel with custom object properties (for meshes and empties)'''
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "Mcblend object properties"

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return (
                context.active_object.type == "MESH" or
                context.active_object.type == "EMPTY")

    def draw(self, context):
        col = self.layout.column(align=True)

        if context.mode == "OBJECT" and context.object != None:
            object_properties = context.object.nusiq_mcblend_object_properties
            uv_groups = context.scene.nusiq_mcblend_uv_groups
            col.prop(object_properties, "is_bone", text="Export as bone")
            if context.object.type == 'MESH':
                col.prop(object_properties, "mirror", text="Mirror")
                # TODO - add button to add/remove UV group
                if object_properties.uv_group != '':
                    col.label(text=f'UV Group: {object_properties.uv_group}')
                else:
                    col.label(text=f"This object does't have a UV group")
                col.prop(object_properties, "inflate", text="Inflate")

class OBJECT_PT_NusiqMcblendExportPanel(bpy.types.Panel):
    '''Panel used for configuration of exporting models'''
    # pylint: disable=C0116, W0613
    bl_label = "Export bedrock model"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        # col.prop(context.scene.nusiq_mcblend, "path", text="")
        col.prop(
            context.scene.nusiq_mcblend, "model_name", text="Name"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_width", text="Visible bounds width"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_height", text="Visible bounds height"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_offset", text="Visible bounds offset"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_export_operator", text="Export model"
        )

class OBJECT_PT_NusiqMcblendImportPanel(bpy.types.Panel):
    '''Panel used for configuration of importing models.'''
    # pylint: disable=C0116, W0613
    bl_label = "Import bedrock model"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)
        # col.prop(context.scene.nusiq_mcblend, "path", text="")
        self.layout.row().operator(
            "object.nusiq_mcblend_import_operator", text="Import model"
        )

class OBJECT_PT_NusiqMcblendExportAnimationPanel(bpy.types.Panel):
    '''Panel used for configuration of exporting animations.'''
    # pylint: disable=C0116, W0613
    bl_label = "Export bedrock animation"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        col = self.layout.column(align=True)

        row = col.row()
        row.operator(
            "object.nusiq_mcblend_add_animation", text="New animation"
        )

        active_anim_id = bpy.context.scene.nusiq_mcblend_active_animation
        anims = bpy.context.scene.nusiq_mcblend_animations
        if active_anim_id < len(anims):
            row.operator(
                "object.nusiq_mcblend_remove_animation", text="Remove this animation"
            )
            col.operator_menu_enum(
                "object.nusiq_mcblend_list_animations", "animations_enum",
                text="Select animation"
            )

            active_anim = anims[active_anim_id]
            col.prop(active_anim, "name", text="Name")
            col.prop(active_anim, "single_frame", text="Export as pose")
            if active_anim.single_frame:
                col.prop(bpy.context.scene, "frame_current", text="Frame")
            else:
                col.prop(active_anim, "loop", text="Loop")
                col.prop(active_anim, "anim_time_update", text="anim_time_update")
                col.prop(bpy.context.scene, "frame_start", text="Frame start")
                col.prop(bpy.context.scene, "frame_end", text="Frame end")
                
            col.operator(
                "object.nusiq_mcblend_export_animation_operator", text="Export animation"
            )

class OBJECT_PT_NusiqMcblendSetUvsPanel(bpy.types.Panel):
    '''Panel  used for Minecraft UV maping and its configuration.'''
    # pylint: disable=C0116, W0613
    bl_label = "Set bedrock UVs"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(
            context.scene.nusiq_mcblend, "texture_width", text="Texture width"
        )
        col.prop(
            context.scene.nusiq_mcblend, "texture_height", text="Texture height"
        )
        col.prop(
            context.scene.nusiq_mcblend, "allow_expanding",
            text="Allow texture expanding"
        )
        col.prop(
            context.scene.nusiq_mcblend, "generate_texture",
            text="Generate Texture"
        )
        if context.scene.nusiq_mcblend.generate_texture:
            col.prop(
                context.scene.nusiq_mcblend, "texture_template_resolution",
                text="Template resolution"
            )
        self.layout.row().operator(
            "object.nusiq_mcblend_map_uv_operator", text="Set minecraft UVs"
        )

class OBJECT_PT_NusiqMcblendOperatorsPanel(bpy.types.Panel):
    '''
    Panel that gives the user access to various operators used by Mcblend.
    '''
    # pylint: disable=C0116, W0613
    bl_label = "Operators"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        col = self.layout.column()
        col.operator(
            "object.nusiq_mcblend_toggle_mirror_operator",
            text="Toggle mirror for UV mapping"
        )
        col.operator(
            "object.nusiq_mcblend_uv_group_operator",
            text="Set the UV group"
        )
        col.operator(
            "object.nusiq_mcblend_clear_uv_group_operator",
            text="Clear UV group"
        )
        col.operator(
            "object.nusiq_mcblend_toggle_is_bone_operator",
            text="Toggle export as bones"
        )
        col.operator(
            "object.nusiq_mcblend_set_inflate_operator",
            text="Inflate"
        )
        col.operator(
            "object.nusiq_mcblend_round_dimensions_operator",
            text="Round dimensions"
        )
