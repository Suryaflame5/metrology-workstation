# Metrology V2 Windows Installer
# Version: 2.0.0
# Edition: PRODUCTION

$ErrorActionPreference = "Stop"

$APP_NAME = "MetrologyV2"
$VERSION = "2.0.0"
$INSTALL_DIR = "$env:LOCALAPPDATA\$APP_NAME"
$DATA_DIR = "$env:LOCALAPPDATA\$APP_NAME\data"
$LOGS_DIR = "$env:LOCALAPPDATA\$APP_NAME\logs"
$SHORTCUT_DIR = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$DESKTOP_DIR = "$env:USERPROFILE\Desktop"

Write-Host "Installing $APP_NAME v$VERSION..." -ForegroundColor Green

# Check administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run as administrator" -ForegroundColor Red
    exit 1
}

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $DATA_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $LOGS_DIR | Out-Null

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$pythonDir = "$env:LOCALAPPDATA\$APP_NAME\python"
if (-not (Test-Path $pythonDir)) {
    Write-Host "Downloading Python..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $pythonInstaller = "$env:TEMP\python_installer.exe"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_test=0" -Wait
    Remove-Item $pythonInstaller
}

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& python -m pip install --requirement requirements.txt

# Create shortcuts
Write-Host "Creating shortcuts..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$DESKTOP_DIR\$APP_NAME.lnk")
$Shortcut.TargetPath = "$INSTALL_DIR\$APP_NAME.exe"
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut("$SHORTCUT_DIR\$APP_NAME.lnk")
$Shortcut.TargetPath = "$INSTALL_DIR\$APP_NAME.exe"
$Shortcut.Save()

# Configure firewall
Write-Host "Configuring firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "$APP_NAME" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow | Out-Null

Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "Application installed to: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host "Data directory: $DATA_DIR" -ForegroundColor Cyan
Write-Host "Logs directory: $LOGS_DIR" -ForegroundColor Cyan
