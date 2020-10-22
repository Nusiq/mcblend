'''
This module contains all of the panels for mcblend GUI.
'''
# don't import future annotations Blender needs that
from typing import List, Optional
from dataclasses import dataclass

import bpy
from bpy.props import (
    StringProperty, IntProperty, BoolProperty, FloatProperty,
    FloatVectorProperty, CollectionProperty, EnumProperty, PointerProperty,
    IntVectorProperty
)
from .operator_func.texture_generator import (
    list_mask_types_as_blender_enum, UvMaskTypes,
    list_mix_mask_modes_as_blender_enum)

# GUI
# UV-groups names list
class OBJECT_UL_NusiqMcblendUVGroupList(bpy.types.UIList):
    '''GUI item used for drawing list of names of UV-groups.'''
    def draw_item(
            self, context, layout, data, item, icon, active_data,
            active_propname):
        '''
        Drawing OBJECT_NusiqMcblendUvGroupProperties in a list.

        - `context` - the contexts of operator
        - `layout: bpy.types.UILayout` - layout in which the object is drawn
        - `data` - the RNA object containing the collection
        - `item` - the item currently drawn in the collection
        - `icon` - not used - "the "computed" icon for the item" (?)
        - `active_data` - the RNA object containing the active property for the
          collection.
        - `active_propname` - the name of the active property.

        For more info see the UI Template called: "UI List Simple".
        '''
        # pylint: disable=arguments-differ, unused-argument
        if self.layout_type in {'DEFAULT', 'COMPACT', 'CENTER'}:
            # No rename functionality:
            # layout.label(text=item.name, translate=False)

            # With rename functionality:
            layout.prop(item, "name", text="", emboss=False)

# UV-group panel
@dataclass
class _UIStackItem():
    '''
    Object used in OBJECT_PT_NusiqMcblendUVGroupPanel for saving the
    information about nested UV-groups in stack data structure.
    '''
    ui: Optional[bpy.types.UILayout]  # None if parent is collapsed
    depth: int

class OBJECT_PT_NusiqMcblendUVGroupPanel(bpy.types.Panel):
    '''Panel used for editing UV-groups.'''
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'
    bl_label = "Mcblend UV groups"

    def draw_colors(self, mask, mask_index: int, col: bpy.types.UILayout):
        '''Draws colors of UV-mask.'''
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
                    "object.nusiq_mcblend_move_uv_mask_color", icon='TRIA_UP',
                    text='')
                op_props.mask_index = mask_index
                op_props.move_from = color_index
                op_props.move_to = color_index - 1
            # Move up
            if color_index + 1 < colors_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_color", icon='TRIA_DOWN',
                    text='')
                op_props.mask_index = mask_index
                op_props.move_from = color_index
                op_props.move_to = color_index + 1
            # Delete button
            op_props = row.operator(
                "object.nusiq_mcblend_remove_uv_mask_color", icon='X', text='')
            op_props.mask_index = mask_index
            op_props.color_index = color_index

    def draw_stripes(self, mask, mask_index: int, col: bpy.types.UILayout):
        '''Draws stripes of UV-mask.'''
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
                    mask.relative_boundaries and
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
                    "object.nusiq_mcblend_move_uv_mask_stripe", icon='TRIA_UP',
                    text='')
                op_props.mask_index = mask_index
                op_props.move_from = stripe_index
                op_props.move_to = stripe_index - 1
            # Move up
            if stripe_index + 1 < stripes_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask_stripe", icon='TRIA_DOWN',
                    text='')
                op_props.mask_index = mask_index
                op_props.move_from = stripe_index
                op_props.move_to = stripe_index + 1
            # Delete button
            op_props = row.operator(
                "object.nusiq_mcblend_remove_uv_mask_stripe", icon='X',
                text='')
            op_props.mask_index = mask_index
            op_props.stripe_index = stripe_index

    def draw_mask_properties(
            self, mask, index: int, col: bpy.types.UILayout, *,
            colors=False, interpolate=False,
            normalize=False, p1p2=False, stripes=False,
            relative_boundaries=False, expotent=False, strength=False,
            hard_edge=False, horizontal=False, seed=False,color=False,
            children=False, mode=False):
        '''Draws properties of UV-mask.'''
        if colors:
            self.draw_colors(mask, index, col)  # colors
        if interpolate:
            col.prop(mask, "interpolate")
        if normalize:
            col.prop(mask, "normalize")
        if p1p2:
            row = col.row()
            if mask.relative_boundaries:
                row.prop(mask, "p1_relative")
                row = col.row()
                row.prop(mask, "p2_relative")
            else:
                row.prop(mask, "p1")
                row = col.row()
                row.prop(mask, "p2")
        if relative_boundaries:
            col.prop(mask, "relative_boundaries")
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
        '''
        Draws whole UV-mask gui with additional GUI items for navigation
        between masks like buttons for moving and removing masks.
        '''
        col = None
        # If parent is collapsed don't draw anything
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
                    "object.nusiq_mcblend_move_uv_mask", icon='TRIA_UP',
                    text='')
                op_props.move_from = index
                op_props.move_to = index - 1
            # Move up
            if index + 1 < masks_len:
                op_props = up_down_row.operator(
                    "object.nusiq_mcblend_move_uv_mask", icon='TRIA_DOWN',
                    text='')
                op_props.move_from = index
                op_props.move_to = index + 1
            # Hide button
            if mask.ui_hidden:
                row.prop(
                    mask, "ui_hidden", text="", icon='HIDE_ON',
                    emboss=False)
            else:
                row.prop(
                    mask, "ui_hidden", text="", icon='HIDE_OFF',
                    emboss=False)
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
                        p1p2=True, stripes=True, relative_boundaries=True,
                        expotent=True)
                if mask.mask_type == UvMaskTypes.ELLIPSE_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        p1p2=True, relative_boundaries=True, expotent=True,
                        strength=True, hard_edge=True)
                if mask.mask_type == UvMaskTypes.RECTANGLE_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        p1p2=True, relative_boundaries=True, expotent=True,
                        strength=True, hard_edge=True)
                if mask.mask_type == UvMaskTypes.STRIPES_MASK.value:
                    self.draw_mask_properties(
                        mask, index, col,
                        stripes=True, relative_boundaries=True, horizontal=True)
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

        if mask.mask_type == UvMaskTypes.MIX_MASK.value and col is not None:
            # mask.children+1 because it counts itself as a member
            if not mask.ui_collapsed:
                ui_stack.append(_UIStackItem(
                    col.box(), mask.children+1))
            else:
                ui_stack.append(_UIStackItem(
                    None, mask.children+1))

    def draw(self, context):
        '''Draws whole UV-group panel.'''
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
            row.operator(
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

# Custom object properties panel
class OBJECT_PT_NusiqMcblendObjectPropertiesPanel(bpy.types.Panel):
    '''Panel used for editing custom model object properties.'''
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
        return False

    def draw(self, context):
        col = self.layout.column(align=True)

        if context.mode == "OBJECT" and context.object is not None:
            object_properties = context.object.nusiq_mcblend_object_properties
            col.prop(object_properties, "is_bone", text="Export as bone")
            if context.object.type == 'MESH':
                col.prop(object_properties, "mirror", text="Mirror")
                # TODO - add button to add/remove UV group
                if object_properties.uv_group != '':
                    col.label(text=f'UV Group: {object_properties.uv_group}')
                else:
                    col.label(text="This object doesn't have a UV group")
                col.prop(object_properties, "inflate", text="Inflate")

# Model export panel
class OBJECT_PT_NusiqMcblendExportPanel(bpy.types.Panel):
    '''
    Panel used for launching the model export operator and changing its
    settings.
    '''
    # pylint: disable=unused-argument
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
            context.scene.nusiq_mcblend, "visible_bounds_width",
            text="Visible bounds width"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_height",
            text="Visible bounds height"
        )
        col.prop(
            context.scene.nusiq_mcblend, "visible_bounds_offset",
            text="Visible bounds offset"
        )
        self.layout.row().operator(
            "object.nusiq_mcblend_export_operator", text="Export model"
        )

