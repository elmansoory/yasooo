@echo off
echo ===============================================================
echo    Quick Start - Figure Skating Analysis System
echo ===============================================================
echo.

echo Step 1: Creating database...
python setup_database.py

echo.
echo ===============================================================
echo Step 2: Starting application...
echo ===============================================================
echo.

python -m streamlit run app.py

pause
