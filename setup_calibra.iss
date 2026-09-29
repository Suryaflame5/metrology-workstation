; ============================================================
;  CALIBRA Metrology Workstation — Professional Inno Setup Script
;  Edition: Professional (v7.0.0)
;  Publisher: NOVYRAX Engineering Intelligence
;  Generates: Metrology-Workstation-Pro-v7.0.0-Setup.exe
; ============================================================

#define AppName       "CALIBRA Metrology Workstation"
#define AppEdition    "Professional Edition"
#define AppVersion    "7.0.0"
#define AppPublisher  "NOVYRAX Engineering Intelligence"
#define AppURL        "https://novyrax.vercel.app"
#define AppExeName    "MetrologyWorkstation.exe"
#define AppRegKey     "MetrologyWorkstationPro"

[Setup]
; ── Identity ────────────────────────────────────────────────
AppId                         = {{A4F91C3D-7B52-4E2A-89CE-2930D174F811}
AppName                       = {#AppName} ({#AppEdition})
AppVersion                    = {#AppVersion}
AppVerName                    = {#AppName} {#AppVersion} ({#AppEdition})
AppPublisher                  = {#AppPublisher}
AppPublisherURL               = {#AppURL}
AppSupportURL                 = {#AppURL}/contact
AppUpdatesURL                 = {#AppURL}/products/metrology-workstation/download

; ── Installation paths ──────────────────────────────────────
DefaultDirName                = {localappdata}\Programs\MetrologyWorkstation
DefaultGroupName              = {#AppName}
DisableProgramGroupPage       = yes
AllowNoIcons                  = yes

; ── Output ──────────────────────────────────────────────────
OutputDir                     = ..\dist
OutputBaseFilename            = Metrology-Workstation-Pro-v7.0.0-Setup
SetupIconFile                 = ..\assets\calibra_icon.ico
UninstallDisplayIcon          = {app}\{#AppExeName}

; ── Wizard appearance ───────────────────────────────────────
WizardStyle                   = modern
WizardResizable               = no
; Large sidebar image (164 x 314 px) — navy/gold CALIBRA branding
WizardImageFile               = ..\assets\wizard_sidebar.bmp
; Small header image (55 x 55 px) — CALIBRA icon mark
WizardSmallImageFile          = ..\assets\wizard_header.bmp
WizardImageBackColor          = $0F0A06

; ── License ─────────────────────────────────────────────────
LicenseFile                   = ..\LICENSE.txt

; ── Compression ─────────────────────────────────────────────
Compression                   = lzma2/ultra64
SolidCompression              = yes
LZMAUseSeparateProcess        = yes

; ── Architecture ────────────────────────────────────────────
ArchitecturesAllowed                = x64compatible
ArchitecturesInstallIn64BitMode     = x64compatible

; ── Privileges ──────────────────────────────────────────────
PrivilegesRequired              = lowest
PrivilegesRequiredOverridesAllowed = dialog

; ── Signing placeholder (uncomment when cert is available) ──
;SignTool=default $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.LaunchAfterInstall=Launch CALIBRA Metrology Workstation (Professional)

[Tasks]
Name: "desktopicon"; \
  Description: "{cm:CreateDesktopIcon}"; \
  GroupDescription: "{cm:AdditionalIcons}"; \
  Flags: unchecked

Name: "startmenuicon"; \
  Description: "Create a Start Menu shortcut"; \
  GroupDescription: "{cm:AdditionalIcons}"; \
  Flags: checkedonce

[Files]
; Main executable
Source: "..\dist\MetrologyWorkstation\MetrologyWorkstation.exe"; \
  DestDir: "{app}"; Flags: ignoreversion

; Edition manifest — marks this install as Professional
Source: "..\build\editions_build\pro\edition.json"; \
  DestDir: "{app}"; Flags: ignoreversion

; Calibration procedures
Source: "..\metrology_app\procedures\*"; \
  DestDir: "{app}\procedures"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Reference standards
Source: "..\standards\*"; \
  DestDir: "{app}\standards"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "..\EULA.md";            DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt";        DestDir: "{app}"; Flags: ignoreversion
Source: "..\INSTALLER_README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.md"

[Dirs]
Name: "{localappdata}\MetrologyWorkstation"; Flags: uninsneveruninstall

[Registry]
; Register edition in AppData so the runtime recognises Professional license
Root: HKCU; \
  Subkey: "Software\NOVYRAX\MetrologyWorkstation"; \
  ValueType: string; ValueName: "Edition"; ValueData: "pro"; \
  Flags: uninsdeletekey createvalueifdoesntexist

Root: HKCU; \
  Subkey: "Software\NOVYRAX\MetrologyWorkstation"; \
  ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; \
  Flags: createvalueifdoesntexist

; Uninstall entry
Root: HKCU; \
  Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppRegKey}"; \
  ValueType: string; ValueName: "DisplayName"; \
  ValueData: "{#AppName} ({#AppEdition})"; Flags: uninsdeletekey

Root: HKCU; \
  Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppRegKey}"; \
  ValueType: string; ValueName: "Publisher"; ValueData: "{#AppPublisher}"

Root: HKCU; \
  Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppRegKey}"; \
  ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#AppVersion}"

[Icons]
; Start Menu group
Name: "{group}\{#AppName} (Professional)"; \
  Filename: "{app}\{#AppExeName}"; \
  Parameters: "--pro"; \
  Comment: "CALIBRA Metrology Workstation — Professional Edition"; \
  Tasks: startmenuicon

; Desktop shortcut
Name: "{autodesktop}\{#AppName} (Professional)"; \
  Filename: "{app}\{#AppExeName}"; \
  Parameters: "--pro"; \
  Tasks: desktopicon

[Run]
; Launch after setup
Filename: "{app}\{#AppExeName}"; \
  Parameters: "--pro"; \
  Description: "{cm:LaunchAfterInstall}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove installation folder contents (user data in %LOCALAPPDATA%\MetrologyWorkstation is preserved)
Type: files;        Name: "{app}\{#AppExeName}"
Type: files;        Name: "{app}\edition.json"
Type: filesandordirs; Name: "{app}\procedures"
Type: filesandordirs; Name: "{app}\standards"
Type: filesandordirs; Name: "{app}\static"

[Code]
{ ── Installer code ─────────────────────────────────────────────────────── }

{ Write Professional edition manifest to %LOCALAPPDATA%\MetrologyWorkstation }
procedure WriteEditionManifest();
var
  AppDataPath: string;
  ManifestPath: string;
  Lines: TArrayOfString;
begin
  AppDataPath := ExpandConstant('{localappdata}\MetrologyWorkstation');
  ForceDirectories(AppDataPath);
  ManifestPath := AppDataPath + '\edition.json';

  SetArrayLength(Lines, 5);
  Lines[0] := '{';
  Lines[1] := '  "edition": "pro",';
  Lines[2] := '  "version": "' + '{#AppVersion}' + '",';
  Lines[3] := '  "installed_at": "' + GetDateTimeString('yyyy-mm-dd"T"hh:nn:ss', '-', ':') + '+00:00"';
  Lines[4] := '}';

  SaveStringsToFile(ManifestPath, Lines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    WriteEditionManifest();
  end;
end;

{ ── Uninstaller cleanup ──────────────────────────────────────────────────── }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    { Installation directory is already cleaned by [UninstallDelete] }
    { User data in %LOCALAPPDATA%\MetrologyWorkstation is deliberately preserved }
  end;
end;