import bpy


class NUSIQ_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export bedrock model"
    bl_category = "Export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("nusiq.main_operator", text="Export bedrock model.")
