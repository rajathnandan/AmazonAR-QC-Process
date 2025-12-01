#!/usr/bin/env python3
"""
Amazon 3D Model Compliance Report Generator
Generates professional PDF reports from validation results
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import subprocess

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("Installing reportlab...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "reportlab"])
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class CompliancePDFGenerator:
    """Generates PDF reports for Amazon 3D model compliance"""
    
    def __init__(self, json_report_path: str, company_name: str = "WarRoom"):
        self.json_path = Path(json_report_path)
        self.company_name = company_name
        self.report_data = self._load_report()
        
        # Color scheme
        self.primary_color = colors.HexColor('#232F3E')  # Amazon dark
        self.secondary_color = colors.HexColor('#FF9900')  # Amazon orange
        self.success_color = colors.HexColor('#4CAF50')
        self.warning_color = colors.HexColor('#FF9800')
        self.error_color = colors.HexColor('#F44336')
        self.info_color = colors.HexColor('#2196F3')
        
    def _load_report(self) -> Dict:
        """Load the JSON report"""
        with open(self.json_path, 'r') as f:
            return json.load(f)
    
    def generate(self, output_path: str = None):
        """Generate the PDF report"""
        if output_path is None:
            output_path = self.json_path.stem + ".pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=self.primary_color,
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Header
        story.extend(self._create_header(title_style, styles))
        
        # Executive Summary
        story.extend(self._create_executive_summary(heading_style, styles))
        
        # Model Information
        story.extend(self._create_model_info(heading_style, styles))
        
        # Detailed Results
        story.extend(self._create_detailed_results(heading_style, styles))
        
        # Recommendations
        story.extend(self._create_recommendations(heading_style, styles))
        
        # Footer
        story.extend(self._create_footer(styles))
        
        # Build PDF
        doc.build(story)
        print(f"\n✅ PDF report generated: {output_path}")
        
        return output_path
    
    def _create_header(self, title_style, styles) -> List:
        """Create the report header"""
        elements = []
        
        # Company name
        company = Paragraph(
            f"<b>{self.company_name}</b>",
            ParagraphStyle(
                'Company',
                parent=styles['Normal'],
                fontSize=10,
                textColor=self.secondary_color,
                alignment=TA_RIGHT
            )
        )
        elements.append(company)
        elements.append(Spacer(1, 0.2*inch))
        
        # Title
        title = Paragraph("Amazon 3D Model<br/>Compliance Report", title_style)
        elements.append(title)
        
        # Model name
        model_name = Paragraph(
            f"<b>{self.report_data['model_name']}</b>",
            ParagraphStyle(
                'ModelName',
                parent=styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                textColor=self.primary_color
            )
        )
        elements.append(model_name)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_executive_summary(self, heading_style, styles) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", heading_style))
        
        # Status badge
        status = self.report_data['overall_status']
        status_color = {
            'COMPLIANT': self.success_color,
            'NON_COMPLIANT': self.error_color,
            'WARNING': self.warning_color
        }.get(status, self.info_color)
        
        # Summary table
        summary_data = [
            ['Overall Status', status, ''],
            ['Validation Date', datetime.fromisoformat(self.report_data['validation_time']).strftime('%Y-%m-%d %H:%M'), ''],
            ['', '', ''],
            ['Checks Passed', str(self.report_data['summary']['PASS']), '✓'],
            ['Checks Failed', str(self.report_data['summary']['FAIL']), '✗'],
            ['Warnings', str(self.report_data['summary']['WARNING']), '⚠'],
            ['Info Items', str(self.report_data['summary']['INFO']), 'ℹ'],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 0.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F5F5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Status row highlighting
            ('BACKGROUND', (1, 0), (1, 0), status_color),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Status message
        if status == 'COMPLIANT':
            message = "✓ This model meets all Amazon 3D technical requirements and is ready for submission."
        elif status == 'WARNING':
            message = "⚠ This model meets core requirements but has warnings that should be reviewed."
        else:
            message = "✗ This model does not meet Amazon 3D technical requirements. Please review the failed checks below."
        
        status_para = Paragraph(
            f"<b>{message}</b>",
            ParagraphStyle(
                'StatusMessage',
                parent=styles['Normal'],
                fontSize=11,
                textColor=status_color,
                alignment=TA_LEFT
            )
        )
        elements.append(status_para)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_model_info(self, heading_style, styles) -> List:
        """Create model information section"""
        elements = []
        
        elements.append(Paragraph("Model Information", heading_style))
        
        model_info = self.report_data['model_info']
        info_data = [
            ['Property', 'Value']
        ]
        
        for key, value in model_info.items():
            readable_key = key.replace('_', ' ').title()
            info_data.append([readable_key, str(value)])
        
        info_table = Table(info_data, colWidths=[2.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_detailed_results(self, heading_style, styles) -> List:
        """Create detailed results section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Validation Results", heading_style))
        
        # Group results by category
        categories = {}
        for result in self.report_data['results']:
            category = result['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        # Create table for each category
        for category, results in categories.items():
            # Category header
            cat_para = Paragraph(
                f"<b>{category}</b>",
                ParagraphStyle(
                    'CategoryHeader',
                    parent=styles['Heading3'],
                    fontSize=13,
                    textColor=self.primary_color,
                    spaceBefore=12,
                    spaceAfter=6
                )
            )
            elements.append(cat_para)
            
            # Results table
            table_data = [['Status', 'Check', 'Result']]
            
            for result in results:
                status_icon = {
                    'PASS': '✓',
                    'FAIL': '✗',
                    'WARNING': '⚠',
                    'INFO': 'ℹ'
                }.get(result['status'], '?')
                
                status_color = {
                    'PASS': self.success_color,
                    'FAIL': self.error_color,
                    'WARNING': self.warning_color,
                    'INFO': self.info_color
                }.get(result['status'], colors.black)
                
                # Truncate long messages
                message = result['message']
                if len(message) > 150:
                    message = message[:147] + "..."
                
                table_data.append([
                    status_icon,
                    result['check_name'],
                    message
                ])
            
            results_table = Table(
                table_data,
                colWidths=[0.5*inch, 2*inch, 3.5*inch]
            )
            
            # Apply style
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
            
            # Color code status column
            for i, result in enumerate(results, start=1):
                status_color = {
                    'PASS': self.success_color,
                    'FAIL': self.error_color,
                    'WARNING': self.warning_color,
                    'INFO': self.info_color
                }.get(result['status'], colors.black)
                
                style_commands.append(('TEXTCOLOR', (0, i), (0, i), status_color))
                style_commands.append(('FONTNAME', (0, i), (0, i), 'Helvetica-Bold'))
            
            results_table.setStyle(TableStyle(style_commands))
            
            elements.append(results_table)
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_recommendations(self, heading_style, styles) -> List:
        """Create recommendations section"""
        elements = []
        
        # Only show if there are failures or warnings
        fail_count = self.report_data['summary']['FAIL']
        warning_count = self.report_data['summary']['WARNING']
        
        if fail_count == 0 and warning_count == 0:
            return elements
        
        elements.append(PageBreak())
        elements.append(Paragraph("Recommendations", heading_style))
        
        recommendations = []
        
        # Analyze failures and provide recommendations
        for result in self.report_data['results']:
            if result['status'] == 'FAIL':
                check = result['check_name']
                
                if 'Triangle Count' in check:
                    recommendations.append(
                        "• <b>Reduce Triangle Count:</b> Optimize mesh geometry using decimation or retopology. "
                        "Target models should stay well under 200,000 triangles."
                    )
                elif 'Texture' in check and 'size' in result['message'].lower():
                    recommendations.append(
                        "• <b>Adjust Texture Resolution:</b> Ensure all textures are between 2048x2048 and 4096x4096 pixels, "
                        "square, and power of 2."
                    )
                elif 'PBR' in check:
                    recommendations.append(
                        "• <b>Implement PBR Materials:</b> Use the Metal-Rough workflow with required BaseColor, "
                        "Metallic, and Roughness texture maps."
                    )
                elif 'Animation' in check or 'Camera' in check:
                    recommendations.append(
                        f"• <b>Remove {check}:</b> Amazon models should not contain animations, cameras, or lights."
                    )
                elif 'embedded' in result['message'].lower():
                    recommendations.append(
                        "• <b>Use External Textures:</b> Export textures as separate .PNG or .JPG files, "
                        "not embedded in the glTF file."
                    )
        
        # Add warning recommendations
        for result in self.report_data['results']:
            if result['status'] == 'WARNING':
                if 'double-sided' in result['message'].lower():
                    recommendations.append(
                        "• <b>Disable Double-Sided Materials:</b> Amazon prefers single-sided materials for better performance."
                    )
                elif 'extension' in result['message'].lower():
                    recommendations.append(
                        "• <b>Review Extensions:</b> Some glTF extensions may not be supported. "
                        "Test the model in Amazon's viewer."
                    )
        
        # Remove duplicates
        recommendations = list(dict.fromkeys(recommendations))
        
        if recommendations:
            for rec in recommendations[:10]:  # Limit to 10 recommendations
                elements.append(Paragraph(rec, styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Add reference to Amazon guidelines
        elements.append(Paragraph(
            "<b>Reference:</b> For complete technical requirements, refer to the "
            "<link href='https://sellercentral.amazon.in/help/hub/reference/external/G7RGSNQFZ2BAG7K3'>"
            "Amazon 3D Model Technical Requirements</link>",
            styles['Normal']
        ))
        
        return elements
    
    def _create_footer(self, styles) -> List:
        """Create report footer"""
        elements = []
        
        elements.append(Spacer(1, 0.5*inch))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        footer_text = (
            f"Generated by {self.company_name} Quality Assurance System | "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            "This report validates compliance with Amazon 3D Model Technical Requirements"
        )
        
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python pdf_report_generator.py <path_to_json_report> [company_name]")
        print("Example: python pdf_report_generator.py model_compliance_report.json WarRoom")
        sys.exit(1)
    
    json_path = sys.argv[1]
    company_name = sys.argv[2] if len(sys.argv) > 2 else "WarRoom"
    
    if not Path(json_path).exists():
        print(f"Error: File not found: {json_path}")
        sys.exit(1)
    
    generator = CompliancePDFGenerator(json_path, company_name)
    output_path = generator.generate()
    
    print(f"✅ Report generated successfully!")
    print(f"📄 Output: {output_path}")


if __name__ == "__main__":
    main()
