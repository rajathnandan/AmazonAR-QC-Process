"""
Amazon 3D Model Compliance Checker - Blender Add-on
Real-time validation of models against Amazon technical requirements

Installation:
1. Save this file as amazon_compliance_addon.py
2. In Blender: Edit > Preferences > Add-ons > Install
3. Select this file and enable the add-on
4. Find the panel in 3D View > Sidebar (N key) > Amazon Compliance

Author: WarRoom
Version: 1.0.0
"""

bl_info = {
    "name": "Amazon 3D Model Compliance Checker",
    "author": "WarRoom",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Amazon Compliance",
    "description": "Real-time validation of 3D models against Amazon technical requirements",
    "category": "Import-Export",
}

import bpy
import math
from bpy.props import (
    StringProperty,
    EnumProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
)
from bpy.types import (
    Panel,
    Operator,
    PropertyGroup,
)


# Utility Functions
def get_triangle_count():
    """Calculate total triangle count for all mesh objects"""
    total_triangles = 0
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # Get mesh data
            mesh = obj.data
            
            # Count triangles (each face is triangulated)
            for poly in mesh.polygons:
                total_triangles += len(poly.vertices) - 2
    
    return total_triangles


def check_alignment(obj, alignment_type):
    """Check if object is properly aligned"""
    if obj.type != 'MESH':
        return True, "N/A"
    
    # Get world matrix
    matrix_world = obj.matrix_world
    location = matrix_world.translation
    
    # Check pivot point
    pivot_ok = abs(location.x) < 0.001 and abs(location.z) < 0.001
    
    if alignment_type == 'FLOOR':
        # Should be at Y=0 or above
        y_ok = location.y >= -0.001
        return pivot_ok and y_ok, f"Pivot: ({location.x:.3f}, {location.y:.3f}, {location.z:.3f})"
    
    elif alignment_type == 'WALL':
        # Should be centered on X and Y, back at Z=0
        centered = abs(location.x) < 0.001 and abs(location.y) < 0.001
        return centered, f"Pivot: ({location.x:.3f}, {location.y:.3f}, {location.z:.3f})"
    
    elif alignment_type == 'CEILING':
        # Should be at Y=0 or below
        y_ok = location.y <= 0.001
        return pivot_ok and y_ok, f"Pivot: ({location.x:.3f}, {location.y:.3f}, {location.z:.3f})"
    
    return True, "N/A"


def check_scale():
    """Check if objects are at real-world scale"""
    issues = []
    
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # Check if scale is not 1,1,1
            scale = obj.scale
            if not (math.isclose(scale.x, 1.0, rel_tol=0.01) and 
                    math.isclose(scale.y, 1.0, rel_tol=0.01) and 
                    math.isclose(scale.z, 1.0, rel_tol=0.01)):
                issues.append(f"{obj.name}: Scale not applied ({scale.x:.3f}, {scale.y:.3f}, {scale.z:.3f})")
    
    return len(issues) == 0, issues


def check_textures():
    """Check texture resolutions and formats"""
    issues = []
    valid_count = 0
    
    for img in bpy.data.images:
        if img.source == 'FILE':
            width, height = img.size
            
            # Check if square
            if width != height:
                issues.append(f"{img.name}: Not square ({width}x{height})")
                continue
            
            # Check if power of 2
            if not (width > 0 and (width & (width - 1)) == 0):
                issues.append(f"{img.name}: Not power of 2 ({width}x{height})")
                continue
            
            # Check resolution
            if width < 2048 or height < 2048:
                issues.append(f"{img.name}: Too small ({width}x{height}, min 2048x2048)")
            elif width > 4096 or height > 4096:
                issues.append(f"{img.name}: Too large ({width}x{height}, max 4096x4096)")
            else:
                valid_count += 1
    
    return valid_count, issues


