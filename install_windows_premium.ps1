# Windows Premium Installation Script for Metrology Workstation
# Professional installation script with dependency checking and validation

param(
    [string]$InstallPath = "$env:ProgramFiles\Metrology Workstation Premium",
    [string]$LicenseKey = "",
    [switch]$Silent = $false,
    [switch]$SkipDependencies = $false
)

# Version information
$ProductVersion = "2.0.0"
$ProductName = "Metrology Workstation Premium"
$CompanyName = "NovyraX"

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    if ($Silent) {
        Add-Content -Path "$env:TEMP\MetrologyPremiumInstall.log" -Value $logMessage
    } else {
        Write-Host $logMessage
    }
}

# Error handling
function Handle-Error {
    param([string]$ErrorMessage)
    Write-Log $ErrorMessage "ERROR"
    if (-not $Silent) {
        Write-Host "Installation failed: $ErrorMessage" -ForegroundColor Red
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Check administrator privileges
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Python installation
function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Python found: $pythonVersion"
            return $true
        }
    } catch {
        Write-Log "Python not found in PATH" "WARNING"
    }
    return $false
}

# Install Python if needed
function Install-Python {
    Write-Log "Installing Python 3.11..."
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python_installer.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Remove-Item $pythonInstaller
        Write-Log "Python installation completed"
    } catch {
        Handle-Error "Failed to install Python: $_"
    }
}

# Install Python dependencies
function Install-Dependencies {
    Write-Log "Installing Python dependencies..."
    
    $requirementsPath = Join-Path $PSScriptRoot "requirements_premium.txt"
    
    if (-not (Test-Path $requirementsPath)) {
        Handle-Error "requirements_premium.txt not found"
    }
    
    try {
        pip install -r $requirementsPath --upgrade --quiet
        Write-Log "Python dependencies installed successfully"
    } catch {
        Handle-Error "Failed to install Python dependencies: $_"
    }
}

# Create application directories
function Initialize-Directories {
    Write-Log "Creating application directories..."
    
    $directories = @(
        $InstallPath,
        "$InstallPath\data",
        "$InstallPath\logs",
        "$InstallPath\plugins",
        "$InstallPath\temp",
        "$InstallPath\backups",
        "$env:LOCALAPPDATA\MetrologyWorkstationPremium"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "Created directory: $dir"
        }
    }
}

