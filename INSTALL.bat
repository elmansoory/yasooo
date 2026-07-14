@echo off
chcp 65001 >nul
title تثبيت نظام تحليل التزلج - Installation
color 0B

echo.
echo ================================================================
echo    🎿 تثبيت نظام تحليل التزلج 🎿
echo    Installing Skating Analysis System
echo ================================================================
echo.

REM ============================================================
REM  الخطوة 1: التحقق من Python
REM ============================================================
echo [1/5] التحقق من Python...
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ [خطأ] Python غير مثبت!
    echo ❌ [ERROR] Python is not installed!
    echo.
    echo يرجى تثبيت Python أولاً من:
    echo Please install Python first from:
    echo https://www.python.org/downloads/
    echo.
    echo ⚠️ مهم: فعّل خيار "Add Python to PATH" أثناء التثبيت
    echo ⚠️ Important: Enable "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

python --version
echo ✅ Python مثبت بنجاح
echo.

REM ============================================================
REM  الخطوة 2: ترقية pip
REM ============================================================
echo [2/5] ترقية pip...
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% equ 0 (
    echo ✅ تم ترقية pip
) else (
    echo ⚠️ تحذير: فشل ترقية pip ^(سيتم المتابعة^)
)
echo.

REM ============================================================
REM  الخطوة 3: تثبيت المكتبات الأساسية
REM ============================================================
echo [3/5] تثبيت المكتبات الأساسية...
echo [3/5] Installing core libraries...
echo.
echo 📦 جاري تثبيت المكتبات من requirements-minimal.txt
echo 📦 Installing libraries from requirements-minimal.txt
echo.
pip install -r requirements-minimal.txt
if %errorlevel% neq 0 (
    echo.
    echo ❌ [خطأ] فشل تثبيت المكتبات الأساسية
    echo ❌ [ERROR] Failed to install core libraries
    echo.
    echo جرب التثبيت اليدوي:
    echo Try manual installation:
    echo pip install -r requirements-minimal.txt
    echo.
    pause
    exit /b 1
)
echo ✅ تم تثبيت المكتبات الأساسية
echo.

REM ============================================================
REM  الخطوة 4: تثبيت المكتبات المتقدمة (اختياري)
REM ============================================================
echo [4/5] تثبيت المكتبات المتقدمة (اختياري)...
echo [4/5] Installing advanced libraries (optional)...
echo.
echo ℹ️ ملاحظة: هذه الخطوة اختيارية - للميزات المتقدمة فقط
echo ℹ️ Note: This step is optional - for advanced features only
echo.
echo المكتبات المتقدمة تشمل: TensorFlow, PyTorch, OpenCV
echo Advanced libraries include: TensorFlow, PyTorch, OpenCV
echo.
echo ⚠️ قد تأخذ 10-30 دقيقة وتحتاج 5+ GB مساحة
echo ⚠️ May take 10-30 minutes and require 5+ GB space
echo.
set /p install_advanced="هل تريد تثبيت المكتبات المتقدمة؟ (y/n): "
if /i "%install_advanced%"=="y" (
    echo.
    echo ⏳ جاري التثبيت... قد يأخذ وقتاً طويلاً
    echo ⏳ Installing... this may take a long time
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ⚠️ [تحذير] بعض المكتبات المتقدمة فشلت
        echo ⚠️ [WARNING] Some advanced libraries failed
        echo.
        echo ✅ لكن المكتبات الأساسية مثبتة - يمكنك المتابعة
        echo ✅ But core libraries are installed - you can continue
        echo.
    )
) else (
    echo.
    echo ⏩ تم تخطي المكتبات المتقدمة
    echo ⏩ Skipped advanced libraries
    echo.
    echo يمكنك تثبيتها لاحقاً بتشغيل:
    echo You can install them later by running:
    echo pip install -r requirements.txt
    echo.
)
echo.

REM ============================================================
REM  الخطوة 5: استيراد البيانات
REM ============================================================
echo [5/5] استيراد البيانات إلى قاعدة البيانات...
echo [5/5] Importing data to database...
echo.

REM التحقق من وجود ملفات البيانات
if not exist "data\members.xlsx" (
    echo ❌ [خطأ] ملف data\members.xlsx غير موجود
    echo ❌ [ERROR] data\members.xlsx not found
    echo.
    echo يرجى التأكد من وجود مجلد data مع ملفات Excel
    echo Please ensure data folder exists with Excel files
    echo.
    pause
    exit /b 1
)

python import_all_data.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ [خطأ] فشل استيراد البيانات
    echo ❌ [ERROR] Failed to import data
    echo.
    echo الأسباب المحتملة:
    echo Possible reasons:
    echo 1. openpyxl غير مثبتة: pip install openpyxl
    echo 2. ملفات Excel غير موجودة في مجلد data/
    echo 3. ملفات Excel تالفة
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    ✅ اكتمل التثبيت بنجاح!
echo    ✅ Installation Completed Successfully!
echo ================================================================
echo.
echo 🎉 كل شيء جاهز!
echo 🎉 Everything is ready!
echo.
echo 🚀 لتشغيل البرنامج:
echo 🚀 To run the application:
echo.
echo    1. اضغط مرتين على START.bat
echo    1. Double-click START.bat
echo.
echo    أو شغّل في Command Prompt:
echo    Or run in Command Prompt:
echo    python -m streamlit run app.py
echo.
echo ================================================================
echo.
echo 📚 ملفات المساعدة المتاحة:
echo 📚 Available help files:
echo.
echo    - HOW_TO_USE.md          دليل الاستخدام الشامل
echo    - WINDOWS_SETUP.md       دليل التثبيت على Windows
echo    - TROUBLESHOOTING.md     حل المشاكل الشائعة
echo    - QUICKSTART.md          بدء سريع
echo.
echo ================================================================
echo.
pause
