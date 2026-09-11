# Metrology Workstation v7.0.0 - Desktop Application Package

## Package Contents

This distribution package contains the Metrology Workstation desktop application for Windows x64.

### Files Included:
- `MetrologyWorkstation.exe` - Standalone executable (117.53 MB)
- `MetrologyWorkstation-v7.0.0-Windows-x64.zip` - Complete distribution package (116.53 MB)
- `AppxManifest.xml` - Microsoft Store packaging manifest
- `package_metadata.json` - Build metadata and version information
- `procedures/` - Standard calibration procedures (7 instrument families)
- `standards/` - Standards concordance documentation

## Installation Instructions

### Option 1: Using the Installation Script (Recommended)
1. Run `INSTALL.bat` from the project root directory
2. The script will automatically:
   - Extract files to `%LOCALAPPDATA%\MetrologyWorkstation`
   - Create a desktop shortcut
   - Add a Start Menu entry
   - Launch the application

### Option 2: Manual Installation
1. Extract `dist\MetrologyWorkstation-v7.0.0-Windows-x64.zip` to your desired location
2. Navigate to the extracted folder
3. Double-click `MetrologyWorkstation.exe` to launch

### Option 3: Direct Execution
1. Navigate to `dist\MetrologyWorkstation\`
2. Double-click `MetrologyWorkstation.exe`

## System Requirements

- **Operating System**: Windows 10 (64-bit) or Windows 11 (64-bit)
- **Processor**: x64 architecture
- **Memory**: 4 GB RAM minimum (8 GB recommended)
- **Disk Space**: 150 MB free space
- **Network**: Not required (application runs 100% offline)

## Application Features

- **Native Desktop Window**: Built with pywebview for native Windows integration
- **DPI Awareness**: Per-Monitor V2 DPI awareness for high-resolution displays
- **Local-First Architecture**: All data stored locally in `%LOCALAPPDATA%\MetrologyWorkstation\`
- **Zero Telemetry**: No data collection or cloud dependencies
- **FastAPI Backend**: Modern async web framework serving the application interface
- **SQLite Database**: Local database for measurements, certificates, and evidence

## Launch Options

The application supports several command-line options:

```batch
# Standard launch (desktop window)
MetrologyWorkstation.exe

# Headless/server-only mode
MetrologyWorkstation.exe --headless

# Browser mode fallback
MetrologyWorkstation.exe --browser

# Custom port
MetrologyWorkstation.exe --port 8080

# CLI commands
MetrologyWorkstation.exe version
MetrologyWorkstation.exe selftest
MetrologyWorkstation.exe demo
```

## First Launch

When you first launch Metrology Workstation:

1. The application will initialize local directories in `%LOCALAPPDATA%\MetrologyWorkstation\`
2. A SQLite database will be created for storing measurements and certificates
3. The application will start a local web server (default port 8000)
4. A native desktop window will open displaying the workstation interface

## Uninstallation

To completely remove Metrology Workstation:

1. Delete the application directory: `%LOCALAPPDATA%\MetrologyWorkstation`
2. Remove desktop shortcut (if created)
3. Remove Start Menu entry (if created)
4. Delete any data directories: `%LOCALAPPDATA%\MetrologyWorkstation\`

## Troubleshooting

### Application won't start
- Check that Windows Defender or antivirus is not blocking the executable
- Ensure you have Windows 10/11 64-bit
- Try running as administrator

### Port already in use
- The application automatically finds an available port starting from 8000
- Use `--port` flag to specify a different port

### Database errors
- Delete `%LOCALAPPDATA%\MetrologyWorkstation\*.db` files to reset the database
- The application will recreate the database on next launch

## Support

- **Email**: novyrax04@gmail.com
- **Website**: https://novyrax.vercel.app
- **Documentation**: https://novyrax.vercel.app/docs

## Build Information

- **Version**: 7.0.0
- **Build Date**: 2026-09-03
- **Python Version**: 3.10.11
- **PyInstaller Version**: 6.22.1
- **Platform**: Windows x64

## License

This is a commercial application. See EULA.md for licensing terms and conditions.

---

**Generated with Devin AI** - https://devin.ai