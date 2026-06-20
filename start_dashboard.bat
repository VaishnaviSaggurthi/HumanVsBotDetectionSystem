@echo off
echo ========================================
echo   Bot Detection System - Dashboard
echo ========================================
echo.
echo Starting Streamlit dashboard...
echo Dashboard will be available at: http://localhost:8501
echo.
cd dashboard
streamlit run dashboard.py --server.port 8501
pause