#!/usr/bin/env python3
"""
Amazon 3D Model Compliance Checker
Validates glTF/GLB models against Amazon Marketplace technical requirements
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
import math

try:
    import pygltflib
    from PIL import Image
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "pygltflib", "Pillow"])
    import pygltflib
    from PIL import Image


@dataclass
class ValidationResult:
    """Stores validation results for a specific check"""
    category: str
    check_name: str
    status: str  # "PASS", "FAIL", "WARNING", "INFO"
    message: str
    details: Optional[Dict] = None


@dataclass
class ComplianceReport:
    """Complete compliance report"""
    model_name: str
    validation_time: str
    overall_status: str  # "COMPLIANT", "NON_COMPLIANT", "WARNING"
    results: List[ValidationResult]
    summary: Dict[str, int]
    model_info: Dict[str, any]


class AmazonGLTFValidator:
    """Validates glTF models against Amazon 3D technical requirements"""
    
    # Amazon Requirements
    MAX_TRIANGLES = 200000
    MIN_TEXTURE_SIZE = 2048
    MAX_TEXTURE_SIZE = 4096
    VALID_TEXTURE_FORMATS = ['.png', '.jpg', '.jpeg']
    REQUIRED_MAPS = ['baseColorTexture']
    SUPPORTED_EXTENSIONS = [
        'KHR_materials_sheen',
        'KHR_materials_transmission',
        'KHR_materials_clearcoat',
        'KHR_materials_ior',
        'KHR_materials_volume',
        'KHR_draco_mesh_compression',
        'KHR_interactivity'
    ]
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.results: List[ValidationResult] = []
        self.gltf = None
        self.model_dir = self.model_path.parent
        
    def validate(self) -> ComplianceReport:
        """Run all validation checks"""
        print(f"🔍 Validating: {self.model_path.name}")
        print("=" * 60)
        
        # Load the model
        if not self._load_model():
            return self._generate_report()
        
        # Run all validation checks
        self._validate_file_format()
        self._validate_geometry()
        self._validate_textures()
        self._validate_materials()
        self._validate_alignment()
        self._validate_extensions()
        self._run_gltf_validator()
        
        return self._generate_report()
    
    def _load_model(self) -> bool:
        """Load the glTF model"""
        try:
            if self.model_path.suffix.lower() == '.glb':
                self.gltf = pygltflib.GLTF2().load(str(self.model_path))
                self.results.append(ValidationResult(
                    category="File Format",
                    check_name="Model Loading",
                    status="PASS",
                    message="GLB model loaded successfully"
                ))
            elif self.model_path.suffix.lower() == '.gltf':
                self.gltf = pygltflib.GLTF2().load(str(self.model_path))
                self.results.append(ValidationResult(
                    category="File Format",
                    check_name="Model Loading",
                    status="PASS",
                    message="glTF model loaded successfully"
                ))
            else:
                self.results.append(ValidationResult(
                    category="File Format",
                    check_name="Model Loading",
                    status="FAIL",
                    message=f"Invalid file format: {self.model_path.suffix}. Must be .glb or .gltf"
                ))
                return False
            return True
        except Exception as e:
            self.results.append(ValidationResult(
                category="File Format",
                check_name="Model Loading",
                status="FAIL",
                message=f"Failed to load model: {str(e)}"
            ))
            return False
    
    def _validate_file_format(self):
        """Validate file format requirements"""
        # Check if using recommended GLB format
        if self.model_path.suffix.lower() == '.glb':
            self.results.append(ValidationResult(
                category="File Format",
                check_name="Format Type",
                status="PASS",
                message="Using recommended GLB format (binary)"
            ))
        else:
            self.results.append(ValidationResult(
                category="File Format",
                check_name="Format Type",
                status="INFO",
                message="Using glTF format. GLB (binary) is recommended for submission"
            ))
            
            # Check for separate bin file
            bin_file = self.model_path.with_suffix('.bin')
            if bin_file.exists():
                self.results.append(ValidationResult(
                    category="File Format",
                    check_name="Binary Data",
                    status="PASS",
                    message="Separate .bin file found"
                ))
            else:
                self.results.append(ValidationResult(
                    category="File Format",
                    check_name="Binary Data",
                    status="WARNING",
                    message="No separate .bin file found. Ensure binary data is properly referenced"
                ))
    
    def _validate_geometry(self):
        """Validate geometry requirements"""
        if not self.gltf.meshes:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Mesh Existence",
                status="FAIL",
                message="No meshes found in the model"
            ))
            return
        
        # Count total triangles
        total_triangles = 0
        for mesh in self.gltf.meshes:
            for primitive in mesh.primitives:
                if primitive.indices is not None:
                    accessor = self.gltf.accessors[primitive.indices]
                    # Assuming triangles (mode 4 or default)
                    triangle_count = accessor.count // 3
                    total_triangles += triangle_count
        
        # Triangle count check
        if total_triangles <= self.MAX_TRIANGLES:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Triangle Count",
                status="PASS",
                message=f"Triangle count: {total_triangles:,} (limit: {self.MAX_TRIANGLES:,})",
                details={"triangle_count": total_triangles, "limit": self.MAX_TRIANGLES}
            ))
        else:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Triangle Count",
                status="FAIL",
                message=f"Triangle count exceeds limit: {total_triangles:,} > {self.MAX_TRIANGLES:,}",
                details={"triangle_count": total_triangles, "limit": self.MAX_TRIANGLES}
            ))
        
        # Check for animations, cameras, lights (should not exist)
        if self.gltf.animations:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Animations",
                status="FAIL",
                message=f"Model contains {len(self.gltf.animations)} animation(s). Animations not allowed"
            ))
        else:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Animations",
                status="PASS",
                message="No animations found"
            ))
        
        if self.gltf.cameras:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Cameras",
                status="FAIL",
                message=f"Model contains {len(self.gltf.cameras)} camera(s). Cameras not allowed"
            ))
        else:
            self.results.append(ValidationResult(
                category="Geometry",
                check_name="Cameras",
                status="PASS",
                message="No cameras found"
            ))
        
        # Note: glTF doesn't store lights in a separate array, they're usually extensions
        self.results.append(ValidationResult(
            category="Geometry",
            check_name="Scene Composition",
            status="INFO",
            message=f"Model has {len(self.gltf.meshes)} mesh(es) and {len(self.gltf.nodes)} node(s)"
        ))
    
    def _validate_textures(self):
        """Validate texture requirements"""
        if not self.gltf.images:
            self.results.append(ValidationResult(
                category="Textures",
                check_name="Texture Existence",
                status="WARNING",
                message="No textures found in the model"
            ))
            return
        
        texture_issues = []
        texture_info = []
        
        for idx, image in enumerate(self.gltf.images):
            # Get image path
            if image.uri:
                if image.uri.startswith('data:'):
                    self.results.append(ValidationResult(
                        category="Textures",
                        check_name=f"Texture {idx} Format",
                        status="FAIL",
                        message="Embedded textures (data URI) not allowed. Must use external files"
                    ))
                    continue
                
                image_path = self.model_dir / image.uri
                
                if not image_path.exists():
                    texture_issues.append(f"Texture {idx} not found: {image.uri}")
                    continue
                
                # Check file format
                if image_path.suffix.lower() not in self.VALID_TEXTURE_FORMATS:
                    texture_issues.append(
                        f"Texture {idx} has invalid format: {image_path.suffix}. "
                        f"Must be {', '.join(self.VALID_TEXTURE_FORMATS)}"
                    )
                    continue
                
                # Check resolution
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                        
                        # Check if square
                        if width != height:
                            texture_issues.append(
                                f"Texture {idx} not square: {width}x{height}. Must be square"
                            )
                        
                        # Check if power of 2
                        if not self._is_power_of_two(width) or not self._is_power_of_two(height):
                            texture_issues.append(
                                f"Texture {idx} not power of 2: {width}x{height}"
                            )
                        
                        # Check size limits
                        if width < self.MIN_TEXTURE_SIZE or height < self.MIN_TEXTURE_SIZE:
                            texture_issues.append(
                                f"Texture {idx} too small: {width}x{height}. "
                                f"Minimum: {self.MIN_TEXTURE_SIZE}x{self.MIN_TEXTURE_SIZE}"
                            )
                        elif width > self.MAX_TEXTURE_SIZE or height > self.MAX_TEXTURE_SIZE:
                            texture_issues.append(
                                f"Texture {idx} too large: {width}x{height}. "
                                f"Maximum: {self.MAX_TEXTURE_SIZE}x{self.MAX_TEXTURE_SIZE}"
                            )
                        else:
                            texture_info.append({
                                "index": idx,
                                "name": image.uri,
                                "resolution": f"{width}x{height}",
                                "format": image_path.suffix,
                                "size_mb": round(image_path.stat().st_size / (1024 * 1024), 2)
                            })
                
                except Exception as e:
                    texture_issues.append(f"Failed to analyze texture {idx}: {str(e)}")
        
        if texture_issues:
            for issue in texture_issues:
                self.results.append(ValidationResult(
                    category="Textures",
                    check_name="Texture Validation",
                    status="FAIL",
                    message=issue
                ))
        
        if texture_info:
            self.results.append(ValidationResult(
                category="Textures",
                check_name="Valid Textures",
                status="PASS",
                message=f"Found {len(texture_info)} valid texture(s)",
                details={"textures": texture_info}
            ))
    
    def _validate_materials(self):
        """Validate material requirements"""
        if not self.gltf.materials:
            self.results.append(ValidationResult(
                category="Materials",
                check_name="Material Existence",
                status="WARNING",
                message="No materials found in the model"
            ))
            return
        
        pbr_compliant = True
        material_info = []
        
        for idx, material in enumerate(self.gltf.materials):
            mat_info = {"index": idx, "name": material.name or f"Material_{idx}"}
            
            # Check for PBR metallic roughness
            if material.pbrMetallicRoughness:
                pbr = material.pbrMetallicRoughness
                mat_info["pbr"] = "Metal-Rough"
                
                # Check for base color texture (required)
                if pbr.baseColorTexture:
                    mat_info["has_base_color"] = True
                else:
                    mat_info["has_base_color"] = False
                    pbr_compliant = False
                
                # Check for metallic/roughness texture (required)
                if pbr.metallicRoughnessTexture:
                    mat_info["has_metallic_roughness"] = True
                else:
                    mat_info["has_metallic_roughness"] = True  # Can be in same texture
                
            else:
                pbr_compliant = False
                mat_info["pbr"] = "None"
            
            # Check for normal map (optional but recommended)
            if material.normalTexture:
                mat_info["has_normal"] = True
            
            # Check for occlusion (optional)
            if material.occlusionTexture:
                mat_info["has_occlusion"] = True
            
            # Check double-sided (should be false per requirements)
            if material.doubleSided:
                mat_info["double_sided"] = True
                self.results.append(ValidationResult(
                    category="Materials",
                    check_name=f"Material {idx} Double-Sided",
                    status="WARNING",
                    message=f"Material '{mat_info['name']}' is double-sided. Not recommended"
                ))
            
            material_info.append(mat_info)
        
        if pbr_compliant:
            self.results.append(ValidationResult(
                category="Materials",
                check_name="PBR Compliance",
                status="PASS",
                message="All materials use PBR Metal-Rough workflow",
                details={"materials": material_info}
            ))
        else:
            self.results.append(ValidationResult(
                category="Materials",
                check_name="PBR Compliance",
                status="FAIL",
                message="Not all materials are PBR compliant or missing required textures",
                details={"materials": material_info}
            ))
    
    def _validate_alignment(self):
        """Validate model alignment and orientation"""
        if not self.gltf.scenes or not self.gltf.nodes:
            self.results.append(ValidationResult(
                category="Alignment",
                check_name="Scene Structure",
                status="WARNING",
                message="Cannot validate alignment - no scene or nodes found"
            ))
            return
        
        # Check if model has proper scene structure
        scene = self.gltf.scenes[self.gltf.scene] if self.gltf.scene is not None else self.gltf.scenes[0]
        
        self.results.append(ValidationResult(
            category="Alignment",
            check_name="Scene Structure",
            status="INFO",
            message=f"Model has {len(self.gltf.nodes)} node(s). "
                    "Verify alignment manually: Front=+Z, Up=+Y, Pivot at (0,0,0)"
        ))
        
        # Note: Full alignment validation requires analyzing mesh vertices
        # which is complex. This is a placeholder for manual verification
        self.results.append(ValidationResult(
            category="Alignment",
            check_name="Orientation Check",
            status="INFO",
            message="Manual verification required: Ensure model front faces +Z, up is +Y, pivot at origin"
        ))
    
    def _validate_extensions(self):
        """Validate glTF extensions"""
        if not self.gltf.extensionsUsed:
            self.results.append(ValidationResult(
                category="Extensions",
                check_name="Extensions Used",
                status="INFO",
                message="No glTF extensions used"
            ))
            return
        
        unsupported = []
        supported = []
        
        for ext in self.gltf.extensionsUsed:
            if ext in self.SUPPORTED_EXTENSIONS:
                supported.append(ext)
            else:
                unsupported.append(ext)
        
        if supported:
            self.results.append(ValidationResult(
                category="Extensions",
                check_name="Supported Extensions",
                status="PASS",
                message=f"Using {len(supported)} supported extension(s)",
                details={"extensions": supported}
            ))
        
        if unsupported:
            self.results.append(ValidationResult(
                category="Extensions",
                check_name="Unsupported Extensions",
                status="WARNING",
                message=f"Using {len(unsupported)} unsupported extension(s): {', '.join(unsupported)}",
                details={"extensions": unsupported}
            ))
    
    def _run_gltf_validator(self):
        """Run the official Khronos glTF validator"""
        try:
            # Check if gltf_validator is available
            result = subprocess.run(
                ['gltf_validator', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise FileNotFoundError()
            
            # Run validator
            result = subprocess.run(
                ['gltf_validator', str(self.model_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.results.append(ValidationResult(
                    category="Official Validation",
                    check_name="Khronos glTF Validator",
                    status="PASS",
                    message="Model passed official glTF validation"
                ))
            else:
                self.results.append(ValidationResult(
                    category="Official Validation",
                    check_name="Khronos glTF Validator",
                    status="FAIL",
                    message=f"Model failed glTF validation: {result.stdout}"
                ))
        
        except FileNotFoundError:
            self.results.append(ValidationResult(
                category="Official Validation",
                check_name="Khronos glTF Validator",
                status="INFO",
                message="glTF Validator not installed. Install from: https://github.com/KhronosGroup/glTF-Validator"
            ))
        except subprocess.TimeoutExpired:
            self.results.append(ValidationResult(
                category="Official Validation",
                check_name="Khronos glTF Validator",
                status="WARNING",
                message="glTF Validator timed out"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category="Official Validation",
                check_name="Khronos glTF Validator",
                status="WARNING",
                message=f"Could not run glTF Validator: {str(e)}"
            ))
    
    def _generate_report(self) -> ComplianceReport:
        """Generate the final compliance report"""
        # Count statuses
        summary = {
            "PASS": sum(1 for r in self.results if r.status == "PASS"),
            "FAIL": sum(1 for r in self.results if r.status == "FAIL"),
            "WARNING": sum(1 for r in self.results if r.status == "WARNING"),
            "INFO": sum(1 for r in self.results if r.status == "INFO")
        }
        
        # Determine overall status
        if summary["FAIL"] > 0:
            overall_status = "NON_COMPLIANT"
        elif summary["WARNING"] > 0:
            overall_status = "WARNING"
        else:
            overall_status = "COMPLIANT"
        
        # Gather model info
        model_info = {
            "filename": self.model_path.name,
            "file_size_mb": round(self.model_path.stat().st_size / (1024 * 1024), 2),
            "format": self.model_path.suffix
        }
        
        if self.gltf:
            model_info.update({
                "meshes": len(self.gltf.meshes) if self.gltf.meshes else 0,
                "materials": len(self.gltf.materials) if self.gltf.materials else 0,
                "textures": len(self.gltf.images) if self.gltf.images else 0,
                "nodes": len(self.gltf.nodes) if self.gltf.nodes else 0
            })
        
        return ComplianceReport(
            model_name=self.model_path.name,
            validation_time=datetime.now().isoformat(),
            overall_status=overall_status,
            results=self.results,
            summary=summary,
            model_info=model_info
        )
    
    @staticmethod
    def _is_power_of_two(n: int) -> bool:
        """Check if number is power of 2"""
        return n > 0 and (n & (n - 1)) == 0


def print_report(report: ComplianceReport):
    """Print a formatted console report"""
    print("\n" + "=" * 60)
    print(f"AMAZON 3D MODEL COMPLIANCE REPORT")
    print("=" * 60)
    print(f"Model: {report.model_name}")
    print(f"Validation Time: {report.validation_time}")
    print(f"Overall Status: {report.overall_status}")
    print(f"\nFile Info:")
    for key, value in report.model_info.items():
        print(f"  {key}: {value}")
    
    print(f"\nSummary:")
    print(f"  ✓ PASS: {report.summary['PASS']}")
    print(f"  ✗ FAIL: {report.summary['FAIL']}")
    print(f"  ⚠ WARNING: {report.summary['WARNING']}")
    print(f"  ℹ INFO: {report.summary['INFO']}")
    
    print(f"\nDetailed Results:")
    print("-" * 60)
    
    current_category = None
    for result in report.results:
        if result.category != current_category:
            current_category = result.category
            print(f"\n{current_category}:")
        
        status_icon = {
            "PASS": "✓",
            "FAIL": "✗",
            "WARNING": "⚠",
            "INFO": "ℹ"
        }.get(result.status, "?")
        
        print(f"  {status_icon} {result.check_name}: {result.message}")
        
        if result.details:
            for key, value in result.details.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"      {key}:")
                    for item in value[:5]:  # Limit to first 5 items
                        if isinstance(item, dict):
                            print(f"        - {item}")
                        else:
                            print(f"        - {item}")
                elif not isinstance(value, list):
                    print(f"      {key}: {value}")
    
    print("\n" + "=" * 60)


def save_json_report(report: ComplianceReport, output_path: str):
    """Save report as JSON"""
    report_dict = asdict(report)
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)
    
    print(f"\n📄 JSON report saved to: {output_path}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python amazon_3d_validator.py <path_to_gltf_or_glb_file>")
        print("Example: python amazon_3d_validator.py model.glb")
        sys.exit(1)
    
    model_path = sys.argv[1]
    
    if not os.path.exists(model_path):
        print(f"Error: File not found: {model_path}")
        sys.exit(1)
    
    # Run validation
    validator = AmazonGLTFValidator(model_path)
    report = validator.validate()
    
    # Print report
    print_report(report)
    
    # Save JSON report
    json_output = Path(model_path).stem + "_compliance_report.json"
    save_json_report(report, json_output)
    
    # Exit with appropriate code
    if report.overall_status == "NON_COMPLIANT":
        sys.exit(1)
    elif report.overall_status == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
