@echo off
echo ========================================
echo MIT Mysore Timetable System
echo Starting Backend Server...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if requirements are installed
echo Checking dependencies...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK!
echo.

REM Start the backend server
echo Starting Flask server on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python backend_ga.py

pause