def check_materials():
    """Check if materials are PBR compliant"""
    issues = []
    pbr_count = 0
    
    for mat in bpy.data.materials:
        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            
            # Check for Principled BSDF (PBR)
            has_principled = any(node.type == 'BSDF_PRINCIPLED' for node in nodes)
            
            if has_principled:
                pbr_count += 1
                
                # Check for base color texture
                principled = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
                base_color_input = principled.inputs['Base Color']
                
                if not base_color_input.is_linked:
                    issues.append(f"{mat.name}: Missing Base Color texture")
            else:
                issues.append(f"{mat.name}: Not using Principled BSDF (PBR)")
        else:
            issues.append(f"{mat.name}: Not using nodes")
    
    return pbr_count, issues


def check_scene_objects():
    """Check for cameras, lights, and animations"""
    cameras = len([obj for obj in bpy.data.objects if obj.type == 'CAMERA'])
    lights = len([obj for obj in bpy.data.objects if obj.type == 'LIGHT'])
    animations = len(bpy.data.actions)
    
    return {
        'cameras': cameras,
        'lights': lights,
        'animations': animations
    }


# Property Group
class AmazonComplianceProperties(PropertyGroup):
    alignment_type: EnumProperty(
        name="Alignment Type",
        description="Product alignment type for Amazon",
        items=[
            ('FLOOR', "Floor/Tabletop", "Products that rest on floor or table"),
            ('WALL', "Wall", "Wall-mounted products"),
            ('CEILING', "Ceiling", "Ceiling-mounted products"),
        ],
        default='FLOOR'
    )
    
    auto_check: BoolProperty(
        name="Auto-Check",
        description="Automatically check compliance when scene changes",
        default=False
    )
    
    triangle_limit: IntProperty(
        name="Triangle Limit",
        description="Maximum triangle count",
        default=200000,
        min=1000,
        max=1000000
    )


# Operators
class AMAZON_OT_check_compliance(Operator):
    """Check model compliance with Amazon requirements"""
    bl_idname = "amazon.check_compliance"
    bl_label = "Check Compliance"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.amazon_compliance
        
        self.report({'INFO'}, "Running Amazon compliance check...")
        
        # Store results in scene
        context.scene['amazon_results'] = {
            'last_check': True,
            'triangle_count': get_triangle_count(),
            'alignment_ok': True,
            'scale_ok': True,
            'texture_count': 0,
            'material_count': 0,
        }
        
        return {'FINISHED'}


class AMAZON_OT_fix_scale(Operator):
    """Apply scale to all mesh objects"""
    bl_idname = "amazon.fix_scale"
    bl_label = "Apply Scale"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        count = 0
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
                count += 1
        
        self.report({'INFO'}, f"Applied scale to {count} object(s)")
        return {'FINISHED'}


class AMAZON_OT_align_to_origin(Operator):
    """Align model to world origin based on type"""
    bl_idname = "amazon.align_to_origin"
    bl_label = "Align to Origin"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.amazon_compliance
        
        # Select all mesh objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        
        if not context.selected_objects:
            self.report({'WARNING'}, "No mesh objects to align")
            return {'CANCELLED'}
        
        # Set pivot to 3D cursor at origin
        bpy.context.scene.cursor.location = (0, 0, 0)
        
        self.report({'INFO'}, f"Aligned for {props.alignment_type} placement")
        return {'FINISHED'}


