"""
Pran-Bot Report Server
Generates AI-powered PDF reports using Ollama/Gemma
"""

import os
import io
import json
import requests
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# PDF and Graph libraries
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMMA_MODEL = "gemma2:9b"

# ===================== OLLAMA INTEGRATION =====================

def call_gemma(prompt, max_tokens=2000):
    """Call Ollama with Gemma model for text generation."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": GEMMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

def generate_ai_analysis(sensor_data):
    """Generate comprehensive AI analysis of sensor data."""
    
    # Prepare data summary for AI
    df = pd.DataFrame(sensor_data)
    
    stats_summary = f"""
Sensor Data Statistics:
- Total Records: {len(df)}
- Time Range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}

MQ-2 (Smoke): Min={df['smoke'].min()}, Max={df['smoke'].max()}, Mean={df['smoke'].mean():.1f}, Std={df['smoke'].std():.1f}
MQ-3 (Methane): Min={df['methane'].min()}, Max={df['methane'].max()}, Mean={df['methane'].mean():.1f}, Std={df['methane'].std():.1f}
MQ-7 (CO): Min={df['co'].min()}, Max={df['co'].max()}, Mean={df['co'].mean():.1f}, Std={df['co'].std():.1f}
MQ-135 (Air Quality): Min={df['air'].min()}, Max={df['air'].max()}, Mean={df['air'].mean():.1f}, Std={df['air'].std():.1f}
GPI: Min={df['gpi'].min()}, Max={df['gpi'].max()}, Mean={df['gpi'].mean():.1f}
Temperature: Min={df['temperature'].min():.1f}°C, Max={df['temperature'].max():.1f}°C, Mean={df['temperature'].mean():.1f}°C
Humidity: Min={df['humidity'].min():.1f}%, Max={df['humidity'].max():.1f}%, Mean={df['humidity'].mean():.1f}%
"""
    
    # Detect anomalies and trends
    gpi_trend = "increasing" if df['gpi'].iloc[-5:].mean() > df['gpi'].iloc[:5].mean() else "decreasing"
    high_gpi_count = len(df[df['gpi'] > 100])
    hazardous_count = len(df[df['gpi'] > 200])
    
    anomaly_info = f"""
Trend Analysis:
- GPI Trend: {gpi_trend}
- Records with Moderate+ GPI (>100): {high_gpi_count} ({high_gpi_count/len(df)*100:.1f}%)
- Records with Unhealthy+ GPI (>200): {hazardous_count} ({hazardous_count/len(df)*100:.1f}%)
"""
    
    prompt = f"""You are an expert environmental safety analyst reviewing sensor data from an autonomous gas detection robot called Pran-Bot. Analyze the following sensor data and provide a comprehensive technical report.

{stats_summary}
{anomaly_info}

Please provide:

1. EXECUTIVE SUMMARY (2-3 paragraphs):
- Overall air quality assessment
- Key findings and concerns
- Risk level classification

2. DETAILED SENSOR ANALYSIS:
- Analysis of each sensor (MQ-2, MQ-3, MQ-7, MQ-135)
- What each reading indicates about environmental conditions
- Correlation between sensors

3. GAS POLLUTION INDEX (GPI) ASSESSMENT:
- GPI trend interpretation
- Time periods of concern
- Comparison to safety standards

4. ENVIRONMENTAL CONDITIONS:
- Temperature and humidity impact on sensor readings
- Environmental comfort assessment

5. SAFETY RECOMMENDATIONS:
- Immediate actions if needed
- Long-term monitoring suggestions
- Ventilation recommendations

6. TECHNICAL CONCLUSIONS:
- Sensor calibration observations
- Data quality assessment
- System performance notes

