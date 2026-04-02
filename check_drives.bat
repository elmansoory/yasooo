@echo off
echo ================================================
echo   Drive & Folder Diagnostic - فحص الأقراص
echo ================================================
echo.

echo Checking all available drives...
echo ================================
echo.

for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        echo [OK] Drive %%d: exists

        REM Check for "Off Ice" folder
        if exist "%%d:\Off Ice" (
            echo     ^|
            echo     +-- [FOUND] "%%d:\Off Ice" folder exists!
            echo.
            echo ================================================
            echo SUCCESS! Your videos are in: %%d:\Off Ice
            echo ================================================
            echo.
            echo Files in this folder:
            dir /b "%%d:\Off Ice" 2>nul | findstr /i ".mp4 .avi .mov .mkv .wmv"
            echo.
        )
    )
)

echo.
echo ================================================
echo Checking for external drives and USB...
echo ================================================
wmic logicaldisk get deviceid,volumename,description 2>nul
echo.

echo ================================================
echo Checking for "Off Ice" folder in all drives...
echo ================================================
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        if exist "%%d:\Off Ice" (
            echo.
            echo [FOUND] %%d:\Off Ice
            echo Total videos in %%d:\Off Ice:
            dir /s /b "%%d:\Off Ice\*.mp4" "%%d:\Off Ice\*.avi" "%%d:\Off Ice\*.mov" 2>nul | find /c /v ""
        )
    )
)

echo.
echo ================================================
echo Searching for folders with "ice" in the name...
echo ================================================
for %%d in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        dir /ad /b "%%d:\*ice*" 2>nul | findstr /i "ice" && echo Found in %%d:\
    )
)

echo.
echo ================================================
echo INSTRUCTIONS:
echo ================================================
echo 1. Look for "[FOUND]" messages above
echo 2. Note the correct drive letter
echo 3. Use that path in the annotation tool
echo ================================================
pause