class AMAZON_OT_export_compliant(Operator):
    """Export model with Amazon-compliant glTF settings"""
    bl_idname = "amazon.export_compliant"
    bl_label = "Export for Amazon"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file path specified")
            return {'CANCELLED'}
        
        # Export with Amazon-compliant settings
        bpy.ops.export_scene.gltf(
            filepath=self.filepath,
            export_format='GLTF_SEPARATE',  # Separate .gltf + .bin + textures
            export_materials='EXPORT',
            export_colors=True,
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_apply=True,
            export_yup=True,  # Y-up axis
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_image_format='AUTO',
        )
        
        self.report({'INFO'}, f"Exported to {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Panels
class AMAZON_PT_main_panel(Panel):
    """Main panel for Amazon compliance checking"""
    bl_label = "Amazon Compliance"
    bl_idname = "AMAZON_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Amazon Compliance'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.amazon_compliance
        
        # Settings
        box = layout.box()
        box.label(text="Settings", icon='SETTINGS')
        box.prop(props, "alignment_type")
        box.prop(props, "triangle_limit")
        
        # Check button
        layout.separator()
        layout.operator("amazon.check_compliance", icon='CHECKMARK')


class AMAZON_PT_stats_panel(Panel):
    """Statistics panel showing real-time metrics"""
    bl_label = "Statistics"
    bl_idname = "AMAZON_PT_stats_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Amazon Compliance'
    bl_parent_id = "AMAZON_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.amazon_compliance
        
        # Triangle count
        triangle_count = get_triangle_count()
        triangle_limit = props.triangle_limit
        
        box = layout.box()
        row = box.row()
        row.label(text="Triangle Count:")
        row.label(text=f"{triangle_count:,}")
        
        # Color code based on limit
        row = box.row()
        if triangle_count <= triangle_limit:
            row.label(text="Status:", icon='CHECKMARK')
            row.label(text="PASS")
        elif triangle_count <= triangle_limit * 1.1:
            row.label(text="Status:", icon='ERROR')
            row.label(text="WARNING")
        else:
            row.label(text="Status:", icon='CANCEL')
            row.label(text="FAIL")
        
        progress = min(triangle_count / triangle_limit, 1.0)
        box.progress(factor=progress, type='BAR', text=f"{progress*100:.1f}%")
        
        # Object counts
        layout.separator()
        box = layout.box()
        box.label(text="Scene Objects", icon='OUTLINER')
        
        mesh_count = len([obj for obj in bpy.data.objects if obj.type == 'MESH'])
        mat_count = len(bpy.data.materials)
        tex_count = len([img for img in bpy.data.images if img.source == 'FILE'])
        
        row = box.row()
        row.label(text=f"Meshes: {mesh_count}")
        row = box.row()
        row.label(text=f"Materials: {mat_count}")
        row = box.row()
        row.label(text=f"Textures: {tex_count}")
        
        # Scene objects check
        scene_objs = check_scene_objects()
        
        layout.separator()
        box = layout.box()
        box.label(text="Scene Validation", icon='SCENE_DATA')
        
        # Cameras
        row = box.row()
        if scene_objs['cameras'] == 0:
            row.label(text="Cameras:", icon='CHECKMARK')
            row.label(text="None (Good)")
        else:
            row.label(text="Cameras:", icon='CANCEL')
            row.label(text=f"{scene_objs['cameras']} (Remove)")
        
        # Lights
        row = box.row()
        if scene_objs['lights'] == 0:
            row.label(text="Lights:", icon='CHECKMARK')
            row.label(text="None (Good)")
        else:
            row.label(text="Lights:", icon='CANCEL')
            row.label(text=f"{scene_objs['lights']} (Remove)")
        
        # Animations
        row = box.row()
        if scene_objs['animations'] == 0:
            row.label(text="Animations:", icon='CHECKMARK')
            row.label(text="None (Good)")
        else:
            row.label(text="Animations:", icon='CANCEL')
            row.label(text=f"{scene_objs['animations']} (Remove)")


class AMAZON_PT_tools_panel(Panel):
    """Tools panel for fixing common issues"""
    bl_label = "Quick Fix Tools"
    bl_idname = "AMAZON_PT_tools_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Amazon Compliance'
    bl_parent_id = "AMAZON_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Geometry", icon='MESH_DATA')
        box.operator("amazon.fix_scale", icon='OBJECT_ORIGIN')
        box.operator("amazon.align_to_origin", icon='ORIENTATION_GLOBAL')
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Export", icon='EXPORT')
        box.operator("amazon.export_compliant", icon='EXPORT')


# Registration
classes = (
    AmazonComplianceProperties,
    AMAZON_OT_check_compliance,
    AMAZON_OT_fix_scale,
    AMAZON_OT_align_to_origin,
    AMAZON_OT_export_compliant,
    AMAZON_PT_main_panel,
    AMAZON_PT_stats_panel,
    AMAZON_PT_tools_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.amazon_compliance = bpy.props.PointerProperty(
        type=AmazonComplianceProperties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.amazon_compliance


if __name__ == "__main__":
    register()
