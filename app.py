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
MOCK_ESP32 = True  # Set to True for simulator

# Global storage for emergency messages
# In a real app, this would be a database.
emergency_messages = []

# ===================== STATIC FILES =====================
@app.route('/')
def index():
    return send_file('dashboard.html')

@app.route('/dashboard.css')
def dashboard_css():
    return send_file('dashboard.css')

@app.route('/dashboard.js')
def dashboard_js():
    return send_file('dashboard.js')



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

# ===================== EMERGENCY LOGIC =====================
def classify_emergency(text):
    """Use Gemma to classify the message and extract intensity."""
    prompt = f"""
    Analyze this disaster distress message: "{text}"
    
    Categorize it into exactly one of these: INJURED, TRAPPED, NEED_FOOD, NEED_EVACUATION, GENERAL.
    Assign a severity level: HIGH, MEDIUM, LOW.
    Extract the main need in 3-5 words.
    
    Return ONLY JSON in this format:
    {{"category": "TRAPPED", "severity": "HIGH", "need": "stuck under building"}}
    """
    response = call_gemma(prompt)
    try:
        # Simple extraction of JSON from response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(response[start:end])
    except:
        pass
    
    # Fallback if AI fails or returns bad format
    return {"category": "GENERAL", "severity": "MEDIUM", "need": text[:20]}

@app.route('/api/emergency/receive', methods=['POST'])
def receive_emergency():
    data = request.json
    raw_text = data.get('message', '')
    location = data.get('location', {"x": random.randint(0, 100), "y": random.randint(0, 100)})
    
    if not raw_text:
        return jsonify({"error": "No message"}), 400
        
    analysis = classify_emergency(raw_text)
    
    entry = {
        "id": len(emergency_messages) + 1,
        "timestamp": datetime.now().isoformat(),
        "raw": raw_text,
        "category": analysis.get('category', 'GENERAL'),
        "severity": analysis.get('severity', 'MEDIUM'),
        "need": analysis.get('need', ''),
        "location": location
    }
    
    emergency_messages.append(entry)
    return jsonify(entry)

@app.route('/api/emergency/list', methods=['GET'])
def list_emergency():
    return jsonify(emergency_messages[-20:]) # Return last 20

@app.route('/api/emergency/stats', methods=['GET'])
def get_stats():
    stats = {
        "total": len(emergency_messages),
        "injured": len([m for m in emergency_messages if m['category'] == 'INJURED']),
        "trapped": len([m for m in emergency_messages if m['category'] == 'TRAPPED']),
        "need_evacuation": len([m for m in emergency_messages if m['category'] == 'NEED_EVACUATION']),
        "hotspots": []
    }
    
    # Hotspot logic: display recent report locations
    if emergency_messages:
        # Get up to the 15 most recent locations to form hotspots
        stats['hotspots'] = [m['location'] for m in emergency_messages[-15:]]
        
    return jsonify(stats)

if __name__ == '__main__':
    print("Starting Emergency Dashboard Server on http://localhost:5000")
    print("Starting Pran-Bot Terminal Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
