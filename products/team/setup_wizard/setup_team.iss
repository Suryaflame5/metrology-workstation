; ============================================================
;  CALIBRA Metrology Workstation — Team Fleet Inno Setup Script
;  Edition: Team / Laboratory Fleet (v7.0.0)
;  Publisher: NOVYRAX Engineering Intelligence
;  Generates: Metrology-Workstation-Team-v7.0.0-Setup.exe
; ============================================================

#define AppName       "CALIBRA Metrology Workstation"
#define AppEdition    "Team Fleet Edition"
#define AppVersion    "7.0.0"
#define AppPublisher  "NOVYRAX Engineering Intelligence"
#define AppURL        "https://novyrax.vercel.app"
#define AppExeName    "MetrologyWorkstation.exe"
#define AppRegKey     "MetrologyWorkstationTeam"

[Setup]
AppId                         = {{B8D12F4E-9C33-4F8A-B147-3849F285A922}
AppName                       = {#AppName} ({#AppEdition})
AppVersion                    = {#AppVersion}
AppVerName                    = {#AppName} {#AppVersion} ({#AppEdition})
AppPublisher                  = {#AppPublisher}
AppPublisherURL               = {#AppURL}
AppSupportURL                 = {#AppURL}/contact
AppUpdatesURL                 = {#AppURL}/products/calibra/team

DefaultDirName                = {localappdata}\Programs\MetrologyWorkstationTeam
DefaultGroupName              = {#AppName} Team Fleet
DisableProgramGroupPage       = yes
AllowNoIcons                  = yes

OutputDir                     = ..\..\..\dist
OutputBaseFilename            = Metrology-Workstation-Team-v7.0.0-Setup
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
Source: "..\deployment\*"; DestDir: "{app}\deployment"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\fleet_sync\*"; DestDir: "{app}\fleet_sync"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\batch_pipeline\*"; DestDir: "{app}\batch_pipeline"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\procedures\*"; DestDir: "{app}\procedures"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\standards\*"; DestDir: "{app}\standards"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CALIBRA Team Fleet"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\calibra_icon.ico"
Name: "{group}\Uninstall CALIBRA Team"; Filename: "{uninstallexe}"
Name: "{autodesktop}\CALIBRA Team Fleet"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\calibra_icon.ico"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