Write in a professional, technical style suitable for industrial safety reports. Be specific with numbers and percentages."""

    return call_gemma(prompt, max_tokens=3000)

# ===================== GRAPH GENERATION =====================

def create_sensor_graph(df, output_path):
    """Create a multi-line chart for all sensors."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(range(len(df)), df['smoke'], label='MQ-2 (Smoke)', color='#00ff00', linewidth=2)
    ax.plot(range(len(df)), df['methane'], label='MQ-3 (Methane)', color='#00ffff', linewidth=2)
    ax.plot(range(len(df)), df['co'], label='MQ-7 (CO)', color='#ffb000', linewidth=2)
    ax.plot(range(len(df)), df['air'], label='MQ-135 (Air)', color='#ff00ff', linewidth=2)
    
    ax.set_xlabel('Sample Index', fontsize=12)
    ax.set_ylabel('ADC Value', fontsize=12)
    ax.set_title('MQ Sensor Array Readings Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0d0d1a')
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#0d0d1a', edgecolor='none')
    plt.close()

def create_gpi_graph(df, output_path):
    """Create GPI trend graph with threshold zones."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    x = range(len(df))
    gpi = df['gpi']
    
    # Fill zones
    ax.axhspan(0, 50, alpha=0.2, color='green', label='Good (0-50)')
    ax.axhspan(50, 100, alpha=0.2, color='yellow', label='Moderate (50-100)')
    ax.axhspan(100, 200, alpha=0.2, color='orange', label='Unhealthy (100-200)')
    ax.axhspan(200, 300, alpha=0.2, color='red', label='Very Unhealthy (200-300)')
    
    ax.plot(x, gpi, color='#00ff00', linewidth=2.5, marker='o', markersize=3)
    ax.fill_between(x, gpi, alpha=0.3, color='#00ff00')
    
    ax.set_xlabel('Sample Index', fontsize=12)
    ax.set_ylabel('GPI Value', fontsize=12)
    ax.set_title('Gas Pollution Index (GPI) Trend Analysis', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(300, gpi.max() + 20))
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0d0d1a')
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#0d0d1a', edgecolor='none')
    plt.close()

def create_env_graph(df, output_path):
    """Create temperature and humidity graph."""
    fig, ax1 = plt.subplots(figsize=(10, 5))
    
    x = range(len(df))
    
    ax1.plot(x, df['temperature'], color='#ff4444', linewidth=2, label='Temperature (°C)')
    ax1.set_xlabel('Sample Index', fontsize=12)
    ax1.set_ylabel('Temperature (°C)', color='#ff4444', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='#ff4444')
    
    ax2 = ax1.twinx()
    ax2.plot(x, df['humidity'], color='#4444ff', linewidth=2, label='Humidity (%)')
    ax2.set_ylabel('Humidity (%)', color='#4444ff', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='#4444ff')
    
    ax1.set_title('Environmental Conditions', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0d0d1a')
    ax1.tick_params(colors='white')
    ax2.tick_params(colors='white')
    ax1.xaxis.label.set_color('white')
    ax1.title.set_color('white')
    
    for spine in ax1.spines.values():
        spine.set_color('#333')
    for spine in ax2.spines.values():
        spine.set_color('#333')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#0d0d1a', edgecolor='none')
    plt.close()

def create_distribution_graph(df, output_path):
    """Create box plot distribution of all sensors."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    data = [df['smoke'], df['methane'], df['co'], df['air']]
    labels = ['MQ-2\n(Smoke)', 'MQ-3\n(Methane)', 'MQ-7\n(CO)', 'MQ-135\n(Air)']
    
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    
    colors_list = ['#00ff00', '#00ffff', '#ffb000', '#ff00ff']
    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax.set_ylabel('ADC Value', fontsize=12)
    ax.set_title('Sensor Value Distribution Analysis', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0d0d1a')
    ax.tick_params(colors='white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    
    for spine in ax.spines.values():
        spine.set_color('#333')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#0d0d1a', edgecolor='none')
    plt.close()

# ===================== PDF GENERATION =====================

def generate_pdf_report(sensor_data, ai_analysis):
    """Generate a comprehensive PDF report."""
    
    df = pd.DataFrame(sensor_data)
    
    # Create temporary directory for graphs
    temp_dir = tempfile.mkdtemp()
    sensor_graph_path = os.path.join(temp_dir, 'sensors.png')
    gpi_graph_path = os.path.join(temp_dir, 'gpi.png')
    env_graph_path = os.path.join(temp_dir, 'env.png')
    dist_graph_path = os.path.join(temp_dir, 'distribution.png')
    
    # Generate graphs
    create_sensor_graph(df, sensor_graph_path)
    create_gpi_graph(df, gpi_graph_path)
    create_env_graph(df, env_graph_path)
    create_distribution_graph(df, dist_graph_path)
    
    # Create PDF
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                           rightMargin=1*cm, leftMargin=1*cm,
                           topMargin=1*cm, bottomMargin=1*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#00ff00'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#00cccc'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#ffb000'),
        spaceBefore=10,
        spaceAfter=5
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    )
    
    # Build PDF content
    story = []
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("PRAN-BOT", title_style))
    story.append(Paragraph("Environmental Monitoring Report", heading_style))
    story.append(Spacer(1, 0.5*inch))
    
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"<b>Generated:</b> {report_time}", body_style))
    story.append(Paragraph(f"<b>Data Points:</b> {len(df)} records", body_style))
    story.append(Paragraph(f"<b>Time Range:</b> {df['timestamp'].iloc[0]} - {df['timestamp'].iloc[-1]}", body_style))
    story.append(Paragraph(f"<b>AI Model:</b> Gemma 2 9B (Ollama)", body_style))
    
    story.append(PageBreak())
    
    # Statistics Table
    story.append(Paragraph("Statistical Summary", heading_style))
    
    stats_data = [
        ['Sensor', 'Min', 'Max', 'Mean', 'Std Dev', 'Status'],
        ['MQ-2 (Smoke)', f"{df['smoke'].min()}", f"{df['smoke'].max()}", 
         f"{df['smoke'].mean():.1f}", f"{df['smoke'].std():.1f}", 
         'Normal' if df['smoke'].mean() < 900 else 'Alert'],
        ['MQ-3 (Methane)', f"{df['methane'].min()}", f"{df['methane'].max()}", 
         f"{df['methane'].mean():.1f}", f"{df['methane'].std():.1f}",
         'Normal' if df['methane'].mean() < 200 else 'Alert'],
        ['MQ-7 (CO)', f"{df['co'].min()}", f"{df['co'].max()}", 
         f"{df['co'].mean():.1f}", f"{df['co'].std():.1f}",
         'Normal' if df['co'].mean() < 100 else 'Alert'],
        ['MQ-135 (Air)', f"{df['air'].min()}", f"{df['air'].max()}", 
         f"{df['air'].mean():.1f}", f"{df['air'].std():.1f}",
         'Normal' if df['air'].mean() < 150 else 'Alert'],
        ['GPI', f"{df['gpi'].min()}", f"{df['gpi'].max()}", 
         f"{df['gpi'].mean():.1f}", f"{df['gpi'].std():.1f}",
         'Good' if df['gpi'].mean() < 50 else ('Moderate' if df['gpi'].mean() < 100 else 'Unhealthy')],
        ['Temperature (°C)', f"{df['temperature'].min():.1f}", f"{df['temperature'].max():.1f}", 
         f"{df['temperature'].mean():.1f}", f"{df['temperature'].std():.1f}", '-'],
        ['Humidity (%)', f"{df['humidity'].min():.1f}", f"{df['humidity'].max():.1f}", 
         f"{df['humidity'].mean():.1f}", f"{df['humidity'].std():.1f}", '-'],
    ]
    
    table = Table(stats_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#00ff00')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#333333')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Graphs Section
    story.append(Paragraph("Sensor Readings Graph", heading_style))
    story.append(Image(sensor_graph_path, width=7*inch, height=3.5*inch))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Gas Pollution Index (GPI) Trend", heading_style))
    story.append(Image(gpi_graph_path, width=7*inch, height=3.5*inch))
    
    story.append(PageBreak())
    
    story.append(Paragraph("Environmental Conditions", heading_style))
    story.append(Image(env_graph_path, width=7*inch, height=3.5*inch))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Value Distribution Analysis", heading_style))
    story.append(Image(dist_graph_path, width=7*inch, height=3.5*inch))
    
    story.append(PageBreak())
    
    # AI Analysis Section
    story.append(Paragraph("AI-Powered Analysis (Gemma 2 9B)", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Split AI analysis into paragraphs
    ai_paragraphs = ai_analysis.split('\n\n')
    for para in ai_paragraphs:
        if para.strip():
            # Check if it's a heading
            if para.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                story.append(Paragraph(para.strip(), subheading_style))
            elif para.strip().isupper() or ':' in para.split('\n')[0]:
                story.append(Paragraph(para.strip(), subheading_style))
            else:
                # Clean up the text for PDF
                clean_text = para.strip().replace('\n', ' ').replace('**', '')
                story.append(Paragraph(clean_text, body_style))
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("─" * 60, body_style))
    story.append(Paragraph(
        "<i>This report was automatically generated by Pran-Bot using Gemma 2 9B AI model. "
        "Data accuracy depends on sensor calibration and environmental conditions.</i>", 
        body_style
    ))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    
    # Cleanup temp files
    for path in [sensor_graph_path, gpi_graph_path, env_graph_path, dist_graph_path]:
        try:
            os.remove(path)
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass
    
    return pdf_buffer

# ===================== API ENDPOINTS =====================

@app.route('/health', methods=['GET'])
def health_check():
    """Check if server and Ollama are running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_status = "connected" if response.status_code == 200 else "error"
    except:
        ollama_status = "disconnected"
    
    return jsonify({
        "status": "running",
        "ollama": ollama_status,
        "model": GEMMA_MODEL
    })

@app.route('/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report from sensor data."""
    try:
        data = request.json
        sensor_data = data.get('sensorData', {})
        
        if not sensor_data.get('timestamps') or len(sensor_data['timestamps']) < 3:
            return jsonify({"error": "Not enough sensor data (minimum 3 records required)"}), 400
        
        # Convert to list of dicts for DataFrame
        records = []
        for i in range(len(sensor_data['timestamps'])):
            records.append({
                'timestamp': sensor_data['timestamps'][i],
                'smoke': sensor_data['smoke'][i],
                'methane': sensor_data['methane'][i],
                'co': sensor_data['co'][i],
                'air': sensor_data['air'][i],
                'gpi': sensor_data['gpi'][i],
                'temperature': sensor_data['temperature'][i],
                'humidity': sensor_data['humidity'][i]
            })
        
        # Save CSV
        df = pd.DataFrame(records)
        csv_filename = f"pranbot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
        df.to_csv(csv_path, index=False)
        
        # Generate AI analysis
        print("Generating AI analysis with Gemma...")
        ai_analysis = generate_ai_analysis(records)
        print("AI analysis complete.")
        
        # Generate PDF
        print("Generating PDF report...")
        pdf_buffer = generate_pdf_report(records, ai_analysis)
        print("PDF report complete.")
        
        # Generate filename
        pdf_filename = f"pranbot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=pdf_filename
        )
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/generate-csv', methods=['POST'])
def generate_csv():
    """Generate and return CSV from sensor data."""
    try:
        data = request.json
        sensor_data = data.get('sensorData', {})
        
        if not sensor_data.get('timestamps'):
            return jsonify({"error": "No sensor data provided"}), 400
        
        # Convert to DataFrame
        records = []
        for i in range(len(sensor_data['timestamps'])):
            records.append({
                'timestamp': sensor_data['timestamps'][i],
                'smoke': sensor_data['smoke'][i],
                'methane': sensor_data['methane'][i],
                'co': sensor_data['co'][i],
                'air': sensor_data['air'][i],
                'gpi': sensor_data['gpi'][i],
                'temperature': sensor_data['temperature'][i],
                'humidity': sensor_data['humidity'][i]
            })
        
        df = pd.DataFrame(records)
        
        # Create CSV buffer
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        csv_filename = f"pranbot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=csv_filename
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("  PRAN-BOT Report Server")
    print("=" * 50)
    print(f"  Model: {GEMMA_MODEL}")
    print(f"  Ollama URL: {OLLAMA_URL}")
    print("=" * 50)
    print("\nStarting server on http://localhost:5000")
    print("Endpoints:")
    print("  GET  /health          - Check server status")
    print("  POST /generate-report - Generate PDF report")
    print("  POST /generate-csv    - Generate CSV export")
    print("\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
