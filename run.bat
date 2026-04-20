@echo off
REM Market Regime Detection Engine - Startup Script for Windows

echo.
echo ============================================
echo Market Regime Detection Engine
echo Frontend Startup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [✓] Python found
echo.

REM Check if virtual environment exists
if exist venv (
    echo [✓] Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [✓] Virtual environment created
)

echo.
echo Installing/updating dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [✓] Dependencies installed
echo.

echo ============================================
echo Starting Flask Application...
echo ============================================
echo.
echo INFO: Flask server is starting...
echo INFO: Open your browser and go to:
echo.
echo        http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

REM Run the Flask app
python app.py

pause
