; Inno Setup Script for Metrology Workstation (v1.0.0)
; Produces Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe

#define MyAppName "Metrology Workstation"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Metrology Workstation Engineering"
#define MyAppURL "https://metrologyworkstation.com"
#define MyAppExeName "MetrologyWorkstation.exe"

[Setup]
; App Identity
AppId={{D89B5F4A-3C21-4F1E-98A7-8724E65D9201}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/download
DefaultDirName={localappdata}\Programs\MetrologyWorkstation
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Metrology-Workstation-v1.0.0-Windows-x64-Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\MetrologyWorkstation\MetrologyWorkstation.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\MetrologyWorkstation\procedures\*"; DestDir: "{app}\procedures"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\MetrologyWorkstation\standards\*"; DestDir: "{app}\standards"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean installation folder only; user data in %LOCALAPPDATA%\MetrologyWorkstation is strictly preserved
Type: files; Name: "{app}\{#MyAppExeName}"
Type: filesandordirs; Name: "{app}\procedures"
Type: filesandordirs; Name: "{app}\standards"
