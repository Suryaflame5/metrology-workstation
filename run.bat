@echo off
REM Metrology Workstation Launcher
REM This script launches the Metrology Workstation desktop application

echo Starting Metrology Workstation...
echo.

REM Launch the desktop application
python desktop_app.py

REM If the application exits, pause to show any error messages
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred while starting Metrology Workstation
    echo Error code: %ERRORLEVEL%
    pause
)