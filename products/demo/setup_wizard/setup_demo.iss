; ============================================================
;  CALIBRA Metrology Workstation — Community Demo Inno Setup Script
;  Edition: Community Demo Edition (v7.0.0)
;  Publisher: NOVYRAX Engineering Intelligence
;  Generates: Metrology-Workstation-Demo-v7.0.0-Setup.exe
; ============================================================

#define AppName       "CALIBRA Metrology Workstation"
#define AppEdition    "Community Demo Edition"
#define AppVersion    "7.0.0"
#define AppPublisher  "NOVYRAX Engineering Intelligence"
#define AppURL        "https://novyrax.vercel.app"
#define AppExeName    "MetrologyWorkstation.exe"
#define AppRegKey     "MetrologyWorkstationDemo"

[Setup]
AppId                         = {{B8C12D4E-9E63-4C3B-9A7D-3841E285F922}
AppName                       = {#AppName} ({#AppEdition})
AppVersion                    = {#AppVersion}
AppVerName                    = {#AppName} {#AppVersion} ({#AppEdition})
AppPublisher                  = {#AppPublisher}
AppPublisherURL               = {#AppURL}
AppSupportURL                 = {#AppURL}/contact
AppUpdatesURL                 = {#AppURL}/products/metrology-workstation/download
DefaultDirName                = {localappdata}\Programs\MetrologyWorkstation
DefaultGroupName              = {#AppName}
DisableProgramGroupPage       = yes
AllowNoIcons                  = yes
OutputDir                     = ..\..\..\dist
OutputBaseFilename            = Metrology-Workstation-Demo-v7.0.0-Setup
SetupIconFile                 = ..\..\..\assets\calibra_icon.ico
UninstallDisplayIcon          = {app}\{#AppExeName}
WizardStyle                   = modern
WizardResizable               = no
LicenseFile                   = ..\..\..\LICENSE.txt
Compression                   = lzma2/ultra64
SolidCompression              = yes
ArchitecturesAllowed          = x64compatible
ArchitecturesInstallIn64BitMode = x64compatible
PrivilegesRequired            = lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "..\..\..\dist\MetrologyWorkstation\MetrologyWorkstation.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\manifest.json"; DestDir: "{app}"; DestName: "edition.json"; Flags: ignoreversion
Source: "..\..\..\metrology_app\procedures\*"; DestDir: "{app}\procedures"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\..\standards\*"; DestDir: "{app}\standards"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName} ({#AppEdition})"; Filename: "{app}\{#AppExeName}"; Parameters: "--demo"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName} ({#AppEdition})"; Filename: "{app}\{#AppExeName}"; Parameters: "--demo"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Parameters: "--demo"; Description: "Launch CALIBRA Metrology Workstation (Demo)"; Flags: postinstall nowait skipifsilent
