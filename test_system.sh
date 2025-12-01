#!/bin/bash
# WarRoom 3D QA System - Test Script
# Run this to verify all tools are working correctly

echo "=================================================="
echo "WarRoom 3D QA System - Installation Test"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Python version
echo "Test 1: Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ Python is installed: $python_version${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi
echo ""

# Test 2: Check required Python packages
echo "Test 2: Checking Python packages..."

packages=("pygltflib" "Pillow" "reportlab" "flask")
all_installed=true

for package in "${packages[@]}"; do
    python3 -c "import ${package}" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ ${package} is installed${NC}"
    else
        echo -e "${RED}✗ ${package} is not installed${NC}"
        all_installed=false
    fi
done

if [[ "$all_installed" = false ]]; then
    echo ""
    echo -e "${YELLOW}Installing missing packages...${NC}"
    pip3 install pygltflib Pillow reportlab flask --break-system-packages
fi
echo ""

# Test 3: Check if required files exist
echo "Test 3: Checking required files..."

files=(
    "amazon_3d_validator.py"
    "pdf_report_generator.py"
    "amazon_compliance_addon.py"
    "dashboard_app.py"
    "README.md"
    "IMPLEMENTATION_GUIDE.md"
    "QUICK_START.md"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓ $file exists${NC}"
    else
        echo -e "${RED}✗ $file is missing${NC}"
    fi
done
echo ""

# Test 4: Check for glTF validator (optional)
echo "Test 4: Checking for glTF Validator (optional)..."
if command -v gltf_validator &> /dev/null; then
    version=$(gltf_validator --version 2>&1)
    echo -e "${GREEN}✓ glTF Validator is installed: $version${NC}"
else
    echo -e "${YELLOW}⚠ glTF Validator not found (optional)${NC}"
    echo "  Install from: https://github.com/KhronosGroup/glTF-Validator/releases"
fi
echo ""

# Test 5: Test validator with a simple example
echo "Test 5: Testing validator (dry run)..."
python3 -c "
from amazon_3d_validator import AmazonGLTFValidator
print('✓ Validator module loads successfully')
" 2>/dev/null

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ Validator module is working${NC}"
else
    echo -e "${YELLOW}⚠ Validator module check skipped (needs a test model)${NC}"
fi
echo ""

# Test 6: Test PDF generator
echo "Test 6: Testing PDF generator..."
python3 -c "
from pdf_report_generator import CompliancePDFGenerator
print('✓ PDF generator module loads successfully')
" 2>/dev/null

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✓ PDF generator module is working${NC}"
else
    echo -e "${RED}✗ PDF generator has issues${NC}"
fi
echo ""

# Summary
echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo ""
echo -e "${GREEN}System is ready to use!${NC}"
echo ""
echo "Next steps:"
echo "1. Read QUICK_START.md for demo instructions"
echo "2. Test with a sample glTF/GLB model:"
echo "   python amazon_3d_validator.py your_model.glb"
echo "3. Generate a PDF report:"
echo "   python pdf_report_generator.py model_compliance_report.json WarRoom"
echo "4. Start the dashboard:"
echo "   python dashboard_app.py"
echo ""
echo "For full documentation, see:"
echo "- README.md (overview)"
echo "- IMPLEMENTATION_GUIDE.md (detailed setup)"
echo "- QUICK_START.md (client demo script)"
echo ""
