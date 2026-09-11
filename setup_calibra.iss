; Metrology Workstation Installer Script for Inno Setup
; This creates a professional Windows installer with CALIBRA branding

[Setup]
AppName=Metrology Workstation
AppVersion=7.0.0
AppPublisher=NovyraX
AppPublisherURL=https://novyrax.vercel.app
AppSupportURL=https://novyrax.vercel.app
AppUpdatesURL=https://novyrax.vercel.app
DefaultDirName={pf}\Metrology Workstation
DefaultGroupName=Metrology Workstation
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputBaseFilename=MetrologyWorkstation-Setup-7.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile=assets\calibra_logo.png
WizardSmallImageFile=assets\calibra_logo.png
SetupIconFile=assets\calibra_icon.ico
UninstallDisplayIcon={app}\MetrologyWorkstation.exe
ChangesAssociations=yes

[Files]
Source: "dist\MetrologyWorkstation\MetrologyWorkstation.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "metrology_app\static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "metrology_app\procedures\*"; DestDir: "{app}\procedures"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "standards\*"; DestDir: "{app}\standards"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Metrology Workstation"; Filename: "{app}\MetrologyWorkstation.exe"; IconFilename: "{app}\MetrologyWorkstation.exe"
Name: "{group}\Uninstall Metrology Workstation"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Metrology Workstation"; Filename: "{app}\MetrologyWorkstation.exe"; IconFilename: "{app}\MetrologyWorkstation.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Registry]
Root: HKCR; Subkey: ".cal"; ValueType: string; ValueData: "MetrologyWorkstationFile"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "MetrologyWorkstationFile"; ValueType: string; ValueData: "Metrology Workstation File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "MetrologyWorkstationFile\DefaultIcon"; ValueType: string; ValueData: "{app}\MetrologyWorkstation.exe,0"
Root: HKCR; Subkey: "MetrologyWorkstationFile\shell\open\command"; ValueType: string; ValueData: """{app}\MetrologyWorkstation.exe"" ""%1"""

[Run]
Filename: "{app}\MetrologyWorkstation.exe"; Description: "Launch Metrology Workstation"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\static"
Type: filesandordirs; Name: "{app}\procedures"
Type: filesandordirs; Name: "{app}\standards"