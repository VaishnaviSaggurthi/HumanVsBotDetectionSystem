@echo off
echo ========================================
echo   Bot Detection System - Frontend
echo ========================================
echo.
echo Starting frontend web server...
echo Website will be available at: http://localhost:8000
echo.
cd frontend
python -m http.server 8000
pause