# Model import panel
class OBJECT_PT_NusiqMcblendImportPanel(bpy.types.Panel):
    '''Panel used for launching the model import operator.'''
    # pylint: disable=unused-argument
    bl_label = "Import bedrock model"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        self.layout.row().operator(
            "object.nusiq_mcblend_import_operator", text="Import model"
        )

# Animation export panel
class OBJECT_PT_NusiqMcblendExportAnimationPanel(bpy.types.Panel):
    '''
    Panel used launching the animation export operator and changing its
    settings.
    '''
    # pylint: disable=unused-argument
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
                "object.nusiq_mcblend_remove_animation",
                text="Remove this animation"
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
                col.prop(active_anim, "anim_time_update",
                    text="anim_time_update")
                col.prop(bpy.context.scene, "frame_start", text="Frame start")
                col.prop(bpy.context.scene, "frame_end", text="Frame end")

            col.operator(
                "object.nusiq_mcblend_export_animation_operator",
                text="Export animation")

# UV-mapper panel
class OBJECT_PT_NusiqMcblendSetUvsPanel(bpy.types.Panel):
    '''
    Panel used for launching the UV-mapping operator and changing its settings.
    '''
    # pylint: disable=unused-argument
    bl_label = "Set bedrock UVs"
    bl_category = "Mcblend"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(
            context.scene.nusiq_mcblend, "texture_width", text="Texture width")
        col.prop(
            context.scene.nusiq_mcblend, "texture_height",
            text="Texture height")
        col.prop(
            context.scene.nusiq_mcblend, "allow_expanding",
            text="Allow texture expanding")
        col.prop(
            context.scene.nusiq_mcblend, "generate_texture",
            text="Generate Texture")
        if context.scene.nusiq_mcblend.generate_texture:
            col.prop(
                context.scene.nusiq_mcblend, "texture_template_resolution",
                text="Template resolution")
        self.layout.row().operator(
            "object.nusiq_mcblend_map_uv_operator", text="Set minecraft UVs")

# "Other" operators panel
class OBJECT_PT_NusiqMcblendOperatorsPanel(bpy.types.Panel):
    '''
    Panel that gives the user access to various operators used by Mcblend.
    '''
    # pylint: disable=unused-argument
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
