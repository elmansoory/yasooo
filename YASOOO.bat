@echo off
chcp 65001 >nul 2>&1
title YASOOO - Figure Skating Analysis System
color 0A
cls

echo.
echo ================================================
echo   YASOOO - Figure Skating Analysis System
echo   نظام تحليل التزلج الفني
echo ================================================
echo.

set "APP_DIR=%~dp0"
set "PYTHON=py -3.11"
set "PIP=py -3.11 -m pip"
set "STREAMLIT=py -3.11 -m streamlit"
set "LOG=%APP_DIR%launch.log"

echo [1/5] Checking Python 3.11...
%PYTHON% --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERROR: Python 3.11 is not installed.
    echo.
    echo Please download and install it from:
    echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
echo [OK] Python 3.11 found.

echo.
echo [2/5] Checking required libraries...
%PYTHON% -c "import streamlit, plotly, pandas, numpy, cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing missing libraries... (this may take a few minutes)
    %PIP% install --quiet --upgrade pip >> "%LOG%" 2>&1
    %PIP% install --quiet streamlit plotly pandas numpy opencv-python openpyxl sqlalchemy >> "%LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: Some libraries failed. Check launch.log for details.
    )
)

%PYTHON% -c "import mediapipe" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing mediapipe for AI analysis...
    %PIP% install --quiet "mediapipe==0.10.14" >> "%LOG%" 2>&1
)
echo [OK] Libraries ready.

echo.
echo [3/5] Checking database...
if not exist "%APP_DIR%skating_database.db" (
    echo Creating database...
    cd /d "%APP_DIR%"
    %PYTHON% import_all_data.py >> "%LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo WARNING: Data import failed. Starting with empty database.
    )
)
echo [OK] Database ready.

echo.
echo [4/5] Scanning device for video files...
cd /d "%APP_DIR%"
%PYTHON% setup_auto.py --scan-videos >> "%LOG%" 2>&1
echo [OK] Video scan complete. Check the app to see results.

echo.
echo [5/5] Launching application...
echo.
echo ================================================
echo   Opening browser at: http://localhost:8501
echo   Press Ctrl+C in this window to stop the app.
echo ================================================
echo.

cd /d "%APP_DIR%"
%STREAMLIT% run final_app.py --server.headless false --browser.gatherUsageStats false

pause
