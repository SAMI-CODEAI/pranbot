# 🤖 Pran-Bot: Autonomous IoT Environmental Guardian

**Pran-Bot** (inspired by the Sanskrit word for "Breath/Life Force") is a mobile sensing platform that bridges the gap between industrial safety and autonomous robotics. By combining a multi-gas sensing array with intelligent obstacle avoidance, it transforms static environmental monitoring into a proactive, mobile patrol system.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.9+**
- **Ollama** (for AI Report Generation)
- **Node.js** (Optional, only for dev)

### 2. Install & Run Gemma Model (Required for AI Reports)
To enable the AI-powered PDF report generation, you need to install Ollama and the Gemma model.

1. Download and install **[Ollama](https://ollama.com/download)**.
2. Open a terminal and pull the Gemma model:
   ```powershell
   ollama pull gemma2:9b
   ```
   *(Note: You can use `gemma2:2b` for lower-end hardware)*
3. Ensure Ollama is running in the background:
   ```powershell
   ollama serve
   ```

### 3. Setup & Run Application

We've provided a simple script to handle everything for you.

#### Option A: One-Click Launch (Windows)
Double-click `run_report_server.bat` in the project folder. 
This will:
1. Create a virtual environment (`.venv`)
2. Install all Python dependencies
3. Start the Report Server

#### Option B: Manual Setup
```powershell
# Create virtual env
python -m venv .venv

# Activate it
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python report_server.py
```

### 4. Access the Terminal Interface
Once the server is running on `http://localhost:5000`:
1. Open `terminal.html` in your browser.
2. Type `help` to see available commands.
3. Type `report` to generate an AI-powered safety analysis PDF.

---

## 🧠 System Architecture & "Intelligence"

The robot operates on a multi-layer logic system:

***The Sensing Layer**: A quad-sensor array (MQ-2, MQ-3, MQ-7, MQ-135) continuously samples air quality.

***The Decision Engine**: If Smoke or CO levels cross critical safety thresholds (Smoke > 2000 or CO > 1500), the robot executes an "Emergency Stop".

***The Mobility Layer**: Uses IR-based reactive navigation to navigate complex indoor environments autonomously.

***The API Bridge**: An onboard WebServer exposes a JSON API, allowing live data visualization and Python-based AI command.

***The AI Analysis Layer**: Integrates with Google's **Gemma** model via Ollama to produce comprehensive safety reports with statistical analysis and actionable recommendations.

---

## 🛠 Hardware Interconnects

*Built on an ESP32 SoC for high-speed processing and dual-core performance.*

| Subsystem | Components | ESP32 Pins |
| --- | --- | --- |
| **Gas Array** | MQ-2 (Smoke), MQ-3 (CH4), MQ-7 (CO), MQ-135 (AQI) | GPIO 34, 35, 32, 33 |
| **Propulsion** | L298N Dual Bridge (IN1-IN4) | GPIO 25, 26, 27, 14 |
| **Speed Control** | Dual PWM (ENA/ENB) | GPIO 12, 13 |
| **Vision/Safety** | Dual Infrared (IR) Obstacle Sensors | GPIO 4, 5 |
| **Power** | Battery Voltage Monitoring | GPIO 36 |

---

## 🔬 Research & Academic Alignment

This project serves as a physical validation of the **"Indoor Air Quality Detection Robot Model"** (referenced in IEEE literature), proving that:

**Sensor Fusion** provides a more accurate Gas Pollution Index (GPI) than single-sensor systems.
**Autonomous Patrols** significantly reduce human exposure to hazardous leaks during initial inspection.
**Generative AI Integration** allows for automated, high-level interpreting of raw sensor data into human-readable safety reports.

---

## 📊 Data & Control API

The robot serves a live API for remote integration via its local Access Point **"Gas_Robot_AP"**:

* `GET /data`: Returns real-time sensor telemetry (Smoke, Methane, CO, Air Quality, Battery) in JSON format.
* `GET /cmd?d=`: Remotely overrides navigation (f=forward, b=back, l=left, r=right, s=stop).
* `GET /auto?v=1`: Activates the autonomous "Decision Engine".
