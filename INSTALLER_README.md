# Metrology Workstation - CALIBRA Branded Installer

## Quick Start

### Option 1: Direct Executable (No Installation)
- Double-click `dist/MetrologyWorkstation/MetrologyWorkstation.exe` to run the application directly
- No installation required - portable application

### Option 2: Professional Installer (Recommended)
- Run `build_installer_calibra.bat` to create a Windows installer
- Requires Inno Setup (https://jrsoftware.org/isdl.php)
- Creates `MetrologyWorkstation-Setup-7.0.0.exe` for distribution

## Building the Installer

### Prerequisites
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)
- Inno Setup (for installer creation only)

### Build Process
1. **Build Executable**: `python build_calibra_installer.py`
   - Creates standalone executable with CALIBRA icon
   - Output: `dist/MetrologyWorkstation/MetrologyWorkstation.exe`

2. **Create Installer**: `build_installer_calibra.bat`
   - Creates professional Windows installer
   - Output: `MetrologyWorkstation-Setup-7.0.0.exe`

## CALIBRA Branding

The application is branded with the CALIBRA logo:
- Desktop icon: CALIBRA hourglass logo with teal-blue dot
- Installer theme: Modern CALIBRA branding
- File associations: .cal files open with Metrology Workstation

## Application Features

- Professional metrology measurement management
- ISO/IEC 17025-aligned workflows
- Advanced analytics and fleet management
- Enterprise certificate system
- Cross-platform support (Windows/macOS)
- Integration gateway for external systems

## System Requirements

- Windows 10/11 (64-bit)
- 4GB RAM minimum (8GB recommended)
- 500MB disk space
- Modern web browser (Edge, Chrome, Firefox)

## Support

- Website: https://novyrax.vercel.app
- Email: novyrax04@gmail.com
- Documentation: See included README.md

## Installation

### From Installer
1. Run `MetrologyWorkstation-Setup-7.0.0.exe`
2. Follow the installation wizard
3. Launch from desktop shortcut or Start menu

### Portable Version
1. Extract `dist/MetrologyWorkstation/` folder
2. Run `MetrologyWorkstation.exe` directly
3. No installation required

## License

See LICENSE.txt for terms and conditions.

---
*Generated with [Devin](https://devin.ai)*