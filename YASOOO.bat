@echo off
chcp 65001 >nul 2>&1
title ياسو - نظام تحليل التزلج
color 0A
cls

:: ================================================================
::   YASOOO — Figure Skating Analysis System
::   تشغيل تلقائي كامل بدون أي تدخل
:: ================================================================

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║         نظام تحليل التزلج الفني  YASOOO         ║
echo  ║          Figure Skating Analysis System          ║
echo  ╚══════════════════════════════════════════════════╝
echo.

set "APP_DIR=%~dp0"
set "PYTHON=py -3.11"
set "PIP=py -3.11 -m pip"
set "STREAMLIT=py -3.11 -m streamlit"
set "LOG=%APP_DIR%launch.log"

:: ── تحقق من Python 3.11 ────────────────────────────────────────
echo  [1/5] التحقق من Python 3.11...
%PYTHON% --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo  ╔══════════════════════════════════════════════════╗
    echo  ║  Python 3.11 غير مثبت — يرجى تثبيته أولاً       ║
    echo  ║  https://www.python.org/downloads/release/python-3119/   ║
    echo  ║  python-3.11.9-amd64.exe                        ║
    echo  ╚══════════════════════════════════════════════════╝
    echo.
    pause
    exit /b 1
)
echo  [✓] Python 3.11 جاهز

:: ── تثبيت المكتبات تلقائياً إذا ناقصة ────────────────────────
echo  [2/5] التحقق من المكتبات...
%PYTHON% -c "import streamlit, plotly, pandas, numpy, cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo  ... تثبيت المكتبات الأساسية تلقائياً
    %PIP% install --quiet --upgrade pip >> "%LOG%" 2>&1
    %PIP% install --quiet streamlit plotly pandas numpy opencv-python openpyxl sqlalchemy >> "%LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo  [!] بعض المكتبات فشلت — انظر launch.log للتفاصيل
    )
)

:: تثبيت mediapipe اختياري (يفشل بصمت إذا غير متاح)
%PYTHON% -c "import mediapipe" >nul 2>&1
if %errorlevel% neq 0 (
    echo  ... تثبيت mediapipe للتحليل المتقدم...
    %PIP% install --quiet "mediapipe==0.10.14" >> "%LOG%" 2>&1
)
echo  [✓] المكتبات جاهزة

:: ── إعداد قاعدة البيانات إذا غير موجودة ─────────────────────
echo  [3/5] التحقق من قاعدة البيانات...
if not exist "%APP_DIR%skating_database.db" (
    echo  ... إنشاء قاعدة البيانات وإستيراد البيانات...
    cd /d "%APP_DIR%"
    %PYTHON% import_all_data.py >> "%LOG%" 2>&1
    if %errorlevel% neq 0 (
        echo  [!] استيراد البيانات فشل — سيتم إنشاء قاعدة بيانات فارغة
    )
)
echo  [✓] قاعدة البيانات جاهزة

:: ── مسح الفيديوهات تلقائياً ──────────────────────────────────
echo  [4/5] مسح الفيديوهات على الجهاز...
cd /d "%APP_DIR%"
%PYTHON% setup_auto.py --scan-videos >> "%LOG%" 2>&1
echo  [✓] اكتمل مسح الفيديوهات — راجع التطبيق لعرض النتائج

:: ── تشغيل التطبيق ────────────────────────────────────────────
echo  [5/5] تشغيل التطبيق...
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  سيفتح المتصفح تلقائياً على:                    ║
echo  ║  http://localhost:8501                           ║
echo  ║                                                  ║
echo  ║  للإيقاف: اضغط Ctrl+C في هذه النافذة           ║
echo  ╚══════════════════════════════════════════════════╝
echo.

cd /d "%APP_DIR%"
%STREAMLIT% run final_app.py --server.headless false --browser.gatherUsageStats false

pause
