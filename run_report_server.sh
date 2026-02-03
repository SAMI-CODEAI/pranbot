#!/bin/bash
echo "=================================================="
echo "  PRAN-BOT REPORT SERVER LAUNCHER"
echo "=================================================="

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python -m venv .venv
fi

echo "[INFO] Activating virtual environment..."
source .venv/Scripts/activate

echo "[INFO] Installing requirements..."
pip install -r requirements.txt

echo "[INFO] Starting Flask Server..."
python report_server.py
