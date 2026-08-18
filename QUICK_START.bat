@echo off
echo ===============================================================
echo    Quick Start - YASOOO Figure Skating Analysis System
echo ===============================================================
echo.
echo NOTE: final_app.py is the current application. It creates and
echo repairs its own database schema (skating_database.db) on
echo startup, so the old setup_database.py / app.py / professional_app.py
echo (legacy "members" table schema) are no longer used here.
echo.

echo Step 1: Checking dependencies...
echo.

echo Checking MediaPipe...
python -c "import mediapipe as mp; print('MediaPipe OK - AI analysis features available')" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] MediaPipe not found or not working properly
    echo AI movement-analysis features will not be available.
    echo.
    echo To fix: pip install mediapipe==0.10.14
    echo See INSTALL_MEDIAPIPE.md for details
    echo.
)

echo.
echo ===============================================================
echo Step 2: Starting application...
echo ===============================================================
echo.

python -m streamlit run final_app.py

pause
