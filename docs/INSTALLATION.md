# INSTALLATION & USER SETUP GUIDE — METROLOGY WORKSTATION

---

## 1. System Requirements

### Minimum Requirements:
- **Operating System**: Windows 10 (64-bit, Version 1809+) or Windows 11
- **Processor**: 64-bit Dual-Core x86_64 CPU (1.8 GHz+)
- **Memory (RAM)**: 4 GB RAM
- **Storage**: 200 MB free disk space
- **Display**: $1280 \times 720$ resolution
- **Network**: **None required** (Operates 100% offline)

### Recommended Requirements:
- **Processor**: Quad-Core Intel / AMD CPU (2.4 GHz+)
- **Memory (RAM)**: 8 GB RAM
- **Display**: $1920 \times 1080$ Full HD display

---

## 2. Step-by-Step Installation

1. **Download Installer**:
   Download `Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe` from the [Official Website](https://metrologyworkstation.com) or [GitHub Releases](https://github.com/your-org/metrology-workstation/releases).
2. **Run Installer**:
   Double-click the downloaded setup file.
   - The installer installs Metrology Workstation into `%LOCALAPPDATA%\Programs\MetrologyWorkstation`.
   - Creates a Start Menu entry: **Metrology Workstation**.
3. **Launch Application**:
   Launch from the Start Menu or Desktop shortcut. The application starts the in-process service and opens your browser to `http://127.0.0.1:8000`.

---

## 3. Silent & Enterprise Deployment

For automated laboratory IT rollout, run with the silent flag:
```powershell
.\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe --silent --no-launch
```

---

## 4. Upgrading to a New Version

1. Download the new version installer.
2. Run the installer. It automatically replaces previous binary files while **strictly preserving all user databases, calibration records, and audit vaults** in `%LOCALAPPDATA%\MetrologyWorkstation\`.

---

## 5. Uninstallation

To uninstall Metrology Workstation:
1. Open **Windows Settings $\to$ Apps $\to$ Installed Apps** (or search "Add or remove programs").
2. Locate **Metrology Workstation** and click **Uninstall**.
3. *Note*: Your historical calibration records and SQLite database in `%LOCALAPPDATA%\MetrologyWorkstation\` are preserved to protect your laboratory data.
