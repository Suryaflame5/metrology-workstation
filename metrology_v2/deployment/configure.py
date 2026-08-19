"""
Deployment scripts and configuration for Metrology V2

Production-grade deployment automation with:
- Windows PowerShell installer
- macOS Bash installer
- Docker configuration
- Requirements management
- Build automation
"""

import sys
import subprocess
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class DeploymentConfig:
    """Configuration for deployment."""
    
    APP_NAME = "MetrologyV2"
    VERSION = "2.0.0"
    EDITION = "PRODUCTION"
    
    # Dependencies
    PYTHON_VERSION = "3.12"
    REQUIRED_PACKAGES = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "pydantic>=2.5.0",
        "psycopg2-binary>=2.9.0",
        "cryptography>=41.0.0",
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "scipy>=1.11.0",
        "scikit-learn>=1.3.0",
        "reportlab>=4.0.0",
        "Pillow>=10.1.0",
        "openpyxl>=3.1.0",
        "python-docx>=1.1.0",
        "PySide6>=6.6.0",
        "qrcode>=7.4.0",
        "requests>=2.31.0",
        "bcrypt>=4.1.0",
        "pyotp>=2.9.0",
    ]
    
    # Build configuration
    BUILD_DIR = Path("build")
    DIST_DIR = Path("dist")
    ICON_PATH = Path("assets/icon.ico")
    
    # Application configuration
    DEFAULT_PORT = 8000
    DATABASE_NAME = "metrology_v2"
    DATABASE_USER = "metrology_user"
    DATABASE_PORT = 5432


def create_requirements_file():
    """Create requirements.txt file."""
    requirements_path = Path("requirements.txt")
    
    with open(requirements_path, 'w') as f:
        f.write("# Metrology V2 Requirements\n")
        f.write("# Version: " + DeploymentConfig.VERSION + "\n")
        f.write("# Edition: " + DeploymentConfig.EDITION + "\n\n")
        
        for package in DeploymentConfig.REQUIRED_PACKAGES:
            f.write(package + "\n")
    
    logger.info("Created requirements.txt at " + str(requirements_path))


