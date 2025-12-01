"""
Amazon 3D Model Validator - Flixmedia Smollan Branded Version
Upload GLB files and get instant validation reports with recommendations

Usage:
    python3 simple_validator_ui_branded.py
    Open: http://localhost:5001
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Import our validator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amazon_3d_validator import AmazonGLTFValidator

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

# Create upload folder
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# HTML Template with Flixmedia Smollan branding
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon 3D Model Validator | Flixmedia Smollan</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #2ccd6f 0%, #1ea557 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .logo {
            margin-bottom: 20px;
        }
        
        .logo svg {
            height: 60px;
            width: auto;
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 15px;
        }
        
        .powered-by {
            font-size: 12px;
            color: #999;
            margin-top: 10px;
        }
        
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 10px;
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #fafafa;
            position: relative;
        }
        
        .upload-area:hover {
            border-color: #2ccd6f;
            background: #f0fff6;
        }
        
        .upload-area.dragover {
            border-color: #2ccd6f;
            background: #f0fff6;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 64px;
            color: #2ccd6f;
            margin-bottom: 20px;
        }
        
        .upload-text {
            font-size: 18px;
            color: #333;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .upload-subtext {
            font-size: 14px;
            color: #999;
        }
        
        #fileInput {
            display: none;
        }
        
        .file-info {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: #f0fff6;
            border-radius: 10px;
        }
        
        .file-info.show {
            display: block;
        }
        
        .file-name {
            font-size: 16px;
            color: #333;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .file-size {
            font-size: 14px;
            color: #666;
        }
        
        .validate-btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #2ccd6f 0%, #1ea557 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.3s;
            display: none;
        }
        
        .validate-btn.show {
            display: block;
        }
        
        .validate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(44, 205, 111, 0.4);
        }
        
        .validate-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 30px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #2ccd6f;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-text {
            color: #666;
            font-size: 16px;
        }
        
        .results {
            display: none;
            margin-top: 30px;
        }
        
        .results.show {
            display: block;
        }
        
        .status-badge {
            display: inline-block;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }
        
        .status-compliant {
            background: #E8F5E9;
            color: #2ccd6f;
        }
        
        .status-warning {
            background: #FFF3E0;
            color: #FF9800;
        }
        
        .status-failed {
            background: #FFEBEE;
            color: #F44336;
        }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .summary-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .summary-value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .summary-card.pass .summary-value {
            color: #2ccd6f;
        }
        
        .summary-card.fail .summary-value {
            color: #F44336;
        }
        
        .summary-card.warning .summary-value {
            color: #FF9800;
        }
        
        .results-section {
            margin-bottom: 30px;
        }
        
        .results-section h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 20px;
        }
        
        .result-item {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            gap: 15px;
            align-items: flex-start;
        }
        
        .result-item.pass {
            border-color: #2ccd6f;
            background: #f0fff6;
        }
        
        .result-item.fail {
            border-color: #F44336;
            background: #FFEBEE;
        }
        
        .result-item.warning {
            border-color: #FF9800;
            background: #FFF3E0;
        }
        
        .result-item.info {
            border-color: #2196F3;
            background: #E3F2FD;
        }
        
        .result-icon {
            font-size: 24px;
            min-width: 30px;
        }
        
        .result-content {
            flex: 1;
        }
        
        .result-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        
        .result-message {
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .recommendations {
            background: #FFF9C4;
            border: 2px solid #FBC02D;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
        }
        
        .recommendations h3 {
            color: #F57F17;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .recommendation-item {
            padding: 10px 0;
            color: #333;
            line-height: 1.6;
        }
        
        .recommendation-item strong {
            color: #F57F17;
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }
        
        .btn {
            flex: 1;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #2ccd6f 0%, #1ea557 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(44, 205, 111, 0.4);
        }
        
        .btn-secondary {
            background: white;
            color: #2ccd6f;
            border: 2px solid #2ccd6f;
        }
        
        .btn-secondary:hover {
            background: #f0fff6;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <svg id="logos" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1049.37 314.65" style="height: 50px; width: auto;">
                    <defs><style>.cls-1{fill:#2ccd6f;}.cls-2{fill:#333;}</style></defs>
                    <polygon class="cls-1" points="59.63 188.36 98.35 149.64 117.19 130.8 98.35 111.96 59.63 73.24 42.52 93.81 79.51 130.8 42.52 167.78 59.63 188.36"/>
                    <path class="cls-2" d="M147.46,194.24V48.78h93.03l-2.81,30.44h-56.11v26.74h50.08l-2.81,30.23h-47.27v58.05h-34.11Z"/>
                    <path class="cls-2" d="M254.1,194.24V45.32h31.72v148.92h-31.72Z"/>
                    <path class="cls-2" d="M303.73,61.53v-1.7c0-11.54,5.77-17.32,17.32-17.32s17.32,5.77,17.32,17.32v1.73c0,11.54-5.77,17.32-17.32,17.32s-17.32-5.78-17.32-17.35ZM305.25,194.24v-104.66h31.65v104.66h-31.65Z"/>
                    <path class="cls-2" d="M350.13,194.24c9.54-18.26,20.66-35.64,33.25-51.95-13.03-16.29-24.11-34.04-33.04-52.89h34.11c3.62,10.53,8.87,20.43,15.55,29.33h.87c6.27-9.13,11.41-18.98,15.31-29.33h33.04c-8.64,18.46-19.08,36.03-31.17,52.44,13.25,16.43,25.17,33.9,35.64,52.23h-35.57c-5.04-9.81-10.66-19.32-16.83-28.47h-.87c-5.64,9.2-10.66,18.77-15.03,28.64h-35.26Z"/>
                    <path class="cls-2" d="M470.35,194.24v-104.66h16.62l1.52,11.43c4.29-4.5,9.42-8.13,15.1-10.67,5.8-2.77,12.14-4.21,18.56-4.23,13.09,0,22.33,5.03,27.71,15.1,9.41-9.68,22.35-15.13,35.85-15.1,22.58,0,33.87,12.95,33.87,38.86v69.27h-19.64v-65.39c0-8.77-1.44-14.89-4.33-18.36-3.98-4.15-9.65-6.24-15.38-5.65-10.19.27-19.74,5-26.11,12.95.28,2.6.42,6.93.42,12.75v63.69h-19.64v-64.31c.44-6.52-.75-13.04-3.46-18.98-2.46-4.19-7.27-6.1-14.44-6.1-5.03.11-9.97,1.44-14.37,3.88-4.82,2.45-9.11,5.84-12.61,9.97v75.54h-19.67Z"/>
                    <path class="cls-2" d="M641.68,142.47v-.45c0-16.16,3.95-29.54,11.84-40.14,7.9-10.6,19.63-15.85,35.19-15.76,29.23,0,43.85,18.7,43.85,56.11,0,3.46,0,6.06-.24,7.79h-70.06c1.59,20.57,11.81,30.86,30.65,30.86,10.7.14,21.31-1.93,31.17-6.06l1.73,16c-10.49,4.79-21.93,7.16-33.46,6.93-33.78-.02-50.67-18.45-50.67-55.27ZM662.18,135.33h50.08c-.74-21.7-8.66-32.57-23.76-32.59-7.64-.55-15.03,2.87-19.57,9.04-4.6,6.98-7,15.19-6.89,23.55h.14Z"/>
                    <path class="cls-2" d="M750.95,144.2v-1.25c0-17.11,3.99-30.88,11.98-41.32,7.99-10.44,19.33-15.65,34.01-15.65,9.38-.19,18.61,2.37,26.56,7.34v-48h19.84v105.77c0,10.62.14,25.01.42,43.15h-16.59l-1.32-9.04h-.21c-8.28,8.21-19.52,12.71-31.17,12.5-12.17.42-23.84-4.84-31.59-14.23-7.94-9.49-11.93-22.58-11.95-39.27ZM771.48,142.23c-.47,9.56,1.85,19.06,6.68,27.33,4.54,6.96,12.48,10.94,20.78,10.39,9.35-.05,18.26-3.96,24.62-10.81v-57.56c-6.15-5.16-14-7.85-22.03-7.55-20.06,0-30.08,12.73-30.06,38.2Z"/>
                    <path class="cls-2" d="M870.26,58.69v-1.49c0-8.8,3.95-13.16,11.88-13.16s11.22,4.36,11.22,13.16v1.49c0,8.66-3.74,12.95-11.22,12.95s-11.88-4.29-11.88-12.95ZM871.99,194.24v-104.66h19.64v104.66h-19.64Z"/>
                    <path class="cls-2" d="M914.59,166.4c0-25.74,19.71-38.62,59.12-38.62h5.4v-4.12c0-8.03-1.8-13.58-5.4-16.62s-9.43-4.48-17.49-4.29c-10.85.29-21.54,2.64-31.52,6.93l-3.01-16.17c11.8-4.77,24.4-7.26,37.13-7.34,13.69,0,23.77,2.74,30.24,8.21,6.47,5.47,9.7,14.97,9.7,28.5v52.64c-.26,2.57.24,5.15,1.42,7.45.94,1.25,2.98,1.84,6.13,1.84v11.43c-3.33,1.17-6.86,1.69-10.39,1.52-9.07,0-14.23-4.33-15.55-12.95-8.75,8.68-20.69,13.36-33.01,12.95-8.61.32-17.02-2.65-23.52-8.31-6.35-5.92-9.74-14.36-9.25-23.03ZM935.09,164.46c-.21,4.51,1.41,8.9,4.5,12.19,3.64,3.33,8.49,5.01,13.4,4.64,9.93-.13,19.37-4.34,26.11-11.64v-26.98h-3.22c-4.91-.05-9.81.21-14.68.76-4.33.52-8.6,1.46-12.75,2.81-3.94,1.11-7.43,3.45-9.94,6.68-2.37,3.37-3.58,7.42-3.43,11.53Z"/>
                </svg>
            </div>
            <h1>Amazon 3D Model Validator</h1>
            <p>Quality Check for Amazon Marketplace</p>
        </div>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📦</div>
            <div class="upload-text">Drop your GLB file here or click to browse</div>
            <div class="upload-subtext">Supported formats: .glb, .gltf (Max 200MB)</div>
            <input type="file" id="fileInput" accept=".glb,.gltf">
        </div>
        
        <div class="file-info" id="fileInfo">
            <div class="file-name" id="fileName"></div>
            <div class="file-size" id="fileSize"></div>
        </div>
        
        <button class="validate-btn" id="validateBtn">
            Validate Model
        </button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div class="loading-text">Validating your model...</div>
            <div class="loading-text" style="font-size: 14px; margin-top: 10px;">Checking 20+ technical requirements</div>
        </div>
        
        <div class="results" id="results">
            <!-- Results will be inserted here -->
        </div>
        
        <div class="footer">
            © 2025 Amazon 3D Model Quality Assurance
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const validateBtn = document.getElementById('validateBtn');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        
        let selectedFile = null;
        
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFile(e.target.files[0]);
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFile(e.dataTransfer.files[0]);
        });
        
        function handleFile(file) {
            if (!file) return;
            
            const ext = file.name.toLowerCase().split('.').pop();
            if (ext !== 'glb' && ext !== 'gltf') {
                alert('Please upload a .glb or .gltf file');
                return;
            }
            
            selectedFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.classList.add('show');
            validateBtn.classList.add('show');
            results.classList.remove('show');
        }
        
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        }
        
        validateBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            validateBtn.disabled = true;
            loading.classList.add('show');
            results.classList.remove('show');
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/validate', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                loading.classList.remove('show');
                validateBtn.disabled = false;
                
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                displayResults(data);
            } catch (error) {
                loading.classList.remove('show');
                validateBtn.disabled = false;
                alert('Error validating file: ' + error.message);
            }
        });
        
        function displayResults(data) {
            const report = data.report;
            const recommendations = data.recommendations;
            
            let statusClass = 'status-failed';
            let statusText = 'NON-COMPLIANT';
            
            if (report.overall_status === 'COMPLIANT') {
                statusClass = 'status-compliant';
                statusText = 'COMPLIANT ✓';
            } else if (report.overall_status === 'WARNING') {
                statusClass = 'status-warning';
                statusText = 'COMPLIANT WITH WARNINGS';
            }
            
            let html = `
                <div class="status-badge ${statusClass}">${statusText}</div>
                
                <div class="summary">
                    <div class="summary-card pass">
                        <div class="summary-label">Passed</div>
                        <div class="summary-value">${report.summary.PASS}</div>
                    </div>
                    <div class="summary-card fail">
                        <div class="summary-label">Failed</div>
                        <div class="summary-value">${report.summary.FAIL}</div>
                    </div>
                    <div class="summary-card warning">
                        <div class="summary-label">Warnings</div>
                        <div class="summary-value">${report.summary.WARNING}</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-label">Info</div>
                        <div class="summary-value">${report.summary.INFO}</div>
                    </div>
                </div>
            `;
            
            const categories = {};
            report.results.forEach(result => {
                if (!categories[result.category]) {
                    categories[result.category] = [];
                }
                categories[result.category].push(result);
            });
            
            for (const [category, categoryResults] of Object.entries(categories)) {
                html += `
                    <div class="results-section">
                        <h3>${category}</h3>
                `;
                
                categoryResults.forEach(result => {
                    const icon = {
                        'PASS': '✓',
                        'FAIL': '✗',
                        'WARNING': '⚠',
                        'INFO': 'ℹ'
                    }[result.status] || '?';
                    
                    html += `
                        <div class="result-item ${result.status.toLowerCase()}">
                            <div class="result-icon">${icon}</div>
                            <div class="result-content">
                                <div class="result-title">${result.check_name}</div>
                                <div class="result-message">${result.message}</div>
                            </div>
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            if (recommendations && recommendations.length > 0) {
                html += `
                    <div class="recommendations">
                        <h3>💡 Recommendations to Fix Issues</h3>
                `;
                
                recommendations.forEach((rec, index) => {
                    html += `
                        <div class="recommendation-item">
                            ${index + 1}. ${rec}
                        </div>
                    `;
                });
                
                html += `</div>`;
            }
            
            html += `
                <div class="action-buttons">
                    <button class="btn btn-secondary" onclick="location.reload()">
                        Validate Another Model
                    </button>
                    <button class="btn btn-primary" onclick="downloadReport()">
                        Download Full Report
                    </button>
                </div>
            `;
            
            results.innerHTML = html;
            results.classList.add('show');
            
            window.reportData = data;
        }
        
        function downloadReport() {
            const data = window.reportData;
            const blob = new Blob([JSON.stringify(data.report, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.report.model_name.replace('.glb', '') + '_compliance_report.json';
            a.click();
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""


def generate_recommendations(report):
    """Generate actionable recommendations based on validation results"""
    recommendations = []
    
    # Handle both dict and object formats
    if hasattr(report, '__dict__'):
        report_dict = report.__dict__
        results = report_dict.get('results', [])
    else:
        report_dict = report
        results = report.get('results', [])
    
    for result in results:
        # Convert result to dict if it's an object
        if hasattr(result, '__dict__'):
            result_dict = result.__dict__
        else:
            result_dict = result
            
        status = result_dict.get('status')
        check = result_dict.get('check_name', '')
        message = result_dict.get('message', '')
        
        if status == 'FAIL':
            if 'Triangle Count' in check and 'exceeds' in message:
                recommendations.append(
                    "<strong>Reduce Triangle Count:</strong> Your model exceeds the 200,000 triangle limit. "
                    "Use Blender's Decimate modifier or retopology tools to optimize the mesh. "
                    "Aim for 150,000-180,000 triangles for safety margin."
                )
            
            elif 'Texture' in check and ('small' in message.lower() or 'large' in message.lower()):
                if 'small' in message.lower():
                    recommendations.append(
                        "<strong>Increase Texture Resolution:</strong> Textures must be at least 2048x2048 pixels. "
                        "Re-export your textures at 2K or 4K resolution."
                    )
                else:
                    recommendations.append(
                        "<strong>Reduce Texture Resolution:</strong> Textures must not exceed 4096x4096 pixels. "
                        "Resize to 4K or 2K using image editing software."
                    )
            
            elif 'embedded' in message.lower() or 'data URI' in message.lower():
                recommendations.append(
                    "<strong>Use External Textures:</strong> Amazon does not accept embedded textures. "
                    "When exporting from Blender, use 'glTF Separate' format."
                )
            
            elif 'PBR' in check or 'material' in message.lower():
                recommendations.append(
                    "<strong>Implement PBR Materials:</strong> Use Blender's Principled BSDF shader "
                    "with Metal-Rough workflow. Include BaseColor, Metallic, and Roughness texture maps."
                )
            
            elif 'animation' in message.lower():
                recommendations.append(
                    "<strong>Remove Animations:</strong> Delete all animation data. "
                    "Uncheck 'Export Animations' when exporting."
                )
            
            elif 'camera' in message.lower():
                recommendations.append(
                    "<strong>Remove Cameras:</strong> Delete all camera objects and uncheck 'Export Cameras'."
                )
            
            elif 'light' in message.lower():
                recommendations.append(
                    "<strong>Remove Lights:</strong> Delete all light objects and uncheck 'Export Lights'."
                )
    
    recommendations = list(dict.fromkeys(recommendations))
    return recommendations


@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/validate', methods=['POST'])
def validate():
    """Handle file upload and validation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.glb', '.gltf')):
        return jsonify({'error': 'Invalid file format. Please upload .glb or .gltf files only.'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(filepath)
        
        validator = AmazonGLTFValidator(str(filepath))
        report = validator.validate()
        
        recommendations = generate_recommendations(report.__dict__)
        
        report_dict = {
            'model_name': report.model_name,
            'validation_time': report.validation_time,
            'overall_status': report.overall_status,
            'summary': report.summary,
            'model_info': report.model_info,
            'results': [
                {
                    'category': r.category,
                    'check_name': r.check_name,
                    'status': r.status,
                    'message': r.message,
                    'details': r.details
                }
                for r in report.results
            ]
        }
        
        return jsonify({
            'success': True,
            'report': report_dict,
            'recommendations': recommendations
        })
    
    except Exception as e:
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎯 Amazon 3D Model Validator - Flixmedia Smollan Edition")
    print("="*70)
    print("\n📍 Open your browser and go to: http://localhost:5001")
    print("\n✨ Branded for Flixmedia Smollan")
    print("   • Green color scheme matching brand identity")
    print("   • Company logo in header")
    print("   • Professional quality assurance interface")
    print("\n🔄 Press Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5001)