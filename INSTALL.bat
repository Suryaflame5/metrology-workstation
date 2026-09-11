@echo off
REM Metrology Workstation v7.0.0 - Installation Script
REM This script extracts and sets up the Metrology Workstation desktop application

echo =======================================================
echo Metrology Workstation v7.0.0 - Installation
echo =======================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [INFO] Running with standard user privileges
)

echo.
echo [1/3] Extracting application files...
powershell -Command "Expand-Archive -Path 'dist\MetrologyWorkstation-v7.0.0-Windows-x64.zip' -DestinationPath '%LOCALAPPDATA%\MetrologyWorkstation' -Force"

if %errorLevel% neq 0 (
    echo [ERROR] Failed to extract files
    pause
    exit /b 1
)

echo [OK] Application files extracted successfully
echo.

echo [2/3] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Metrology Workstation.lnk'); $Shortcut.TargetPath = '%LOCALAPPDATA%\MetrologyWorkstation\MetrologyWorkstation.exe'; $Shortcut.WorkingDirectory = '%LOCALAPPDATA%\MetrologyWorkstation'; $Shortcut.Description = 'Metrology Workstation v7.0.0'; $Shortcut.Save()"

if %errorLevel% neq 0 (
    echo [WARNING] Failed to create desktop shortcut (non-critical)
) else (
    echo [OK] Desktop shortcut created
)

echo.
echo [3/3] Creating Start Menu entry...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Metrology Workstation" mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Metrology Workstation"
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Metrology Workstation\Metrology Workstation.lnk'); $Shortcut.TargetPath = '%LOCALAPPDATA%\MetrologyWorkstation\MetrologyWorkstation.exe'; $Shortcut.WorkingDirectory = '%LOCALAPPDATA%\MetrologyWorkstation'; $Shortcut.Description = 'Metrology Workstation v7.0.0'; $Shortcut.Save()"

if %errorLevel% neq 0 (
    echo [WARNING] Failed to create Start Menu entry (non-critical)
) else (
    echo [OK] Start Menu entry created
)

echo.
echo =======================================================
echo Installation Complete!
echo =======================================================
echo.
echo Application Location: %LOCALAPPDATA%\MetrologyWorkstation
echo Executable: %LOCALAPPDATA%\MetrologyWorkstation\MetrologyWorkstation.exe
echo.
echo You can launch Metrology Workstation from:
echo - Desktop shortcut
echo - Start Menu
echo - Or directly: %LOCALAPPDATA%\MetrologyWorkstation\MetrologyWorkstation.exe
echo.
echo Press any key to launch Metrology Workstation now...
pause >nul

start "" "%LOCALAPPDATA%\MetrologyWorkstation\MetrologyWorkstation.exe"