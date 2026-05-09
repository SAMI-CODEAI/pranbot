# Pran-Bot: Technology Stack & Workflow Documentation

This document provides a comprehensive overview of the technical architecture, technology stack, and operational methodologies used in the Pran-Bot Autonomous Gas Detection System.

## 1. Technology Stack

### 1.1 Embedded Systems (Robot)
The core logic for the robot implementation.
*   **Microcontroller:** ESP32 (WiFi-enabled SoC).
*   **Framework:** Arduino (C++).
*   **Sensors:**
    *   **MQ Series:** MQ-2 (Smoke/Combustible), MQ-3 (Alcohol/Methane), MQ-7 (Carbon Monoxide), MQ-135 (Air Quality).
    *   **Environmental:** DHT11/22 (Implied for Temperature & Humidity).
    *   **Navigation:** IR Sensors (Left/Right) for line tracking or obstacle avoidance.
    *   **Voltage:** Resistor divider for battery monitoring.
*   **Actuators:**
    *   **Motors:** DC Motors driven by L298N Motor Driver.
    *   **Alerts:** Active Buzzer.
*   **Connectivity:**
    *   **Wi-Fi Mode:** Access Point (`Gas_Robot_AP`) & Web Server.
    *   **Protocol:** HTTP (REST API for data & control).

### 1.2 Frontend Interfaces
Two distinct interfaces are available for interacting with the robot.

**A. Terminal Interface (Web)**
*   **Type:** Single Page Application (SPA).
*   **Languages:** HTML5, CSS3, Vanilla JavaScript (ES6+).
*   **Libraries:**
    *   `Chart.js`: Real-time sensor and GPI visualization.
    *   Google Fonts (`Ubuntu Mono`): Retro terminal aesthetics.
*   **Features:**
    *   Simulated Linux-like CLI.
    *   Real-time WebSocket/HTTP polling.
    *   Dynamic GPI (Gas Pollution Index) calculation.

**B. Dashboard Interface (Desktop)**
*   **Framework:** Streamlit (Python).
*   **Analysis Libraries:**
    *   `Pandas`: Data manipulation.
    *   `NumPy`: Statistical calculations.
*   **Visualization:**
    *   `Plotly`: Interactive data plotting.
    *   Streamlit Native Metrics.

### 1.3 Backend & Reporting Server
Handles heavy-duty data processing and AI generation off-board.
*   **Server Framework:** Flask (Python).
*   **AI Integration:**
    *   **Model:** Gemma 2 9B (served via Ollama).
    *   **Orchestration:** `requests` to local Ollama API.
*   **Report Generation:**
    *   **PDF Engine:** `reportlab` (programmatic PDF creation).
    *   **Graphing:** `matplotlib` (generating static plots for the PDF).
*   **Utilities:** `flask-cors` (Cross-Origin Resource Sharing).

---

## 2. System Architecture & Methodology

The system operates on a **Client-Server-Robot** architecture, capable of running in both *Real-World* and *Simulation* modes.

### 2.1 Gas Pollution Index (GPI) Methodology
The GPI is a custom composite metric calculated to quantify air quality safety.
*   **Calculation:** Weighted average of sensor ratios ($R_s/R_0$) converted to a logarithmic scale.
*   **Formula:** $GPI = \min(500, \lfloor 100 \times \log_{10}(1 + AvgRatio \times 5) \rfloor)$
*   **Scales:**
    *   0-50: Good (Green)
    *   51-100: Moderate (Yellow)
    *   101-200: Unhealthy (Orange)
    *   201-300: Very Unhealthy (Red)
    *   300+: Hazardous (Purple)

### 2.2 Operational Workflow

#### Phase 1: Data Acquisition
1.  **Sensing:** The ESP32 constantly polls analog status of all MQ sensors and digital status of IR sensors.
2.  **Hosting:** The ESP32 hosts a local HTTP server exposing `/data` (JSON sensor values) and `/cmd` (Motor control).
3.  **Polling:** The frontend (Terminal or Streamlit) polls the ESP32 IP (`192.168.4.1`) or generates simulated data if disconnected.

#### Phase 2: Monitoring & Control
1.  **Visualization:** Data is streamed into rolling buffers (History=60s).
2.  **Display:** Real-time line charts update for individual gases and the aggregate GPI.
3.  **Control:** User sends commands (e.g., `forward`, `stop`, `buzzer on`).
    *   *Frontend* sends HTTP GET request to ESP32.
    *   *ESP32* interprets command and triggers L298N driver.
4.  **Autonomous Safety:**
    *   If GPI exceeds critical threshold (e.g., >200), the robot autonomously halts and sounds the buzzer.

#### Phase 3: AI-Enhanced Reporting
1.  **Trigger:** User issues `report` command in the Terminal.
2.  **Data Transmission:** Browser sends collected sensor history buffer (JSON) to the Flask Report Server (`localhost:5000`).
3.  **Processing:**
    *   Server converts JSON to Pandas DataFrame.
    *   Generates statistical summaries (Min, Max, Mean, Std Dev).
    *   Detects anomalies (e.g., "Trending High").
4.  **AI Analysis:**
    *   A structured prompt containing the statistics is sent to the **Gemma 2 9B** model via **Ollama**.
    *   The AI generates an Executive Summary, Detailed Analysis, and Safety Recommendations.
5.  **Compilation:**
    *   Matplotlib generates high-res static images of the trends.
    *   ReportLab compiles text, tables, and images into a professional PDF.
6.  **Delivery:** PDF is streamed back to the browser for automatic download.

## 3. Directory Structure Summary

```
/pranbot
├── main.ino            # ESP32 Firmware (C++)
├── terminal.html       # Web Interface Entry Point
├── terminal.js         # Web Interface Logic & Charts
├── terminal.css        # Web Interface Styling
├── dashboard .py       # Streamlit Dashboard (Python)
├── report_server.py    # Flask AI Report Server (Python)
├── requirements.txt    # Python Dependencies
└── /tests              # Simulation Data & Tests
```
