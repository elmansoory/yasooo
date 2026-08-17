@echo off
setlocal EnableDelayedExpansion
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
    echo Python 3.11 not found. Attempting automatic installation...
    echo.

    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        echo Installing Python 3.11 via winget ^(Windows Package Manager^)...
        winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1
    ) else (
        echo winget not available. Downloading the official installer instead...
        set "PY_INSTALLER=!TEMP!\python-3.11.9-amd64.exe"
        powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '!PY_INSTALLER!'" >> "%LOG%" 2>&1
        if exist "!PY_INSTALLER!" (
            echo Running the Python installer silently ^(this may take a minute^)...
            "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 >> "%LOG%" 2>&1
        ) else (
            echo.
            echo ERROR: Could not download the Python installer automatically.
            echo Please install it manually from:
            echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
            echo Make sure to check "Add Python to PATH" during installation.
            echo.
            pause
            exit /b 1
        )
    )

    REM Refresh PATH for this session so a newly installed Python/py launcher is found
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=%%B;%PATH%"
    for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "PATH=%%B;%PATH%"

    %PYTHON% --version >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo ERROR: Automatic installation did not complete successfully.
        echo Please close this window, install Python 3.11 manually from:
        echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
        echo ^(check "Add Python to PATH"^), then run YASOOO.bat again.
        echo.
        pause
        exit /b 1
    )
    echo [OK] Python 3.11 installed successfully.
) else (
    echo [OK] Python 3.11 found.
)

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
    %PIP% install --quiet "mediapipe==0.10.14" "protobuf>=3.20,<5" >> "%LOG%" 2>&1
)

REM protobuf 5.x removes MessageFactory.GetPrototype, which mediapipe's
REM generated _pb2 files still call — this crashes the app on import with
REM "'MessageFactory' object has no attribute 'GetPrototype'". Some other
REM package may have upgraded protobuf past 5.0 even if mediapipe itself
REM imported fine before, so re-check and pin it down every run.
%PYTHON% -c "import google.protobuf as p; import sys; sys.exit(0 if int(p.__version__.split('.')[0]) < 5 else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo Fixing protobuf version for MediaPipe compatibility...
    %PIP% install --quiet "protobuf>=3.20,<5" >> "%LOG%" 2>&1
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
echo [3b/5] Merging Excel data into database...
cd /d "%APP_DIR%"
%PYTHON% merge_all_data.py >> "%LOG%" 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Data merge had issues. Check launch.log for details.
) else (
    echo [OK] All Excel data merged.
)

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
