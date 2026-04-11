@echo off
echo ================================================
echo تثبيت ميزات الذكاء الاصطناعي
echo AI Features Installation
echo ================================================
echo.

echo [1/3] Checking Python version...
python --version
echo.

echo [2/3] Installing MediaPipe (required for AI analysis)...
python -m pip install --upgrade pip
python -m pip install mediapipe opencv-python numpy
echo.

echo [3/3] Testing import...
python -c "import mediapipe as mp; print('✅ MediaPipe:', mp.__version__)"
python -c "import cv2; print('✅ OpenCV:', cv2.__version__)"
python -c "import numpy as np; print('✅ NumPy:', np.__version__)"
echo.

echo ================================================
echo Installation Complete!
echo.
echo Now run:
echo   python -m streamlit run ultimate_app.py
echo ================================================
pause
