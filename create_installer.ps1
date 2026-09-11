# Metrology Workstation v7.0.0 - Professional Windows Installer
# Creates a production-ready desktop application with proper shortcuts and integration

$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptPath
$DistDir = Join-Path $ProjectRoot "dist"
$TempDir = Join-Path $env:TEMP "MetrologyWorkstation_Installer"
$AppName = "Metrology Workstation"
$AppExe = "MetrologyWorkstation.exe"
$Version = "7.0.0"
$Publisher = "NovyraX"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Metrology Workstation v$Version - Professional Installer" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Clean up temp directory
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

# Create installer structure
$InstallerDir = Join-Path $TempDir "Installer"
New-Item -ItemType Directory -Path $InstallerDir -Force | Out-Null

Write-Host "[1/6] Preparing installation files..." -ForegroundColor Yellow

# Copy main executable
$SourceExe = Join-Path $DistDir $AppExe
if (-not (Test-Path $SourceExe)) {
    Write-Host "ERROR: Executable not found at $SourceExe" -ForegroundColor Red
    exit 1
}

Copy-Item $SourceExe -Destination $InstallerDir -Force
Write-Host "  ✓ Copied main executable" -ForegroundColor Green

# Copy MetrologyWorkstation directory contents
$AppDir = Join-Path $DistDir "MetrologyWorkstation"
if (Test-Path $AppDir) {
    Copy-Item $AppDir -Destination $InstallerDir -Recurse -Force
    Write-Host "  ✓ Copied application resources" -ForegroundColor Green
}

# Copy procedures and standards
$ProceduresDir = Join-Path $ProjectRoot "metrology_app\procedures"
if (Test-Path $ProceduresDir) {
    Copy-Item $ProceduresDir -Destination (Join-Path $InstallerDir "procedures") -Recurse -Force
    Write-Host "  ✓ Copied procedures catalog" -ForegroundColor Green
}

$StandardsDir = Join-Path $ProjectRoot "standards"
if (Test-Path $StandardsDir) {
    Copy-Item $StandardsDir -Destination (Join-Path $InstallerDir "standards") -Recurse -Force
    Write-Host "  ✓ Copied standards documentation" -ForegroundColor Green
}

Write-Host "[2/6] Creating application metadata..." -ForegroundColor Yellow

# Create application manifest
$Manifest = @"
<?xml version="1.0" encoding="utf-8"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="$Version.0" processorArchitecture="*" name="$Publisher.$AppName" type="win32" />
  <description>$AppName - Precision Metrology Platform</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false" />
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 and Windows 11 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}" />
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
</assembly>
"@

$ManifestPath = Join-Path $InstallerDir "$AppName.exe.manifest"
$Manifest | Out-File -FilePath $ManifestPath -Encoding UTF8
Write-Host "  ✓ Created application manifest" -ForegroundColor Green

Write-Host "[3/6] Creating desktop shortcuts..." -ForegroundColor Yellow

# Create desktop shortcut using PowerShell
$WshShell = New-Object -ComObject WScript.Shell
$DesktopShortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\$AppName.lnk")
$DesktopShortcut.TargetPath = Join-Path $env:LOCALAPPDATA "$AppName\$AppExe"
$DesktopShortcut.WorkingDirectory = Join-Path $env:LOCALAPPDATA "$AppName"
$DesktopShortcut.Description = "$AppName v$Version - Precision Metrology Platform"
$DesktopShortcut.IconLocation = Join-Path $env:LOCALAPPDATA "$AppName\$AppExe,0"
$DesktopShortcut.Save()

# Save shortcut for installer
Copy-Item "$env:USERPROFILE\Desktop\$AppName.lnk" -Destination (Join-Path $InstallerDir "Desktop Shortcut.lnk") -Force
Remove-Item "$env:USERPROFILE\Desktop\$AppName.lnk" -Force
Write-Host "  ✓ Created desktop shortcut" -ForegroundColor Green

Write-Host "[4/6] Creating Start Menu integration..." -ForegroundColor Yellow

# Create Start Menu shortcut
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName"
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}

$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuDir\$AppName.lnk")
$StartMenuShortcut.TargetPath = Join-Path $env:LOCALAPPDATA "$AppName\$AppExe"
$StartMenuShortcut.WorkingDirectory = Join-Path $env:LOCALAPPDATA "$AppName"
$StartMenuShortcut.Description = "$AppName v$Version - Precision Metrology Platform"
$StartMenuShortcut.IconLocation = Join-Path $env:LOCALAPPDATA "$AppName\$AppExe,0"
$StartMenuShortcut.Save()

# Save shortcut for installer
Copy-Item "$StartMenuDir\$AppName.lnk" -Destination (Join-Path $InstallerDir "Start Menu Shortcut.lnk") -Force
Remove-Item "$StartMenuDir\$AppName.lnk" -Force
Remove-Item $StartMenuDir -Force
Write-Host "  ✓ Created Start Menu shortcut" -ForegroundColor Green

Write-Host "[5/6] Creating installation script..." -ForegroundColor Yellow

# Create installation script
$InstallScript = @"
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Metrology Workstation v$Version - Installation
echo ========================================================
echo.

REM Check for administrator rights
net session >nul 2>&1
if "!errorLevel!" == "0" (
    echo [INFO] Running with administrator privileges
) else (
    echo [INFO] Running with standard user privileges
)

echo.
echo [1/4] Installing application files...
set "TARGET_DIR=%LOCALAPPDATA%\$AppName"

