@echo off
echo ========================================
echo MIT Mysore Timetable Generation Server
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask server...
echo Server will run on http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
python flask_server.py
pause
