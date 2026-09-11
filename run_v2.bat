@echo off
REM Metrology V2 Launcher
REM This script launches the Metrology V2 desktop application

echo Starting Metrology V2...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.12+ and add it to your PATH
    pause
    exit /b 1
)

REM Launch the v2 desktop application
python -m metrology_v2.desktop.application

REM If the application exits, pause to show any error messages
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred while starting Metrology V2
    echo Error code: %ERRORLEVEL%
    echo.
    echo Make sure all dependencies are installed:
    echo pip install -r requirements.txt
    pause
)