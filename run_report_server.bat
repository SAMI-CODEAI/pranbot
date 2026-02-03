@echo off
echo ==================================================
echo   PRAN-BOT REPORT SERVER LAUNCHER
echo ==================================================

if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [INFO] Installing requirements...
pip install -r requirements.txt

echo [INFO] Starting Flask Server...
python report_server.py

pause
