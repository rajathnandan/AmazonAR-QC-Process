"""
Amazon 3D Model QA Dashboard
A simple web interface for managing validation projects

Usage:
    python dashboard_app.py

Then open: http://localhost:5000
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
import sys

# Install Flask if needed
try:
    import flask
except ImportError:
    print("Installing Flask...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "flask"])
    import flask

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/claude/uploads'
app.config['REPORTS_FOLDER'] = '/home/claude/reports'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Create necessary directories
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['REPORTS_FOLDER']).mkdir(exist_ok=True)

# Simple in-memory database (use SQLite or PostgreSQL in production)
projects_db = {}


# HTML Templates
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WarRoom 3D QA Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
            color: #333;
        }
        
        .stat-card.success .number {
            color: #4CAF50;
        }
        
        .stat-card.warning .number {
            color: #FF9800;
        }
        
        .stat-card.error .number {
            color: #F44336;
        }
        
        .upload-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .upload-section h2 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .upload-form {
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }
        
        .form-group {
            flex: 1;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #666;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .projects-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .projects-section h2 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .project-list {
            list-style: none;
        }
        
        .project-item {
            padding: 20px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        
        .project-item:hover {
            border-color: #667eea;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .project-name {
            font-size: 18px;
            font-weight: 600;
            color: #333;
        }
        
        .project-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-compliant {
            background: #E8F5E9;
            color: #4CAF50;
        }
        
        .status-warning {
            background: #FFF3E0;
            color: #FF9800;
        }
        
        .status-failed {
            background: #FFEBEE;
            color: #F44336;
        }
        
        .status-pending {
            background: #E3F2FD;
            color: #2196F3;
        }
        
        .project-meta {
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
        }
        
        .project-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn-small {
            padding: 8px 20px;
            font-size: 12px;
        }
        
        .btn-success {
            background: #4CAF50;
            color: white;
        }
        
        .btn-info {
            background: #2196F3;
            color: white;
        }
        
        .message {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .message.success {
            background: #E8F5E9;
            color: #4CAF50;
            border: 2px solid #4CAF50;
        }
        
        .message.error {
            background: #FFEBEE;
            color: #F44336;
            border: 2px solid #F44336;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state svg {
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 WarRoom 3D QA Dashboard</h1>
            <p>Amazon Marketplace Compliance System</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Projects</h3>
                <div class="number">{{ stats.total }}</div>
            </div>
            <div class="stat-card success">
                <h3>Compliant</h3>
                <div class="number">{{ stats.compliant }}</div>
            </div>
            <div class="stat-card warning">
                <h3>Warnings</h3>
                <div class="number">{{ stats.warnings }}</div>
            </div>
            <div class="stat-card error">
                <h3>Failed</h3>
                <div class="number">{{ stats.failed }}</div>
            </div>
        </div>
        
        <div class="upload-section">
            <h2>📤 Upload New Model</h2>
            <form class="upload-form" action="/upload" method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Project Name</label>
                    <input type="text" name="project_name" required placeholder="e.g., TechBrand Headphones">
                </div>
                <div class="form-group">
                    <label>Client</label>
                    <input type="text" name="client_name" required placeholder="e.g., TechBrand Inc">
                </div>
                <div class="form-group">
                    <label>glTF/GLB File</label>
                    <input type="file" name="model_file" accept=".glb,.gltf" required>
                </div>
                <button type="submit" class="btn btn-primary">Validate Model</button>
            </form>
        </div>
        
        <div class="projects-section">
            <h2>📋 Recent Projects</h2>
            
            {% if projects %}
            <ul class="project-list">
                {% for project in projects %}
                <li class="project-item">
                    <div class="project-header">
                        <div class="project-name">{{ project.name }}</div>
                        <div class="project-status status-{{ project.status }}">
                            {{ project.status }}
                        </div>
                    </div>
                    <div class="project-meta">
                        <span>👤 {{ project.client }}</span>
                        <span>📅 {{ project.date }}</span>
                        <span>📁 {{ project.filename }}</span>
                    </div>
                    {% if project.summary %}
                    <div class="project-meta">
                        <span>✓ {{ project.summary.PASS }} passed</span>
                        <span>✗ {{ project.summary.FAIL }} failed</span>
                        <span>⚠ {{ project.summary.WARNING }} warnings</span>
                    </div>
                    {% endif %}
                    <div class="project-actions">
                        <a href="/report/{{ project.id }}" class="btn btn-small btn-info">View Report</a>
                        {% if project.pdf_report %}
                        <a href="/download/{{ project.id }}" class="btn btn-small btn-success">Download PDF</a>
                        {% endif %}
                    </div>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <h3>No projects yet</h3>
                <p>Upload your first model to get started!</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

REPORT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validation Report - {{ project.name }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header {
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .meta {
            color: #666;
            font-size: 14px;
        }
        
        .summary {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        
        .summary h2 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .summary-item {
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ddd;
        }
        
        .summary-item.pass {
            border-left-color: #4CAF50;
        }
        
        .summary-item.fail {
            border-left-color: #F44336;
        }
        
        .summary-item.warning {
            border-left-color: #FF9800;
        }
        
        .summary-item label {
            display: block;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .summary-item value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .results-section {
            margin-bottom: 30px;
        }
        
        .results-section h2 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .category {
            margin-bottom: 30px;
        }
        
        .category h3 {
            background: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        .result-item {
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            margin-bottom: 10px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }
        
        .result-icon {
            font-size: 20px;
            min-width: 30px;
        }
        
        .result-content {
            flex: 1;
        }
        
        .result-name {
            font-weight: 600;
            margin-bottom: 5px;
            color: #333;
        }
        
        .result-message {
            color: #666;
            font-size: 14px;
        }
        
        .result-item.pass {
            background: #E8F5E9;
            border-color: #4CAF50;
        }
        
        .result-item.fail {
            background: #FFEBEE;
            border-color: #F44336;
        }
        
        .result-item.warning {
            background: #FFF3E0;
            border-color: #FF9800;
        }
        
        .result-item.info {
            background: #E3F2FD;
            border-color: #2196F3;
        }
        
        .back-link {
            display: inline-block;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .back-link:hover {
            background: #5568d3;
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Dashboard</a>
        
        <div class="header">
            <h1>{{ project.name }}</h1>
            <div class="meta">
                <p>Client: {{ project.client }}</p>
                <p>Validated: {{ project.date }}</p>
                <p>File: {{ project.filename }}</p>
            </div>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-item pass">
                    <label>Passed</label>
                    <value>{{ report.summary.PASS }}</value>
                </div>
                <div class="summary-item fail">
                    <label>Failed</label>
                    <value>{{ report.summary.FAIL }}</value>
                </div>
                <div class="summary-item warning">
                    <label>Warnings</label>
                    <value>{{ report.summary.WARNING }}</value>
                </div>
                <div class="summary-item">
                    <label>Info</label>
                    <value>{{ report.summary.INFO }}</value>
                </div>
            </div>
        </div>
        
        <div class="results-section">
            <h2>Detailed Results</h2>
            
            {% for category, results in categorized_results.items() %}
            <div class="category">
                <h3>{{ category }}</h3>
                {% for result in results %}
                <div class="result-item {{ result.status|lower }}">
                    <div class="result-icon">
                        {% if result.status == 'PASS' %}✓
                        {% elif result.status == 'FAIL' %}✗
                        {% elif result.status == 'WARNING' %}⚠
                        {% else %}ℹ{% endif %}
                    </div>
                    <div class="result-content">
                        <div class="result-name">{{ result.check_name }}</div>
                        <div class="result-message">{{ result.message }}</div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Main dashboard view"""
    projects = list(projects_db.values())
    projects.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate stats
    stats = {
        'total': len(projects),
        'compliant': sum(1 for p in projects if p['status'] == 'compliant'),
        'warnings': sum(1 for p in projects if p['status'] == 'warning'),
        'failed': sum(1 for p in projects if p['status'] == 'failed')
    }
    
    return render_template_string(DASHBOARD_HTML, projects=projects, stats=stats)


