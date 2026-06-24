@echo off
chcp 65001 >nul
title نظام تحليل التزلج - Skating Analysis System
color 0B

cd /d "%~dp0"

echo.
echo ============================================================
echo            نظام تحليل اداء لاعبي التزلج
echo            Skating Analysis ^& Coaching System
echo ============================================================
echo.

REM ===== 1) التحقق من Python =====
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Python غير مثبت على الجهاز!
    echo [ERROR] Python is not installed!
    echo.
    echo حمل Python من: https://www.python.org/downloads/
    echo مهم: فعّل خيار "Add Python to PATH" اثناء التثبيت
    echo.
    pause
    exit /b 1
)
echo [✓] Python مثبت
echo.

REM ===== 2) التحقق من المكتبات وتثبيتها تلقائيا =====
echo [...] جاري التحقق من المكتبات المطلوبة
python -c "import streamlit, pandas, plotly, openpyxl, numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] بعض المكتبات ناقصة - جاري التثبيت التلقائي...
    echo     قد يستغرق هذا بضع دقائق في المرة الاولى فقط
    echo.
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install -r requirements-minimal.txt
    if %errorlevel% neq 0 (
        echo.
        echo [خطأ] فشل تثبيت المكتبات - تحقق من اتصال الانترنت
        pause
        exit /b 1
    )
    echo.
    echo [✓] تم تثبيت المكتبات بنجاح
) else (
    echo [✓] جميع المكتبات جاهزة
)
echo.

REM ===== 3) التحقق من قاعدة البيانات =====
if not exist "skating_database.db" (
    echo [!] قاعدة البيانات غير موجودة - جاري انشاؤها...
    python setup_database.py
    if %errorlevel% neq 0 (
        echo [خطأ] فشل انشاء قاعدة البيانات
        pause
        exit /b 1
    )
    echo [✓] تم انشاء قاعدة البيانات
) else (
    echo [✓] قاعدة البيانات جاهزة
)
echo.

echo ============================================================
echo    جاري تشغيل البرنامج... سيفتح في المتصفح تلقائيا
echo    Starting... The app will open in your browser
echo ============================================================
echo.
echo    الرابط: http://localhost:8501
echo    للايقاف: اغلق هذه النافذة او اضغط Ctrl+C
echo.

REM ===== 4) فتح المتصفح تلقائيا بعد 5 ثوان =====
start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:8501"

REM ===== 5) تشغيل التطبيق =====
python -m streamlit run app.py --server.port 8501 --server.headless true

echo.
echo تم ايقاف البرنامج.
pause
