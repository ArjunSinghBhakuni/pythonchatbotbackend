@echo off
echo Starting Gemini AI Backend...
echo ================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

REM Start the backend
echo Starting Gemini Backend...
python run_gemini_backend.py

pause




