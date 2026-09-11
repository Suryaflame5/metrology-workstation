@echo off
REM Metrology Workstation Installer Builder
REM This script builds the desktop application with the CALIBRA icon

echo Building Metrology Workstation Installer with CALIBRA icon...
echo.

REM Install PyInstaller if not available
python -m pip install pyinstaller

REM Build the standalone executable with the icon
python compile_standalone_exe.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\MetrologyWorkstation\MetrologyWorkstation.exe
echo.
pause