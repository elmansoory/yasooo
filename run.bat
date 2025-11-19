@echo off
REM سكريبت تشغيل نظام تحليل التزلج الفني - Windows
REM Figure Skating Analysis System - Run Script for Windows

echo ===============================================================
echo    Figure Skating Analysis System - yasooo
echo ===============================================================
echo.

REM التحقق من Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10 or later
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM التحقق من قاعدة البيانات
if not exist "skating_analysis.db" (
    echo [WARNING] Database not found, will be created on first run...
)

REM تثبيت المتطلبات
echo Checking requirements...
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -q -r requirements.txt
    echo [OK] Requirements installed
) else (
    echo [OK] All requirements are installed
)

echo.
echo ===============================================================
echo Starting application...
echo ===============================================================
echo.
echo The app will open in your browser at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.
echo ===============================================================
echo.

REM تشغيل التطبيق
streamlit run app.py

pause
