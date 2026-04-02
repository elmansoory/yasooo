@echo off
echo ================================================
echo   Video Finder - ابحث عن الفيديوهات
echo ================================================
echo.

echo Searching in common locations...
echo.

echo === C:\Users\%USERNAME%\Videos ===
dir /b "C:\Users\%USERNAME%\Videos\*.mp4" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Videos\*.avi" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Videos\*.mov" 2>nul | find /c /v ""
echo.

echo === C:\Users\%USERNAME%\Downloads ===
dir /b "C:\Users\%USERNAME%\Downloads\*.mp4" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Downloads\*.avi" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Downloads\*.mov" 2>nul | find /c /v ""
echo.

echo === C:\Users\%USERNAME%\Desktop ===
dir /b "C:\Users\%USERNAME%\Desktop\*.mp4" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Desktop\*.avi" 2>nul | find /c /v ""
dir /b "C:\Users\%USERNAME%\Desktop\*.mov" 2>nul | find /c /v ""
echo.

echo === D:\ Drive ===
if exist D:\ (
    dir /b /s D:\*.mp4 2>nul | find /c /v ""
    dir /b /s D:\*.avi 2>nul | find /c /v ""
)
echo.

echo ================================================
echo Enter the full path where your videos are:
echo Example: D:\My Videos\Skating
echo ================================================
set /p VIDEO_PATH="Path: "

echo.
echo Scanning: %VIDEO_PATH%
echo.

if exist "%VIDEO_PATH%" (
    dir /b /s "%VIDEO_PATH%\*.mp4" "%VIDEO_PATH%\*.avi" "%VIDEO_PATH%\*.mov" "%VIDEO_PATH%\*.mkv" 2>nul
    echo.
    echo Done! Found videos above.
) else (
    echo Error: Path not found!
)

pause
