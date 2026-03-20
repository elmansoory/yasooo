@echo off
chcp 65001 >nul
title نظام تحليل التزلج - Skating Analysis System
color 0A

echo.
echo ========================================
echo    نظام تحليل التزلج
echo    Skating Analysis System
echo ========================================
echo.

REM التحقق من تثبيت Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Python غير مثبت!
    echo [ERROR] Python is not installed!
    echo.
    echo يرجى تثبيت Python من: https://www.python.org/downloads/
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python مثبت بنجاح
echo.

REM التحقق من تثبيت Streamlit
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [تحذير] المكتبات غير مثبتة
    echo [WARNING] Libraries not installed
    echo.
    echo جاري تثبيت المكتبات المطلوبة...
    echo Installing required libraries...
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [خطأ] فشل تثبيت المكتبات
        echo [ERROR] Failed to install libraries
        pause
        exit /b 1
    )
)

echo [✓] جميع المكتبات جاهزة
echo [✓] All libraries ready
echo.

REM التحقق من وجود قاعدة البيانات
if not exist "skating_database.db" (
    echo [تحذير] قاعدة البيانات غير موجودة
    echo [WARNING] Database not found
    echo.
    echo جاري إنشاء قاعدة البيانات...
    echo Creating database...
    python import_members.py
    python import_attendance.py
)

echo [✓] قاعدة البيانات جاهزة
echo [✓] Database ready
echo.

echo ========================================
echo    جاري تشغيل البرنامج...
echo    Starting application...
echo ========================================
echo.
echo سيتم فتح البرنامج في المتصفح تلقائياً
echo The application will open in your browser automatically
echo.
echo للإيقاف: اضغط Ctrl+C
echo To stop: Press Ctrl+C
echo.

REM تشغيل التطبيق
streamlit run app.py

pause