def create_pyinstaller_spec():
    """Create PyInstaller spec file for Windows."""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['metrology_v2/desktop/application.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('metrology_v2', 'metrology_v2'),
        ('metrology_v2/ui', 'metrology_v2/ui'),
        ('metrology_v2/core', 'metrology_v2/core'),
        ('metrology_v2/infrastructure', 'metrology_v2/infrastructure'),
        ('metrology_v2/api', 'metrology_v2/api'),
        ('metrology_v2/downloader', 'metrology_v2/downloader'),
        ('metrology_v2/desktop', 'metrology_v2/desktop'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'sqlalchemy',
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'scipy',
        'sklearn',
        'reportlab',
        'PIL',
        'qrcode',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'unittest',
        'pydoc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MetrologyV2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    spec_path = Path(DeploymentConfig.APP_NAME + ".spec")
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    logger.info("Created PyInstaller spec at " + str(spec_path))


def build_windows_executable():
    """Build Windows executable using PyInstaller."""
    try:
        # Install PyInstaller if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        # Create spec file
        create_pyinstaller_spec()
        
        # Run PyInstaller
        spec_path = Path(DeploymentConfig.APP_NAME + ".spec")
        subprocess.run([sys.executable, "-m", "PyInstaller", str(spec_path)], check=True)
        
        logger.info("Windows executable built successfully in " + str(DeploymentConfig.DIST_DIR))
        
    except subprocess.CalledProcessError as e:
        logger.error("Build failed: " + str(e))
        raise


def create_windows_installer_script():
    """Create Windows PowerShell installer script."""
    installer_script = """# Metrology V2 Windows Installer
# Version: 2.0.0
# Edition: PRODUCTION

$ErrorActionPreference = "Stop"

$APP_NAME = "MetrologyV2"
$VERSION = "2.0.0"
$INSTALL_DIR = "$env:LOCALAPPDATA\\$APP_NAME"
$DATA_DIR = "$env:LOCALAPPDATA\\$APP_NAME\\data"
$LOGS_DIR = "$env:LOCALAPPDATA\\$APP_NAME\\logs"
$SHORTCUT_DIR = "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs"
$DESKTOP_DIR = "$env:USERPROFILE\\Desktop"

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
$pythonDir = "$env:LOCALAPPDATA\\$APP_NAME\\python"
if (-not (Test-Path $pythonDir)) {
    Write-Host "Downloading Python..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $pythonInstaller = "$env:TEMP\\python_installer.exe"
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
$Shortcut = $WshShell.CreateShortcut("$DESKTOP_DIR\\$APP_NAME.lnk")
$Shortcut.TargetPath = "$INSTALL_DIR\\$APP_NAME.exe"
$Shortcut.Save()

$Shortcut = $WshShell.CreateShortcut("$SHORTCUT_DIR\\$APP_NAME.lnk")
$Shortcut.TargetPath = "$INSTALL_DIR\\$APP_NAME.exe"
$Shortcut.Save()

# Configure firewall
Write-Host "Configuring firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "$APP_NAME" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow | Out-Null

Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "Application installed to: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host "Data directory: $DATA_DIR" -ForegroundColor Cyan
Write-Host "Logs directory: $LOGS_DIR" -ForegroundColor Cyan
"""
    
    installer_path = Path("install_windows.ps1")
    with open(installer_path, 'w') as f:
        f.write(installer_script)
    
    logger.info("Created Windows installer script at " + str(installer_path))


def create_macos_installer_script():
    """Create macOS Bash installer script."""
    installer_script = """#!/bin/bash
# Metrology V2 macOS Installer
# Version: 2.0.0
# Edition: PRODUCTION

set -e

APP_NAME="MetrologyV2"
VERSION="2.0.0"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
DATA_DIR="$HOME/.local/share/$APP_NAME/data"
LOGS_DIR="$HOME/.local/share/$APP_NAME/logs"
APP_BUNDLE="/Applications/$APP_NAME.app"

echo "Installing $APP_NAME v$VERSION..."

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$LOGS_DIR"

# Install Homebrew if not available
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python 3.12
echo "Installing Python 3.12..."
brew install python@3.12

# Install required packages
echo "Installing required packages..."
python3.12 -m pip install --upgrade pip
python3.12 -m pip install --requirement requirements.txt

# Create .app bundle
echo "Creating .app bundle..."
APP_CONTENTS="$APP_BUNDLE/Contents"
mkdir -p "$APP_CONTENTS/MacOS"
mkdir -p "$APP_CONTENTS/Resources"

# Create Info.plist
cat > "$APP_CONTENTS/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.novyrax.$APP_NAME</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
EOF

# Create launcher script
cat > "$APP_CONTENTS/MacOS/$APP_NAME" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3.12 -m metrology_v2.desktop.application
EOF

chmod +x "$APP_CONTENTS/MacOS/$APP_NAME"

echo "Installation completed successfully!"
echo "Application installed to: $APP_BUNDLE"
echo "Data directory: $DATA_DIR"
echo "Logs directory: $LOGS_DIR"
"""
    
    installer_path = Path("install_macos.sh")
    with open(installer_path, 'w') as f:
        f.write(installer_script)
    
    # Make script executable
    installer_path.chmod(0o755)
    
    logger.info("Created macOS installer script at " + str(installer_path))


def create_docker_configuration():
    """Create Docker configuration files."""
    
    # Dockerfile
    dockerfile = """FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY metrology_v2/ ./metrology_v2/

# Create data directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "uvicorn", "metrology_v2.api.rest:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    dockerfile_path = Path("Dockerfile")
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile)
    
    # Docker Compose
    docker_compose = """version: '3.8'

services:
  metrology-db:
    image: postgres:15
    environment:
      POSTGRES_DB: metrology_v2
      POSTGRES_USER: metrology_user
      POSTGRES_PASSWORD: metrology_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metrology_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  metrology-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=metrology-db
      - DATABASE_PORT=5432
      - DATABASE_NAME=metrology_v2
      - DATABASE_USER=metrology_user
      - DATABASE_PASSWORD=metrology_password
    depends_on:
      metrology-db:
        condition: service_healthy
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  postgres_data:
"""
    
    docker_compose_path = Path("docker-compose.yml")
    with open(docker_compose_path, 'w') as f:
        f.write(docker_compose)
    
    logger.info("Created Docker configuration files")


def create_deployment_documentation():
    """Create comprehensive deployment documentation."""
    documentation = """# Metrology V2 Deployment Guide

## Overview

Metrology V2 is a production-grade metrology platform designed for enterprise deployment. This guide covers deployment across multiple platforms and environments.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.13+, or Linux
- **Processor**: x64 architecture
- **Memory**: 8 GB RAM minimum, 16 GB recommended
- **Storage**: 500 MB for application, 10 GB for data
- **Network**: Local network or internet for initial setup

### Software Dependencies
- Python 3.12+
- PostgreSQL 15+
- (Optional) Docker for containerized deployment

## Installation Methods

### Windows Installation

1. **Download the installer**: `install_windows.ps1`
2. **Run as Administrator**: Right-click and select "Run as Administrator"
3. **Follow the prompts**: The installer will:
   - Install Python dependencies
   - Create application directories
   - Configure firewall rules
   - Create desktop shortcuts

### macOS Installation

1. **Download the installer**: `install_macos.sh`
2. **Make executable**: `chmod +x install_macos.sh`
3. **Run with sudo**: `sudo ./install_macos.sh`
4. **Follow the prompts**: The installer will:
   - Install Homebrew (if not present)
   - Install Python 3.12
   - Install required packages
   - Create .app bundle in Applications folder

### Docker Deployment

1. **Build the image**: `docker build -t metrology-v2 .`
2. **Run with Docker Compose**: `docker-compose up -d`
3. **Access the application**: `http://localhost:8000`

## Configuration

### Environment Variables

Configure the following environment variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=metrology_v2
DB_USER=metrology_user
DB_PASSWORD=your_password

# Application Configuration
METROLOGY_ENV=production
METROLOGY_DEPLOYMENT=local
SECRET_KEY=your_secret_key
MFA_ENABLED=true
ENABLE_ANIMATIONS=true
ENABLE_AGENTIC_UI=true

# Storage Configuration
STORAGE_PATH=/path/to/storage
```

### Database Setup

1. **Create PostgreSQL database**:
```sql
CREATE DATABASE metrology_v2;
CREATE USER metrology_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE metrology_v2 TO metrology_user;
```

2. **Run migrations**:
```bash
cd metrology_v2/infrastructure/database
alembic upgrade head
```

## Deployment Modes

### Local Deployment
- Single-user installation
- Local PostgreSQL database
- Desktop application with embedded server
- Ideal for individual laboratories

### Professional Deployment
- Desktop/web client
- Application server
- Shared PostgreSQL database
- File-based object storage
- Suitable for small teams

### Enterprise Deployment
- Multi-server setup
- Load balancer
- PostgreSQL with connection pooling
- Redis for caching and job queues
- S3-compatible object storage
- Background job workers
- High availability configuration

## Verification

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Connection
```bash
psql -h localhost -U metrology_user -d metrology_v2
```

### Application Logs
```bash
# Windows
type %LOCALAPPDATA%\\MetrologyV2\\logs\\app.log

# macOS/Linux
tail -f ~/.local/share/MetrologyV2/logs/app.log
```

## Troubleshooting

### Port Already in Use
Change the default port in the configuration:
```bash
export DEFAULT_PORT=8001
```

### Database Connection Failed
1. Verify PostgreSQL is running
2. Check connection parameters
3. Ensure firewall allows connections

### Permission Errors
1. Run installer as administrator (Windows) or with sudo (macOS/Linux)
2. Check file permissions on data directories

## Backup and Recovery

### Database Backup
```bash
pg_dump -U metrology_user metrology_v2 > backup.sql
```

### Database Restore
```bash
psql -U metro_user metrology_v2 < backup.sql
```

### Application Data Backup
```bash
# Windows
robocopy %LOCALAPPDATA%\\MetrologyV2\\data C:\\backup\\metrology_data /E

# macOS/Linux
cp -r ~/.local/share/MetrologyV2/data ~/backup/metrology_data
```

## Security Considerations

### Production Deployment
1. **Change default passwords**
2. **Enable HTTPS/TLS**
3. **Configure firewall rules**
4. **Enable audit logging**
5. **Regular security updates**
6. **Backup encryption**

### Network Security
1. **Use VPN for remote access**
2. **Implement rate limiting**
3. **Enable DDoS protection**
4. **Regular security audits**

## Monitoring

### Application Metrics
- API response time
- Database query performance
- Memory usage
- CPU utilization
- Error rates

### Logging
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Audit logs: Database audit_events table

## Support

For deployment support:
- Email: novyrax04@gmail.com
- Documentation: https://novyrax.vercel.app/docs
- Issues: GitHub Issues

---

*Deployment Guide for Metrology V2 v2.0.0*
*Edition: PRODUCTION*
*© 2026 NovyraX. All rights reserved.*
"""
    
    documentation_path = Path("DEPLOYMENT.md")
    with open(documentation_path, 'w') as f:
        f.write(documentation)
    
    logger.info("Created deployment documentation at " + str(documentation_path))


def create_readme():
    """Create comprehensive README file."""
    readme = """# Metrology V2 - Professional Metrology Platform

Version: 2.0.0
Edition: PRODUCTION
License: Commercial

A production-grade, auditable metrology platform for accredited laboratories, quality engineering teams, and precision manufacturing operations.

## Features

### Core Capabilities
- 50-digit exact decimal mathematics for uncompromising accuracy
- GUM uncertainty propagation with full audit trails
- TUR and guardband calculations for compliance
- ISO 14253-1 conformity assessment
- Immutable measurement history with version control
- Cryptographic audit evidence for reproducibility

### Premium Features
- Advanced Analytics with SPC, ML anomaly detection, and trend analysis
- Fleet Management with complete lifecycle tracking
- Enterprise Certificate Generation with digital signatures
- Full API Integration with REST, webhooks, and ERP/PLM connectors
- Plugin System with custom scripting capabilities
- Agentic UI Animations for professional user experience

## Quick Start

### Installation

#### Windows
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install_windows.ps1
```

#### macOS
```bash
# Run with sudo
sudo ./install_macos.sh
```

#### Docker
```bash
docker-compose up -d
```

### Configuration

1. Set environment variables (see DEPLOYMENT.md)
2. Configure database connection
3. Run database migrations: alembic upgrade head
4. Start the application

### Running the Application

#### Desktop Application
```bash
python -m metrology_v2.desktop.application
```

#### Web API
```bash
python -m uvicorn metrology_v2.api.rest:app --host 0.0.0.0 --port 8000
```

## Documentation

- Deployment Guide: DEPLOYMENT.md
- Architecture Documentation: PREMIUM_ARCHITECTURE.md
- User Guide: PREMIUM_USER_GUIDE.md
- API Documentation: http://localhost:8000/api/docs

## Requirements

- Python 3.12+
- PostgreSQL 15+
- See requirements.txt for full dependencies

## Architecture

Metrology V2 follows a modular monolith architecture with domain-driven design.

## Support

- Email: novyrax04@gmail.com
- Website: https://novyrax.vercel.app
- Documentation: https://novyrax.vercel.app/docs

## License

Commercial License - See LICENSE file for details.

## Version

Current Version: 2.0.0
Edition: PRODUCTION

Metrology V2 - Professional Metrology Platform
Copyright 2026 NovyraX. All rights reserved.
"""
    
    readme_path = Path("README.md")
    with open(readme_path, 'w') as f:
        f.write(readme)
    
    logger.info("Created README at " + str(readme_path))


def main():
    """Main deployment configuration function."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Creating deployment configuration...")
    
    # Create all deployment artifacts
    create_requirements_file()
    create_pyinstaller_spec()
    create_windows_installer_script()
    create_macos_installer_script()
    create_docker_configuration()
    create_deployment_documentation()
    create_readme()
    
    logger.info("Deployment configuration completed successfully!")
    logger.info("Next steps:")
    logger.info("1. Review deployment scripts")
    logger.info("2. Test installation on target platform")
    logger.info("3. Build distribution packages")
    logger.info("4. Deploy to production environment")


if __name__ == "__main__":
    main()