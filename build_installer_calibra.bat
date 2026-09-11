@echo off
REM Build Professional Windows Installer with CALIBRA Branding
REM This script uses Inno Setup to create a distributable installer

echo Building Metrology Workstation Professional Installer...
echo.

REM Check if Inno Setup compiler is available
where iscc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Inno Setup compiler (iscc) not found in PATH.
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    echo.
    echo Alternative: Copy setup_calibra.iss to a machine with Inno Setup and compile it there.
    pause
    exit /b 1
)

REM Build the installer
iscc setup_calibra.iss

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installer build failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Installer built successfully!
echo Output: MetrologyWorkstation-Setup-7.0.0.exe
echo.
echo The installer is ready for distribution.
echo.
pause