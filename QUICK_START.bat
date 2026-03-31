@echo off
echo ===============================================================
echo    Quick Start - Figure Skating Analysis System
echo ===============================================================
echo.

echo Step 1: Creating database...
python setup_database.py

echo.
echo ===============================================================
echo Step 2: Checking dependencies...
echo ===============================================================
echo.

echo Checking MediaPipe...
python -c "import mediapipe as mp; print('MediaPipe OK - Professional features available')" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] MediaPipe not found or not working properly
    echo Professional features will not be available.
    echo.
    echo To fix: pip install mediapipe==0.10.9
    echo See INSTALL_MEDIAPIPE.md for details
    echo.
)

echo.
echo ===============================================================
echo Step 3: Starting application...
echo ===============================================================
echo.
echo Choose application:
echo   1. Basic App (recommended if MediaPipe issue)
echo   2. Professional App (requires MediaPipe)
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo Starting Basic App...
    python -m streamlit run app.py
) else if "%choice%"=="2" (
    echo Starting Professional App...
    python -m streamlit run professional_app.py
) else (
    echo Invalid choice. Starting Basic App by default...
    python -m streamlit run app.py
)

pause
