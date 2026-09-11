# Metrology Workstation v7.0.0 - Professional Windows Installer Preparation
$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\Lenovo\Documents\First_Product"
$DistDir = Join-Path $ProjectRoot "dist"
$InstallerDir = Join-Path $ProjectRoot "installer_files"
$AppName = "Metrology Workstation"
$AppExe = "MetrologyWorkstation.exe"
$Version = "7.0.0"
$Publisher = "NovyraX"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Metrology Workstation v$Version - Professional Installer" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Preparing installation files..." -ForegroundColor Yellow

# Copy main executable
$SourceExe = Join-Path $DistDir $AppExe
if (-not (Test-Path $SourceExe)) {
    Write-Host "ERROR: Executable not found at $SourceExe" -ForegroundColor Red
    exit 1
}

Copy-Item $SourceExe -Destination $InstallerDir -Force
Write-Host "  Copied main executable" -ForegroundColor Green

# Copy MetrologyWorkstation directory contents
$AppDir = Join-Path $DistDir "MetrologyWorkstation"
if (Test-Path $AppDir) {
    Copy-Item $AppDir -Destination $InstallerDir -Recurse -Force
    Write-Host "  Copied application resources" -ForegroundColor Green
}

# Copy procedures and standards
$ProceduresDir = Join-Path $ProjectRoot "metrology_app\procedures"
if (Test-Path $ProceduresDir) {
    Copy-Item $ProceduresDir -Destination (Join-Path $InstallerDir "procedures") -Recurse -Force
    Write-Host "  Copied procedures catalog" -ForegroundColor Green
}

$StandardsDir = Join-Path $ProjectRoot "standards"
if (Test-Path $StandardsDir) {
    Copy-Item $StandardsDir -Destination (Join-Path $InstallerDir "standards") -Recurse -Force
    Write-Host "  Copied standards documentation" -ForegroundColor Green
}

Write-Host "[2/4] Creating application metadata..." -ForegroundColor Yellow

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
Write-Host "  Created application manifest" -ForegroundColor Green

Write-Host "[3/4] Creating README..." -ForegroundColor Yellow

$ReadmeContent = "Metrology Workstation v$Version - Desktop Application`r`n`r`nInstallation:`r`n1. Run INSTALL.bat`r`n2. Follow the installation prompts`r`n3. The application will be installed to: %LOCALAPPDATA%\$AppName`r`n`r`nFeatures:`r`n- Native desktop window with DPI awareness`r`n- 100 percent offline operation`r`n- Local data storage`r`n- Zero telemetry`r`n- FastAPI backend`r`n- SQLite database`r`n`r`nLaunch after installation from desktop shortcut or Start Menu.`r`n`r`nUninstall by running UNINSTALL.bat from the installation directory.`r`n`r`nSupport: novyrax04@gmail.com"

$ReadmePath = Join-Path $InstallerDir "README.txt"
$ReadmeContent | Out-File -FilePath $ReadmePath -Encoding ASCII
Write-Host "  Created README" -ForegroundColor Green

Write-Host "[4/4] Creating distribution package..." -ForegroundColor Yellow

# Create final distribution package
$OutputZip = Join-Path $DistDir "$AppName-v$Version-Windows-x64-Installer.zip"
if (Test-Path $OutputZip) {
    Remove-Item $OutputZip -Force
}

Compress-Archive -Path "$InstallerDir\*" -DestinationPath $OutputZip -Force

$FileSize = (Get-Item $OutputZip).Length
$FileSizeMB = [math]::Round($FileSize / 1MB, 2)

Write-Host "  Created distribution package" -ForegroundColor Green

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
Write-Host "2. Run INSTALL.bat" -ForegroundColor White
Write-Host "3. Follow the installation prompts" -ForegroundColor White
Write-Host ""
Write-Host "The application will be installed to:" -ForegroundColor White
Write-Host "%LOCALAPPDATA%\$AppName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Uninstall by running UNINSTALL.bat from the installation directory" -ForegroundColor White
Write-Host ""