if exist "!TARGET_DIR!" (
    echo [INFO] Removing existing installation...
    rmdir /s /q "!TARGET_DIR!" 2>nul
)

mkdir "!TARGET_DIR!" 2>nul

REM Copy all files from current directory
xcopy /E /I /Y ".\*" "!TARGET_DIR!\" >nul

if "!errorLevel!" neq "0" (
    echo [ERROR] Failed to copy files
    pause
    exit /b 1
)

echo [OK] Application files installed
echo.

echo [2/4] Creating desktop shortcut...
copy "Desktop Shortcut.lnk" "%USERPROFILE%\Desktop\$AppName.lnk" >nul
if "!errorLevel!" == "0" (
    echo [OK] Desktop shortcut created
) else (
    echo [WARNING] Failed to create desktop shortcut
)

echo.
echo [3/4] Creating Start Menu entry...
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\$AppName"
if not exist "!START_MENU_DIR!" mkdir "!START_MENU_DIR!"
copy "Start Menu Shortcut.lnk" "!START_MENU_DIR!\$AppName.lnk" >nul
if "!errorLevel!" == "0" (
    echo [OK] Start Menu entry created
) else (
    echo [WARNING] Failed to create Start Menu entry
)

echo.
echo [4/4] Registering application...
reg add "HKCU\Software\$Publisher\$AppName" /v "Version" /t REG_SZ /d "$Version" /f >nul
reg add "HKCU\Software\$Publisher\$AppName" /v "InstallPath" /t REG_SZ /d "!TARGET_DIR!" /f >nul
reg add "HKCU\Software\$Publisher\$AppName" /v "InstallDate" /t REG_SZ /d "%date%" /f >nul
echo [OK] Application registered

echo.
echo ========================================================
echo Installation Complete!
echo ========================================================
echo.
echo Application installed to: !TARGET_DIR!
echo.
echo You can launch $AppName from:
echo   - Desktop shortcut
echo   - Start Menu
echo   - Or directly: !TARGET_DIR!\$AppExe
echo.
echo Press any key to launch $AppName now...
pause >nul

start "" "!TARGET_DIR!\$AppExe"

endlocal
"@

$InstallScriptPath = Join-Path $InstallerDir "INSTALL.bat"
$InstallScript | Out-File -FilePath $InstallScriptPath -Encoding ASCII
Write-Host "  ✓ Created installation script" -ForegroundColor Green

Write-Host "[6/6] Creating uninstaller..." -ForegroundColor Yellow

# Create uninstaller script
$UninstallScript = @"
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo Metrology Workstation v$Version - Uninstallation
echo ========================================================
echo.

echo This will remove $AppName from your computer.
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause >nul

echo.
echo [1/4] Closing application if running...
taskkill /F /IM $AppExe >nul 2>&1
timeout /t 2 >nul

echo [2/4] Removing desktop shortcut...
del "%USERPROFILE%\Desktop\$AppName.lnk" >nul 2>&1
echo [OK] Desktop shortcut removed

echo [3/4] Removing Start Menu entry...
set "START_MENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\$AppName"
if exist "!START_MENU_DIR!" (
    rmdir /s /q "!START_MENU_DIR!" >nul 2>&1
)
echo [OK] Start Menu entry removed

echo [4/4] Removing application files...
set "TARGET_DIR=%LOCALAPPDATA%\$AppName"
if exist "!TARGET_DIR!" (
    rmdir /s /q "!TARGET_DIR!" >nul 2>&1
    echo [OK] Application files removed
) else (
    echo [INFO] Application directory not found
)

echo.
echo Removing registry entries...
reg delete "HKCU\Software\$Publisher\$AppName" /f >nul 2>&1
echo [OK] Registry entries removed

echo.
echo ========================================================
echo Uninstallation Complete!
echo ========================================================
echo.
echo Some user data may remain in:
echo %LOCALAPPDATA%\$AppName
echo.
echo Press any key to close...
pause >nul

endlocal
"@

$UninstallScriptPath = Join-Path $InstallerDir "UNINSTALL.bat"
$UninstallScript | Out-File -FilePath $UninstallScriptPath -Encoding ASCII
Write-Host "  ✓ Created uninstaller script" -ForegroundColor Green

Write-Host ""
Write-Host "Creating distribution package..." -ForegroundColor Yellow

# Create final distribution package
$OutputZip = Join-Path $DistDir "$AppName-v$Version-Windows-x64-Installer.zip"
if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}

Compress-Archive -Path "$InstallerDir\*" -DestinationPath $OutputZip -Force

$FileSize = (Get-Item $OutputZip).Length
$FileSizeMB = [math]::Round($FileSize / 1MB, 2)

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "INSTALLER CREATED SUCCESSFULLY" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output: $OutputZip" -ForegroundColor Cyan
Write-Host "Size: $FileSizeMB MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installation Instructions:" -ForegroundColor Yellow
Write-Host "1. Extract the ZIP file to a temporary location" -ForegroundColor White
Write-Host "2. Run INSTALL.bat as administrator" -ForegroundColor White
Write-Host "3. Follow the installation prompts" -ForegroundColor White
Write-Host ""
Write-Host "The application will be installed to:" -ForegroundColor White
Write-Host "%LOCALAPPDATA%\$AppName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Uninstall by running UNINSTALL.bat from the installation directory" -ForegroundColor White
Write-Host ""

# Cleanup
Remove-Item $TempDir -Recurse -Force

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")