@app.route('/upload', methods=['POST'])
def upload_model():
    """Handle model upload and validation"""
    if 'model_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['model_file']
    project_name = request.form.get('project_name', 'Untitled Project')
    client_name = request.form.get('client_name', 'Unknown Client')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    filename = file.filename
    filepath = Path(app.config['UPLOAD_FOLDER']) / filename
    file.save(filepath)
    
    # Run validation
    try:
        validator_path = Path('/home/claude/amazon_3d_validator.py')
        result = subprocess.run(
            [sys.executable, str(validator_path), str(filepath)],
            capture_output=True,
            text=True,
            cwd='/home/claude'
        )
        
        # Load JSON report
        json_report_path = filepath.parent / f"{filepath.stem}_compliance_report.json"
        with open(json_report_path) as f:
            report = json.load(f)
        
        # Generate PDF report
        pdf_generator_path = Path('/home/claude/pdf_report_generator.py')
        subprocess.run(
            [sys.executable, str(pdf_generator_path), str(json_report_path), 'WarRoom'],
            capture_output=True,
            text=True,
            cwd='/home/claude'
        )
        
        # Store project
        project_id = len(projects_db) + 1
        project = {
            'id': project_id,
            'name': project_name,
            'client': client_name,
            'filename': filename,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': report['overall_status'].lower(),
            'summary': report['summary'],
            'report': report,
            'pdf_report': f"{filepath.stem}_compliance_report.pdf"
        }
        
        projects_db[project_id] = project
        
        return dashboard()
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/report/<int:project_id>')
def view_report(project_id):
    """View detailed report"""
    project = projects_db.get(project_id)
    if not project:
        return "Project not found", 404
    
    report = project['report']
    
    # Categorize results
    categorized = {}
    for result in report['results']:
        category = result['category']
        if category not in categorized:
            categorized[category] = []
        categorized[category].append(result)
    
    return render_template_string(
        REPORT_HTML,
        project=project,
        report=report,
        categorized_results=categorized
    )


@app.route('/download/<int:project_id>')
def download_report(project_id):
    """Download PDF report"""
    project = projects_db.get(project_id)
    if not project or not project.get('pdf_report'):
        return "Report not found", 404
    
    pdf_path = Path('/home/claude') / project['pdf_report']
    if not pdf_path.exists():
        return "PDF not found", 404
    
    return send_file(pdf_path, as_attachment=True)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 WarRoom 3D QA Dashboard Starting...")
    print("="*60)
    print("\n📍 Dashboard will be available at: http://localhost:5000")
    print("🔄 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