# Copy application files
function Copy-ApplicationFiles {
    Write-Log "Copying application files..."
    
    $sourceDir = $PSScriptRoot
    $excludeFiles = @("*.ps1", "*.md", "build*", "dist*", ".git*", "__pycache__")
    
    try {
        Get-ChildItem -Path $sourceDir -Recurse | ForEach-Object {
            $shouldCopy = $true
            foreach ($exclude in $excludeFiles) {
                if ($_.Name -like $exclude) {
                    $shouldCopy = $false
                    break
                }
            }
            
            if ($shouldCopy -and $_.PSIsContainer -eq $false) {
                $relativePath = $_.FullName.Substring($sourceDir.Length)
                $destPath = Join-Path $InstallPath $relativePath.TrimStart('\')
                $destDir = Split-Path $destPath -Parent
                
                if (-not (Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                
                Copy-Item -Path $_.FullName -Destination $destPath -Force
            }
        }
        
        Write-Log "Application files copied successfully"
    } catch {
        Handle-Error "Failed to copy application files: $_"
    }
}

# Create desktop shortcut
function Create-DesktopShortcut {
    Write-Log "Creating desktop shortcut..."
    
    $WshShell = New-Object -ComObject WScript.Shell
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "$ProductName.lnk"
    $targetPath = Join-Path $InstallPath "desktop_app.py"
    $iconPath = Join-Path $InstallPath "assets\premium_icon.ico"
    
    try {
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "pythonw.exe"
        $shortcut.Arguments = "`"$targetPath`""
        $shortcut.WorkingDirectory = $InstallPath
        $shortcut.Description = "$ProductName - Enterprise Metrology Platform"
        
        if (Test-Path $iconPath) {
            $shortcut.IconLocation = $iconPath
        }
        
        $shortcut.Save()
        Write-Log "Desktop shortcut created"
    } catch {
        Write-Log "Failed to create desktop shortcut: $_" "WARNING"
    }
}

# Create Start Menu shortcut
function Create-StartMenuShortcut {
    Write-Log "Creating Start Menu shortcut..."
    
    $WshShell = New-Object -ComObject WScript.Shell
    $startMenuPath = [Environment]::GetFolderPath("StartMenu")
    $programsPath = Join-Path $startMenuPath "Programs"
    $shortcutPath = Join-Path $programsPath "$ProductName.lnk"
    $targetPath = Join-Path $InstallPath "desktop_app.py"
    
    try {
        $shortcut = $WshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "pythonw.exe"
        $shortcut.Arguments = "`"$targetPath`""
        $shortcut.WorkingDirectory = $InstallPath
        $shortcut.Description = "$ProductName - Enterprise Metrology Platform"
        $shortcut.Save()
        Write-Log "Start Menu shortcut created"
    } catch {
        Write-Log "Failed to create Start Menu shortcut: $_" "WARNING"
    }
}

# Register file associations
function Register-FileAssociations {
    Write-Log "Registering file associations..."
    
    try {
        # Register .cal file association
        $fileType = "Metrology.Calibration"
        $extension = ".cal"
        
        New-Item -Path "Registry::HKEY_CLASSES_ROOT\$extension" -Value $fileType -Force | Out-Null
        New-Item -Path "Registry::HKEY_CLASSES_ROOT\$fileType" -Value "Metrology Calibration File" -Force | Out-Null
        New-Item -Path "Registry::HKEY_CLASSES_ROOT\$fileType\shell\open\command" -Value "pythonw.exe `"$InstallPath\desktop_app.py`" `"%1`"" -Force | Out-Null
        
        Write-Log "File associations registered"
    } catch {
        Write-Log "Failed to register file associations: $_" "WARNING"
    }
}

# Configure application
function Configure-Application {
    Write-Log "Configuring application..."
    
    $configPath = Join-Path $env:LOCALAPPDATA "MetrologyWorkstationPremium\settings.json"
    
    $config = @{
        "version" = $ProductVersion
        "edition" = "PREMIUM"
        "install_path" = $InstallPath
        "license_key" = $LicenseKey
        "first_run" = $true
        "auto_update" = $true
        "telemetry" = $false
        "database_type" = "sqlite"
        "log_level" = "INFO"
    }
    
    try {
        $config | ConvertTo-Json | Set-Content -Path $configPath
        Write-Log "Application configured"
    } catch {
        Handle-Error "Failed to configure application: $_"
    }
}

# Activate license if provided
function Activate-License {
    if ([string]::IsNullOrWhiteSpace($LicenseKey)) {
        Write-Log "No license key provided, skipping activation" "INFO"
        return
    }
    
    Write-Log "Activating premium license..."
    
    try {
        $activateScript = Join-Path $InstallPath "scripts\activate_license.py"
        if (Test-Path $activateScript) {
            python $activateScript -LicenseKey $LicenseKey
            Write-Log "License activation completed"
        } else {
            Write-Log "License activation script not found" "WARNING"
        }
    } catch {
        Write-Log "License activation failed: $_" "WARNING"
    }
}

# Run post-installation validation
function Test-Installation {
    Write-Log "Running installation validation..."
    
    $validationErrors = 0
    
    # Check critical files
    $criticalFiles = @(
        "desktop_app.py",
        "metrology_app\__init__.py",
        "metrology_core\__init__.py"
    )
    
    foreach ($file in $criticalFiles) {
        $filePath = Join-Path $InstallPath $file
        if (-not (Test-Path $filePath)) {
            Write-Log "Critical file missing: $file" "ERROR"
            $validationErrors++
        }
    }
    
    # Test Python import
    try {
        python -c "import metrology_app; import metrology_core"
        Write-Log "Python modules import test passed"
    } catch {
        Write-Log "Python modules import test failed" "ERROR"
        $validationErrors++
    }
    
    if ($validationErrors -eq 0) {
        Write-Log "Installation validation passed"
        return $true
    } else {
        Write-Log "Installation validation failed with $validationErrors errors" "ERROR"
        return $false
    }
}

# Create uninstall script
function Create-UninstallScript {
    Write-Log "Creating uninstall script..."
    
    $uninstallScript = @"
# Uninstall Script for $ProductName
# Generated during installation

`$InstallPath = "$InstallPath"

Write-Host "Uninstalling $ProductName..."

# Stop application if running
Get-Process | Where-Object { `$_.ProcessName -like "*python*" } | Stop-Process -Force

# Remove desktop shortcut
`$desktopPath = [Environment]::GetFolderPath("Desktop")
`$shortcutPath = Join-Path `$desktopPath "$ProductName.lnk"
if (Test-Path `$shortcutPath) { Remove-Item `$shortcutPath }

# Remove Start Menu shortcut
`$startMenuPath = [Environment]::GetFolderPath("StartMenu")
`$programsPath = Join-Path `$startMenuPath "Programs"
`$shortcutPath = Join-Path `$programsPath "$ProductName.lnk"
if (Test-Path `$shortcutPath) { Remove-Item `$shortcutPath }

# Remove file associations
Remove-Item -Path "Registry::HKEY_CLASSES_ROOT\.cal" -ErrorAction SilentlyContinue
Remove-Item -Path "Registry::HKEY_CLASSES_ROOT\Metrology.Calibration" -ErrorAction SilentlyContinue

# Remove application files
if (Test-Path `$InstallPath) {
    Remove-Item -Path `$InstallPath -Recurse -Force
}

# Remove app data
`$appData = Join-Path `$env:LOCALAPPDATA "MetrologyWorkstationPremium"
if (Test-Path `$appData) {
    Remove-Item -Path `$appData -Recurse -Force
}

Write-Host "Uninstallation completed."
"@
    
    $uninstallPath = Join-Path $InstallPath "uninstall.ps1"
    $uninstallScript | Set-Content -Path $uninstallPath
    
    # Register uninstaller in Programs and Features
    try {
        $registryPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$ProductName"
        New-Item -Path $registryPath -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name "DisplayName" -Value $ProductName -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name "DisplayVersion" -Value $ProductVersion -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name "Publisher" -Value $CompanyName -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name "InstallLocation" -Value $InstallPath -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name "UninstallString" -Value "powershell -ExecutionPolicy Bypass -File `"$uninstallPath`"" -Force | Out-Null
        
        Write-Log "Uninstaller registered"
    } catch {
        Write-Log "Failed to register uninstaller: $_" "WARNING"
    }
}

# Main installation process
function Main {
    Write-Log "Starting $ProductName v$ProductVersion installation"
    Write-Log "Install path: $InstallPath"
    
    # Check administrator privileges
    if (-not (Test-Administrator)) {
        Handle-Error "This script requires administrator privileges. Please run as administrator."
    }
    
    # Check Python installation
    if (-not (Test-PythonInstallation)) {
        if ($Silent) {
            Install-Python
        } else {
            $response = Read-Host "Python is not installed. Would you like to install it? (Y/N)"
            if ($response -eq 'Y' -or $response -eq 'y') {
                Install-Python
            } else {
                Handle-Error "Python is required for installation."
            }
        }
    }
    
    # Install dependencies
    if (-not $SkipDependencies) {
        Install-Dependencies
    }
    
    # Create directories
    Initialize-Directories
    
    # Copy application files
    Copy-ApplicationFiles
    
    # Create shortcuts
    Create-DesktopShortcut
    Create-StartMenuShortcut
    
    # Register file associations
    Register-FileAssociations
    
    # Configure application
    Configure-Application
    
    # Activate license
    Activate-License
    
    # Create uninstaller
    Create-UninstallScript
    
    # Validate installation
    if (Test-Installation) {
        Write-Log "Installation completed successfully!"
        
        if (-not $Silent) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "Installation Complete!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "Product: $ProductName" -ForegroundColor Cyan
            Write-Host "Version: $ProductVersion" -ForegroundColor Cyan
            Write-Host "Location: $InstallPath" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "You can now launch the application from:"
            Write-Host "  - Desktop shortcut"
            Write-Host "  - Start Menu"
            Write-Host "  - Command: pythonw `"$InstallPath\desktop_app.py`""
            Write-Host ""
            
            if ([string]::IsNullOrWhiteSpace($LicenseKey)) {
                Write-Host "Remember to activate your premium license in the application settings." -ForegroundColor Yellow
            }
            
            Read-Host "Press Enter to exit"
        }
    } else {
        Handle-Error "Installation validation failed"
    }
}

# Run main installation
try {
    Main
} catch {
    Handle-Error "Unexpected error during installation: $_"
}