; ============================================================
;  CALIBRA Metrology Workstation — Enterprise Inno Setup Script
;  Edition: Enterprise & Industrial Platform (v7.0.0)
;  Publisher: NOVYRAX Engineering Intelligence
;  Generates: Metrology-Workstation-Enterprise-v7.0.0-Setup.exe
; ============================================================

#define AppName       "CALIBRA Metrology Workstation"
#define AppEdition    "Enterprise Platform"
#define AppVersion    "7.0.0"
#define AppPublisher  "NOVYRAX Engineering Intelligence"
#define AppURL        "https://novyrax.vercel.app"
#define AppExeName    "MetrologyWorkstation.exe"
#define AppRegKey     "MetrologyWorkstationEnterprise"

[Setup]
AppId                         = {{C9E23A5F-0D44-4A9B-C258-4950A396B033}
AppName                       = {#AppName} ({#AppEdition})
AppVersion                    = {#AppVersion}
AppVerName                    = {#AppName} {#AppVersion} ({#AppEdition})
AppPublisher                  = {#AppPublisher}
AppPublisherURL               = {#AppURL}
AppSupportURL                 = {#AppURL}/contact
AppUpdatesURL                 = {#AppURL}/products/calibra/enterprise

DefaultDirName                = {localappdata}\Programs\MetrologyWorkstationEnterprise
DefaultGroupName              = {#AppName} Enterprise
DisableProgramGroupPage       = yes
AllowNoIcons                  = yes

OutputDir                     = ..\..\..\dist
OutputBaseFilename            = Metrology-Workstation-Enterprise-v7.0.0-Setup
SetupIconFile                 = ..\..\..\assets\calibra_icon.ico
UninstallDisplayIcon          = {app}\{#AppExeName}

WizardStyle                   = modern
WizardResizable               = no
WizardImageBackColor          = $0F0A06

LicenseFile                   = ..\..\..\LICENSE.txt

Compression                   = lzma2/ultra64
SolidCompression              = yes
LZMAUseSeparateProcess        = yes

ArchitecturesAllowed          = x64compatible
ArchitecturesInstallIn64BitMode = x64compatible

PrivilegesRequired            = lowest
PrivilegesRequiredOverridesAllowed = dialog

MinVersion                    = 10.0.17763
CloseApplications             = force
RestartApplications           = no

Uninstallable                 = yes
CreateUninstallRegKey         = yes

[Files]
Source: "..\..\..\dist\MetrologyWorkstation\MetrologyWorkstation.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\..\assets\calibra_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\manifest.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\hardware_scpi\*"; DestDir: "{app}\hardware_scpi"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\cad_qif\*"; DestDir: "{app}\cad_qif"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\airgap_server\*"; DestDir: "{app}\airgap_server"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\audit_defense\*"; DestDir: "{app}\audit_defense"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\procedures\*"; DestDir: "{app}\procedures"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\standards\*"; DestDir: "{app}\standards"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CALIBRA Enterprise"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\calibra_icon.ico"
Name: "{group}\Uninstall CALIBRA Enterprise"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CALIBRA Enterprise"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\calibra_icon.ico"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
