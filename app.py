"""
Pran-Bot Terminal Backend
Serves the Linux Terminal UI and proxies communication to ESP32
"""

import os
import io
import json
import requests
import tempfile
import random
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# PDF and Graph libraries (from report_server.py)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)
CORS(app)

# ===================== CONFIG =====================
ESP32_IP = "http://192.168.4.1"
OLLAMA_URL = "http://localhost:11434/api/generate"
GEMMA_MODEL = "gemma2:9b"
MOCK_ESP32 = False  # Set to True if ESP32 is not available

# ===================== STATIC FILES =====================
@app.route('/')
def index():
    return send_file('terminal.html')

@app.route('/terminal.css')
def css():
    return send_file('terminal.css')

@app.route('/terminal.js')
def js():
    return send_file('terminal.js')

# ===================== ESP32 PROXY =====================
@app.route('/api/data', methods=['GET'])
def get_data():
    """Fetch real-time data from ESP32."""
    if MOCK_ESP32:
        # Simulated data if ESP32 is offline/mocked
        return jsonify({
            "smoke": random.randint(300, 1400),
            "methane": random.randint(100, 1000),
            "co": random.randint(20, 500),
            "air": random.randint(50, 1600),
            "battery": random.randint(3000, 4200),
            "ir_left": random.choice([0, 1]),
            "ir_right": random.choice([0, 1]),
            "radar_angle": random.choice(range(20, 160, 5)),
            "radar_distance": random.randint(5, 200),
            "mock": True
        })

    try:
        response = requests.get(f"{ESP32_IP}/data", timeout=0.5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "ESP32 Error"}), 502
    except:
        # Fallback to mock if connection fails
        return jsonify({
            "error": "ESP32 Disconnected",
            "smoke": 0, "methane": 0, "co": 0, "air": 0,
            "battery": 0, "ir_left": 1, "ir_right": 1
        }), 504

@app.route('/api/cmd', methods=['GET'])
def send_cmd():
    """Send command to ESP32."""
    cmd = request.args.get('d')
    if not cmd:
        return jsonify({"error": "No command provided"}), 400

    if MOCK_ESP32:
        return jsonify({"status": "OK", "mock": True})

    try:
        requests.get(f"{ESP32_IP}/cmd?d={cmd}", timeout=0.5)
        return jsonify({"status": "OK"})
    except:
        return jsonify({"error": "Failed to send command"}), 502

@app.route('/api/auto', methods=['GET'])
def set_auto():
    """Set autonomous mode."""
    val = request.args.get('v')
    if not val:
        return jsonify({"error": "No value provided"}), 400
    
    if MOCK_ESP32:
        return jsonify({"status": "OK", "mock": True})

    try:
        requests.get(f"{ESP32_IP}/auto?v={val}", timeout=0.5)
        return jsonify({"status": "OK"})
    except:
        return jsonify({"error": "Failed to set auto mode"}), 502

# ===================== REPORT GENERATION (From report_server.py) =====================
def call_gemma(prompt, max_tokens=2000):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": GEMMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7}
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "")
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

def generate_ai_analysis(sensor_data):
    df = pd.DataFrame(sensor_data)
    
    stats_summary = f"""
    Sensor Data Statistics:
    - Total Records: {len(df)}
    MQ-2 (Smoke): Mean={df['smoke'].mean():.1f}
    MQ-3 (Methane): Mean={df['methane'].mean():.1f}
    MQ-7 (CO): Mean={df['co'].mean():.1f}
    MQ-135 (Air): Mean={df['air'].mean():.1f}
    GPI: Mean={df['gpi'].mean():.1f}, Max={df['gpi'].max()}
    """
    
    prompt = f"Analyze this sensor data for an industrial gas robot report:\n{stats_summary}\nProvide a safety assessment and recommendations."
    return call_gemma(prompt)

def create_plots(df, temp_dir):
    paths = {}
    
    # Sensor Plot
    plt.figure(figsize=(10, 5))
    plt.plot(df['smoke'], label='Smoke', color='green')
    plt.plot(df['methane'], label='Methane', color='cyan')
    plt.plot(df['co'], label='CO', color='orange')
    plt.title('Sensor Readings')
    plt.legend()
    plt.savefig(os.path.join(temp_dir, 'sensors.png'))
    plt.close()
    paths['sensors'] = os.path.join(temp_dir, 'sensors.png')

    return paths

def generate_pdf_report(sensor_data, ai_analysis):
    df = pd.DataFrame(sensor_data)
    temp_dir = tempfile.mkdtemp()
    plot_paths = create_plots(df, temp_dir)
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Pran-Bot Environmental Report", styles['Title']))
    story.append(Paragraph(f"Generated: {datetime.now()}", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Sensor Overview", styles['Heading2']))
    story.append(Image(plot_paths['sensors'], width=6*inch, height=3*inch))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("AI Analysis", styles['Heading2']))
    story.append(Paragraph(ai_analysis, styles['Normal']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "running", "ollama": "unknown", "model": GEMMA_MODEL})

@app.route('/generate-report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        sensor_data = data.get('sensorData', {})
        if not sensor_data.get('timestamps') or len(sensor_data['timestamps']) < 3:
            return jsonify({"error": "Not enough data"}), 400
        
        # Convert to list of dicts
        records = []
        for i in range(len(sensor_data['timestamps'])):
            records.append({k: sensor_data[k][i] for k in sensor_data.keys()})

        ai_analysis = generate_ai_analysis(records)
        pdf_buffer = generate_pdf_report(records, ai_analysis)
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Pran-Bot Terminal Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
