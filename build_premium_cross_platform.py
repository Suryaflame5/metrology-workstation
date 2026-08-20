"""
Cross-Platform Build Script for Premium Edition Metrology Workstation.

Creates professional installers for Windows (MSIX/EXE) and Mac (.app bundle)
using PyInstaller with advanced configuration for the premium $1000 edition.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
from datetime import datetime
import zipfile
import hashlib

# Premium edition configuration
PREMIUM_CONFIG = {
    "version": "2.0.0",
    "edition": "PREMIUM",
    "price_point": "$1000",
    "product_name": "Metrology Workstation Premium",
    "company_name": "NovyraX",
    "description": "Enterprise-grade metrology platform with advanced analytics, fleet management, and certificate generation",
    "premium_features": [
        "Advanced Analytics & ML",
        "Fleet Management System", 
        "Enterprise Certificate Generation",
        "Full API & Database Integration",
        "Plugin System & Custom Scripting"
    ]
}


class CrossPlatformBuilder:
    """Cross-platform build system for premium edition."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build" / "premium"
        self.dist_dir = self.project_root / "dist" / "premium"
        self.platform = platform.system()
        self.architecture = platform.machine()
        
        # Create build directories
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.dist_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dependencies(self):
        """Check if required build dependencies are installed."""
        required_packages = [
            ('PyInstaller', 'pyinstaller'),
            ('setuptools', 'setuptools'),
            ('wheel', 'wheel'),
            ('PIL', 'pillow'),  # Pillow imports as PIL
        ]
        
        missing_packages = []
        for import_name, pip_name in required_packages:
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(pip_name)
        
        if missing_packages:
            print(f"Missing required packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        return True
    
    def create_pyinstaller_spec(self):
        """Create PyInstaller spec file for premium edition."""
        product_name_clean = PREMIUM_CONFIG["product_name"].replace(" ", "")
        # Convert path to use forward slashes for cross-platform compatibility
        project_root_safe = str(self.project_root).replace('\\', '/')
        desktop_app_path = self.project_root / 'desktop_app.py'
        
        # Use absolute paths for data files to avoid path resolution issues
        metrology_app_path = self.project_root / 'metrology_app'
        metrology_core_path = self.project_root / 'metrology_core'
        website_path = self.project_root / 'website'
        standards_path = self.project_root / 'standards'
        
        # Pre-compute icon path based on platform (use None if icon doesn't exist)
        icon_path = None  # Icon file not available, will use default
        
        # Build icon parameter conditionally
        icon_param = f",\n    icon='{icon_path}'" if icon_path else ""
        
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{str(desktop_app_path).replace(chr(92), "/")}'],
    pathex=['{project_root_safe}'],
    binaries=[],
    datas=[
        ('{str(metrology_app_path).replace(chr(92), "/")}', 'metrology_app'),
        ('{str(metrology_core_path).replace(chr(92), "/")}', 'metrology_core'),
        ('{str(website_path).replace(chr(92), "/")}', 'website'),
        ('{str(standards_path).replace(chr(92), "/")}', 'standards'),
    ],
    hiddenimports=[
        'metrology_app.services.advanced_analytics_service',
        'metrology_app.services.fleet_management_service',
        'metrology_app.services.enterprise_certificate_service',
        'metrology_app.services.integration_service',
        'metrology_app.services.plugin_service',
        'metrology_app.services.intelligence_service',
        'metrology_app.ai',
        'metrology_app.ml',
        'metrology_app.rag',
        'metrology_app.agents',
        'metrology_app.fleet',
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'reportlab',
        'cryptography',
        'sqlalchemy',
        'openpyxl',
        'uvicorn',
        'fastapi',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PySide2',
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
    name='{product_name_clean}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windows GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None{icon_param}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{product_name_clean}'
)
'''
        
        spec_path = self.build_dir / f"{PREMIUM_CONFIG['product_name'].replace(' ', '_').lower()}.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        
        return spec_path
    
    def build_windows_installer(self):
        """Build Windows installer using PyInstaller and Inno Setup."""
        if self.platform != "Windows":
            print("Windows installer can only be built on Windows platform")
            return False
        
        print("Building Windows Premium Installer...")
        
        # Create PyInstaller spec
        spec_path = self.create_pyinstaller_spec()
        
        # Run PyInstaller
        try:
            subprocess.run([
                'pyinstaller',
                '--clean',
                '--noconfirm',
                str(spec_path)
            ], check=True, cwd=self.project_root)
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller build failed: {e}")
            return False
        
        # Create Inno Setup script
        inno_script = self.create_inno_setup_script()
        inno_path = self.build_dir / "installer_script.iss"
        
        with open(inno_path, 'w') as f:
            f.write(inno_script)
        
        # Run Inno Setup compiler if available
        try:
            inno_compiler = self.find_inno_compiler()
            if inno_compiler:
                subprocess.run([inno_compiler, str(inno_path)], check=True)
                print("Windows installer created successfully")
                return True
            else:
                print("Inno Setup compiler not found. Creating ZIP distribution instead.")
                return self.create_windows_zip_distribution()
        except subprocess.CalledProcessError as e:
            print(f"Inno Setup compilation failed: {e}")
            return self.create_windows_zip_distribution()
    
    def create_inno_setup_script(self):
        """Create Inno Setup installer script."""
        app_name = PREMIUM_CONFIG["product_name"]
        app_name_clean = app_name.replace(" ", "")
        version = PREMIUM_CONFIG["version"]
        
        return f'''
[Setup]
AppName={app_name}
AppVersion={version}
AppPublisher={PREMIUM_CONFIG["company_name"]}
DefaultDirName={{commonpf}}\\{app_name_clean}
DefaultGroupName={app_name}
OutputDir={self.dist_dir}
OutputBaseFilename={app_name_clean}-Premium-v{version}-Windows-x64-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
LicenseFile=LICENSE.md
UninstallDisplayIcon={{app}}\\{app_name_clean}.exe
CreateAppDir=yes
DisableDirPage=no
DisableProgramGroupPage=yes

[Files]
Source: "dist\\{app_name_clean}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "assets\\*"; DestDir: "{{app}}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{app_name}"; Filename: "{{app}}\\{app_name_clean}.exe"
Name: "{{commondesktop}}\\{app_name}"; Filename: "{{app}}\\{app_name_clean}.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{{app}}\\{app_name_clean}.exe"; Description: "Launch {app_name}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKLM; Subkey: "Software\\{PREMIUM_CONFIG["company_name"]}\\{app_name_clean}"; ValueType: string; ValueName: "Edition"; ValueData: "{PREMIUM_CONFIG["edition"]}"
Root: HKLM; Subkey: "Software\\{PREMIUM_CONFIG["company_name"]}\\{app_name_clean}"; ValueType: string; ValueName: "Version"; ValueData: "{version}"
Root: HKLM; Subkey: "Software\\{PREMIUM_CONFIG["company_name"]}\\{app_name_clean}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{{app}}"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Check for .NET Framework (if needed for future versions)
  // if not RegKeyExists(HKLM, 'Software\\Microsoft\\.NETFramework\\Policy\\v4.0') then begin
  //   if MsgBox('This application requires .NET Framework 4.0 or later. Would you like to download it now?', mbConfirmation, MB_YESNO) = IDYES then begin
  //     ShellExec('open', 'https://dotnet.microsoft.com/download/dotnet-framework', '', '', SW_SHOW, ewNoWait, ResultCode);
  //   end;
  //   Result := False;
  // end else begin
    Result := True;
  // end;
end;
'''
    
    def find_inno_compiler(self):
        """Find Inno Setup compiler on Windows."""
        possible_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def create_windows_zip_distribution(self):
        """Create ZIP distribution for Windows if Inno Setup is not available."""
        app_name_clean = PREMIUM_CONFIG["product_name"].replace(" ", "")
        version = PREMIUM_CONFIG["version"]
        
        zip_path = self.dist_dir / f"{app_name_clean}-Premium-v{version}-Windows-x64.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the application directory
            app_dir = self.project_root / "dist" / app_name_clean
            if app_dir.exists():
                for root, dirs, files in os.walk(app_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(app_dir.parent)
                        zipf.write(file_path, arcname)
            
            # Add documentation
            for doc_file in ['LICENSE.md', 'README.md']:
                doc_path = self.project_root / doc_file
                if doc_path.exists():
                    zipf.write(doc_path, doc_file)
        
        print(f"Windows ZIP distribution created: {zip_path}")
        return True
    
    def build_mac_app_bundle(self):
        """Build Mac .app bundle using PyInstaller."""
        if self.platform != "Darwin":
            print("Mac .app bundle can only be built on macOS")
            return False
        
        print("Building Mac Premium App Bundle...")
        
        # Pre-compute values for f-string
        product_name_clean = PREMIUM_CONFIG["product_name"].replace(" ", "")
        company_name_lower = PREMIUM_CONFIG["company_name"].lower()
        version = PREMIUM_CONFIG["version"]
        # Convert path to use forward slashes for cross-platform compatibility
        project_root_safe = str(self.project_root).replace('\\', '/')
        desktop_app_path = self.project_root / 'desktop_app.py'
        
        # Use absolute paths for data files to avoid path resolution issues
        metrology_app_path = self.project_root / 'metrology_app'
        metrology_core_path = self.project_root / 'metrology_core'
        website_path = self.project_root / 'website'
        standards_path = self.project_root / 'standards'
        
        # Pre-compute icon path (use None if icon doesn't exist)
        icon_path = None  # Icon file not available, will use default
        
        # Build icon parameter conditionally
        icon_param = f",\n    icon='{icon_path}'" if icon_path else ""
        bundle_icon_param = f",\n    icon='{icon_path}'" if icon_path else ""
        
        # Create PyInstaller spec for Mac
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{str(desktop_app_path).replace(chr(92), "/")}'],
    pathex=['{project_root_safe}'],
    binaries=[],
    datas=[
        ('{str(metrology_app_path).replace(chr(92), "/")}', 'metrology_app'),
        ('{str(metrology_core_path).replace(chr(92), "/")}', 'metrology_core'),
        ('{str(website_path).replace(chr(92), "/")}', 'website'),
        ('{str(standards_path).replace(chr(92), "/")}', 'standards'),
    ],
    hiddenimports=[
        'metrology_app.services.advanced_analytics_service',
        'metrology_app.services.fleet_management_service',
        'metrology_app.services.enterprise_certificate_service',
        'metrology_app.services.integration_service',
        'metrology_app.services.plugin_service',
        'numpy',
        'pandas',
        'scipy',
        'sklearn',
        'reportlab',
        'cryptography',
        'sqlalchemy',
        'uvicorn',
        'fastapi',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PySide2',
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
    name='{product_name_clean}',
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
    entitlements_file=None{icon_param}
)

app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{product_name_clean}.app'{bundle_icon_param},
    bundle_identifier='com.{company_name_lower}.metrologypremium',
    info_plist={{
        'CFBundleName': '{PREMIUM_CONFIG["product_name"]}',
        'CFBundleDisplayName': '{PREMIUM_CONFIG["product_name"]}',
        'CFBundleIdentifier': 'com.{company_name_lower}.metrologypremium',
        'CFBundleVersion': '{version}',
        'CFBundleShortVersionString': '{version}',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
        'NSRequiresAquaSystemAppearance': False,
    }}
)
'''
        
        spec_path = self.build_dir / f"{PREMIUM_CONFIG['product_name'].replace(' ', '_').lower()}_mac.spec"
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        
        # Run PyInstaller for Mac
        try:
            subprocess.run([
                'pyinstaller',
                '--clean',
                '--noconfirm',
                str(spec_path)
            ], check=True, cwd=self.project_root)
            
            # Create DMG image
            app_name = f"{PREMIUM_CONFIG['product_name'].replace(' ', '')}.app"
            dmg_path = self.dist_dir / f"{PREMIUM_CONFIG['product_name'].replace(' ', '_')}-Premium-v{PREMIUM_CONFIG['version']}-macOS.dmg"
            
            self.create_dmg(app_name, dmg_path)
            
            print("Mac .app bundle and DMG created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller Mac build failed: {e}")
            return False
    
    def create_dmg(self, app_name, dmg_path):
        """Create DMG disk image for Mac distribution."""
        try:
            # Create temporary DMG
            temp_dmg = self.build_dir / "temp.dmg"
            
            # Create a sparse image
            subprocess.run([
                'hdiutil', 'create',
                '-volname', PREMIUM_CONFIG["product_name"],
                '-srcfolder', str(self.project_root / "dist" / app_name),
                '-ov', '-format', 'UDZO',
                str(temp_dmg)
            ], check=True)
            
            # Move to final location
            shutil.move(str(temp_dmg), str(dmg_path))
            
        except subprocess.CalledProcessError as e:
            print(f"DMG creation failed: {e}")
            # Fallback: create ZIP instead
            zip_path = dmg_path.with_suffix('.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                app_path = self.project_root / "dist" / app_name
                if app_path.exists():
                    for root, dirs, files in os.walk(app_path):
                        for file in files:
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(app_path.parent)
                            zipf.write(file_path, arcname)
    
    def build_premium_features(self):
        """Build and package premium features documentation."""
        premium_docs = {
            "PREMIUM_FEATURES.md": self.generate_premium_features_doc(),
            "ENTERPRISE_SETUP_GUIDE.md": self.generate_enterprise_setup_guide(),
            "API_DOCUMENTATION.md": self.generate_api_documentation(),
            "PLUGIN_DEVELOPMENT_GUIDE.md": self.generate_plugin_development_guide()
        }
        
        docs_dir = self.build_dir / "documentation"
        docs_dir.mkdir(exist_ok=True)
        
        for filename, content in premium_docs.items():
            with open(docs_dir / filename, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print("Premium features documentation generated")
    
    def generate_premium_features_doc(self):
        """Generate premium features documentation."""
        return f'''# {PREMIUM_CONFIG["product_name"]} - Premium Features

## Edition Information
- **Version**: {PREMIUM_CONFIG["version"]}
- **Edition**: {PREMIUM_CONFIG["edition"]}
- **Price Point**: {PREMIUM_CONFIG["price_point"]}

## Premium Features

### 1. Advanced Analytics & Measurement Intelligence
- Statistical Process Control (SPC) with Cp, Cpk, Pp, Ppk indices
- Machine learning anomaly detection using Isolation Forest
- Trend analysis with drift forecasting
- Control charts with Western Electric rules
- Fleet-wide instrument clustering and behavior analysis

### 2. Fleet Management System
- Complete instrument lifecycle tracking
- Maintenance scheduling and tracking
- Location and custodian management
- Cost analysis and total cost of ownership
- QR/Barcode integration for mobile workflows
- Calibration schedule optimization

### 3. Enterprise Certificate Generation
- ISO 17025 compliant certificate templates
- Professional PDF generation with ReportLab
- Digital signatures with X.509 certificates
- Batch certificate processing
- Custom laboratory branding
- Multi-language support

### 4. Full API & Database Integration
- RESTful API for external system integration
- Database connectors (PostgreSQL, MySQL, SQL Server)
- File import/export (CSV, Excel, JSON, XML)
- ERP/PLM system integration
- Webhook system for event notifications
- LDAP/Active Directory authentication

### 5. Plugin System & Custom Scripting
- Dynamic plugin loading with MEF architecture
- Custom calculation engines
- Python scripting engine for automation
- Custom workflow automation
- Third-party plugin marketplace support
- Full SDK for plugin development

## Installation & Setup

See [ENTERPRISE_SETUP_GUIDE.md](ENTERPRISE_SETUP_GUIDE.md) for detailed installation instructions.

## API Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

## Plugin Development

See [PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md) for plugin development documentation.

## Support & Contact

- **Company**: {PREMIUM_CONFIG["company_name"]}
- **Website**: https://novyrax.vercel.app
- **Email**: novyrax04@gmail.com

© 2026 {PREMIUM_CONFIG["company_name"]}. All rights reserved.
'''
    
    def generate_enterprise_setup_guide(self):
        """Generate enterprise setup guide."""
        return '''# Enterprise Setup Guide

## System Requirements

### Windows
- Windows 10/11 (64-bit)
- 8 GB RAM minimum (16 GB recommended)
- 2 GB disk space
- .NET Framework 4.7.2 or later (for future .NET versions)

### macOS
- macOS 10.13 (High Sierra) or later
- 8 GB RAM minimum (16 GB recommended)
- 2 GB disk space

## Installation

### Windows Installation
1. Run the installer: `MetrologyWorkstationPremium-v2.0.0-Windows-x64-Setup.exe`
2. Follow the installation wizard
3. Launch from desktop shortcut or Start menu

### macOS Installation
1. Open the DMG: `Metrology_Workstation_Premium-v2.0.0-macOS.dmg`
2. Drag the application to Applications folder
3. Launch from Applications

## Premium Feature Activation

### License Activation
1. Launch the application
2. Navigate to Settings → License
3. Enter your premium license key
4. Click "Activate License"

### Database Setup (Optional)
For PostgreSQL/MySQL integration:
1. Install your preferred database server
2. Create a database for metrology data
3. Configure connection in Settings → Integrations

### Plugin Installation
1. Download plugins from the marketplace
2. Install via Settings → Plugins → Install Plugin
3. Activate plugins as needed

## Enterprise Integration

### API Configuration
1. Navigate to Settings → API
2. Configure API keys and authentication
3. Set up webhook endpoints for notifications

### LDAP/Active Directory
1. Navigate to Settings → Authentication
2. Configure LDAP server settings
3. Test connection and save configuration

## Backup & Recovery

### Automated Backups
- Configured in Settings → Backup
- Supports local and cloud storage
- Scheduled automatic backups

### Manual Export
- Export data via File → Export
- Supported formats: CSV, Excel, JSON, XML
- Include audit trails and evidence packages

## Troubleshooting

### Common Issues
- Database connection failures
- Plugin loading errors
- Certificate generation issues

### Support Contact
- Email: novyrax04@gmail.com
- Documentation: https://novyrax.vercel.app/docs
'''
    
    def generate_api_documentation(self):
        """Generate API documentation."""
        return '''# API Documentation

## Base URL
- Local: `http://localhost:8000/api/v2`
- Production: `https://api.your-domain.com/api/v2`

## Authentication
Most endpoints require API key authentication:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Calculations
- `GET /calculations` - List all calculations
- `GET /calculations/{id}` - Get specific calculation
- `POST /calculations` - Create new calculation
- `PUT /calculations/{id}` - Update calculation
- `DELETE /calculations/{id}` - Delete calculation

### Analytics
- `GET /analytics/spc/{instrument_id}` - Get SPC analysis
- `GET /analytics/trends/{instrument_id}` - Get trend analysis
- `GET /anomalies/{instrument_id}` - Get anomaly detection
- `GET /control-charts/{instrument_id}` - Get control charts

### Fleet Management
- `GET /fleet/instruments` - List fleet instruments
- `GET /fleet/analytics` - Get fleet analytics
- `GET /fleet/calibration-schedule` - Get calibration schedule

### Certificates
- `GET /certificates` - List certificates
- `POST /certificates` - Create certificate
- `POST /certificates/{id}/generate-pdf` - Generate PDF
- `POST /certificates/batch` - Batch generate certificates

### Integrations
- `GET /integrations/connections` - List external connections
- `POST /integrations/connections` - Create connection
- `POST /integrations/connections/{id}/test` - Test connection

## Webhooks

### Subscribe to Events
```http
POST /integrations/webhooks
Content-Type: application/json

{
  "webhook_name": "Calibration Complete",
  "event_type": "calibration.complete",
  "endpoint_url": "https://your-server.com/webhook",
  "secret_key": "your_secret_key"
}
```

## Rate Limiting
- Standard: 100 requests/minute
- Premium: 1000 requests/minute
- Enterprise: Unlimited

## Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
'''
    
    def generate_plugin_development_guide(self):
        """Generate plugin development guide."""
        return '''# Plugin Development Guide

## Plugin Architecture

The Premium Edition uses a dynamic plugin loading system that allows custom
extensions without modifying the core application.

## Plugin Types

### Calculation Engine Plugins
Extend mathematical capabilities with custom measurement models.

### Data Source Plugins
Add support for new data sources and instruments.

### Export Format Plugins
Create custom export formats for certificates and reports.

### UI Extension Plugins
Add custom UI components and views.

### Validation Rule Plugins
Implement custom validation rules and checks.

## Plugin Structure

```python
# my_plugin.py
from metrology_app.services.plugin_service import PluginType

class MyCustomPlugin:
    def __init__(self):
        self.name = "My Custom Plugin"
        self.version = "1.0.0"
        self.type = PluginType.CALCULATION_ENGINE
        self.description = "Custom calculation logic"
    
    def initialize(self, config):
        """Initialize plugin with configuration"""
        self.config = config
        return True
    
    def execute(self, data):
        """Execute plugin logic"""
        # Your custom logic here
        return {"result": "custom_calculation_result"}
    
    def cleanup(self):
        """Clean up resources"""
        pass

# Export plugin instance
plugin_instance = MyCustomPlugin()
```

## Installation

1. Create plugin directory: `plugins/my_plugin/`
2. Add plugin code: `plugins/my_plugin/my_plugin.py`
3. Install via UI or API
4. Configure plugin settings
5. Activate plugin

## Custom Scripting

### Python Scripts
```python
# Custom workflow script
def process_calibration(calibration_data):
    # Access calibration data
    instrument = calibration_data['instrument_name']
    results = calibration_data['results']
    
    # Custom processing logic
    processed_results = []
    for result in results:
        # Your processing
        processed_results.append(result)
    
    return {"processed": processed_results}

# Return result
result = process_calibration(input_data)
```

### Script Parameters
Scripts receive parameters as dictionaries and should return structured data.

## SDK Reference

### Plugin Service API
```python
from metrology_app.services.plugin_service import get_plugin_service

plugin_service = get_plugin_service()

# Install plugin
plugin_service.install_plugin(plugin_data, plugin_code)

# Activate plugin
plugin_service.activate_plugin(plugin_id)

# Call plugin function
result = plugin_service.call_plugin_function(plugin_id, 'function_name', args)
```

## Testing Plugins

```python
# Test your plugin locally
import sys
sys.path.insert(0, '/path/to/metrology_app')

from my_plugin import plugin_instance

# Test initialization
config = {"setting": "value"}
assert plugin_instance.initialize(config)

# Test execution
test_data = {"input": "test"}
result = plugin_instance.execute(test_data)
assert result is not None
```

## Publishing Plugins

1. Test thoroughly with various data scenarios
2. Document configuration parameters
3. Include example usage
4. Submit to marketplace for review
5. Publish when approved

## Best Practices

- Handle errors gracefully
- Log important events
- Validate input data
- Provide clear error messages
- Follow naming conventions
- Include comprehensive documentation
- Test with edge cases
- Version your plugins properly
'''
    
    def create_build_manifest(self):
        """Create build manifest with checksums."""
        manifest = {
            "build_info": {
                "version": PREMIUM_CONFIG["version"],
                "edition": PREMIUM_CONFIG["edition"],
                "build_date": datetime.now().isoformat(),
                "platform": self.platform,
                "architecture": self.architecture,
                "builder": "CrossPlatformBuilder"
            },
            "premium_features": PREMIUM_CONFIG["premium_features"],
            "components": [],
            "checksums": {}
        }
        
        # Add component files and checksums
        for file_path in self.dist_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.dist_dir)
                file_hash = self.calculate_file_hash(file_path)
                
                manifest["components"].append(str(relative_path))
                manifest["checksums"][str(relative_path)] = file_hash
        
        # Save manifest
        manifest_path = self.dist_dir / "BUILD_MANIFEST.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Build manifest created: {manifest_path}")
    
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def build_all(self):
        """Execute complete build process for current platform."""
        print(f"Starting premium build for {self.platform}...")
        
        if not self.check_dependencies():
            return False
        
        # Build premium features documentation
        self.build_premium_features()
        
        # Platform-specific build
        if self.platform == "Windows":
            success = self.build_windows_installer()
        elif self.platform == "Darwin":
            success = self.build_mac_app_bundle()
        else:
            print(f"Unsupported platform: {self.platform}")
            return False
        
        if success:
            # Create build manifest
            self.create_build_manifest()
            print("Premium build completed successfully!")
            return True
        else:
            print("Premium build failed!")
            return False


def main():
    """Main build execution."""
    builder = CrossPlatformBuilder()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "windows":
            builder.build_windows_installer()
        elif command == "mac":
            builder.build_mac_app_bundle()
        elif command == "docs":
            builder.build_premium_features()
        elif command == "all":
            builder.build_all()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: windows, mac, docs, all")
    else:
        # Build for current platform
        builder.build_all()


if __name__ == "__main__":
    main()