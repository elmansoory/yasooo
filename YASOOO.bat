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
set "LOG=%APP_DIR%launch.log"

echo [1/5] Checking Python...
call :detect_python
if not defined PYTHON (
    echo No usable Python installation found. Attempting automatic installation...
    echo.

    REM Attempt 1: winget (Windows Package Manager) — may be missing,
    REM blocked by policy, or fail with a generic "path not specified"
    REM error if App Installer isn't registered correctly. Treat any
    REM failure here as non-fatal and fall through to the direct
    REM download instead of giving up.
    where winget >nul 2>&1
    if !errorlevel! equ 0 (
        echo Installing Python 3.11 via winget ^(Windows Package Manager^)...
        winget install --id Python.Python.3.11 -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity >> "%LOG%" 2>&1
        if !errorlevel! neq 0 (
            echo winget install did not complete ^(see launch.log^) — will try the direct download next.
        )
    ) else (
        echo winget not found on this system.
    )

    call :refresh_path
    call :detect_python
    if not defined PYTHON (
        REM Attempt 2: download the official installer directly and run it silently
        echo Downloading the official Python installer instead...
        set "PY_INSTALLER=!TEMP!\python-3.11.9-amd64.exe"
        powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '!PY_INSTALLER!'" >> "%LOG%" 2>&1
        if exist "!PY_INSTALLER!" (
            echo Running the Python installer silently ^(this may take a minute^)...
            "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 >> "%LOG%" 2>&1
            call :refresh_path
            call :detect_python
        ) else (
            echo ERROR: Could not download the Python installer automatically.
        )
    )

    if not defined PYTHON (
        color 0C
        echo.
        echo ERROR: Automatic installation did not complete successfully.
        echo Details were logged to: !LOG!
        echo.
        echo This script already tried: the py launcher (3.11/3/any),
        echo plain "python", refreshing PATH from the registry, and
        echo searching the standard install folders directly for
        echo python.exe — none of them found a working Python.
        echo.
        echo Please open a Command Prompt and run: where python.exe
        echo If that shows a path, Python is installed somewhere this
        echo script didn't check — tell the developer that exact path.
        echo.
        echo Otherwise, install Python manually from:
        echo https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
        echo ^(check "Add Python to PATH"^), then run YASOOO.bat again.
        echo.
        pause
        exit /b 1
    )
    echo [OK] Python installed successfully: !PYTHON!
) else (
    echo [OK] Python found: !PYTHON!
)

set "PIP=%PYTHON% -m pip"
set "STREAMLIT=%PYTHON% -m streamlit"

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
exit /b 0

REM ============================================================
REM  Refresh PATH in this session so a freshly-installed python/py
REM  launcher is picked up without closing and reopening the
REM  terminal. Uses PowerShell/.NET to read+expand both the Machine
REM  and User PATH from the registry — a plain `reg query` returns
REM  the raw unexpanded string (e.g. literal "%USERPROFILE%\..."),
REM  which silently fails to resolve when appended to PATH as-is.
REM ============================================================
:refresh_path
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "try { ([System.Environment]::GetEnvironmentVariable('Path','Machine')) + ';' + ([System.Environment]::GetEnvironmentVariable('Path','User')) } catch { '' }"`) do (
    if not "%%P"=="" set "PATH=%%P;!PATH!"
)
REM Also probe the two most common per-user/per-machine Python
REM install folders directly, in case PATH still didn't pick it up.
for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do set "PATH=%%D;%%D\Scripts;%PATH%"
for /d %%D in ("%ProgramFiles%\Python3*") do set "PATH=%%D;%%D\Scripts;%PATH%"
goto :eof

REM ============================================================
REM  Detect a usable Python 3 install without forcing an exact
REM  version. Sets PYTHON to whichever launcher command works,
REM  or clears it if nothing usable was found. Prefers 3.11 (the
REM  version this app is tested with) but happily falls back to
REM  any other Python 3 already on the machine — most crashes
REM  reported as "Python not found" actually have Python installed
REM  under a different version/launcher than the one hardcoded here.
REM ============================================================
:detect_python
set "PYTHON="
py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 ( set "PYTHON=py -3.11" & goto :eof )
py -3 --version >nul 2>&1
if !errorlevel! equ 0 ( set "PYTHON=py -3" & goto :eof )
py --version >nul 2>&1
if !errorlevel! equ 0 ( set "PYTHON=py" & goto :eof )
REM Plain "python" is checked next — on a machine with no real Python,
REM Windows sometimes shadows this with a no-op Microsoft Store alias.
python --version >nul 2>&1
if !errorlevel! equ 0 ( set "PYTHON=python" & goto :eof )

REM Last resort: none of the launcher commands worked — this usually
REM means Python IS installed but this process's PATH is stale/wrong
REM (a well-known Windows quirk where windows opened from Explorer can
REM keep an outdated environment even after installers update PATH).
REM Search the well-known install folders directly for python.exe and
REM call it by its full path, completely bypassing PATH and the py
REM launcher.
for /f "delims=" %%F in ('dir /b /s /a-d "%LocalAppData%\Programs\Python\python.exe" 2^>nul') do (
    if not defined PYTHON set "PYTHON="%%F""
)
if defined PYTHON ( "!PYTHON!" --version >nul 2>&1 & if !errorlevel! equ 0 goto :eof )
set "PYTHON="
for %%R in ("%ProgramFiles%\Python3*" "!ProgramFiles(x86)!\Python3*" "C:\Python3*") do (
    if exist "%%~R\python.exe" if not defined PYTHON set "PYTHON="%%~R\python.exe""
)
if defined PYTHON ( "!PYTHON!" --version >nul 2>&1 & if !errorlevel! equ 0 goto :eof )
set "PYTHON="
goto :eof
