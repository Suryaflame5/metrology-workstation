; ==============================================================================
; CALIBRA Metrology Workstation — Master Professional NSIS Modern UI 2 Installer
; Produces industry-standard, high-performance Windows x64 setup packages.
; Zero Python runtime dependencies for the installer itself.
; ==============================================================================

Unicode true
SetCompressor /SOLID lzma

; Definitions fallback if not passed via /D
!ifndef EDITION
  !define EDITION "pro"
!endif

!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION "7.0.0"
!endif

!ifndef COMPANY
  !define COMPANY "NOVYRAX Technologies"
!endif

!ifndef URL
  !define URL "https://novyraxofficial.netlify.app"
!endif

!if "${EDITION}" == "pro"
  !define PRODUCT_NAME "CALIBRA Metrology Workstation 7 (Professional Edition)"
  !define PRODUCT_SHORT "CALIBRA Metrology Workstation"
  !define DEFAULT_OUTFILE "..\dist\Metrology-Workstation-Pro-v7.0.0-Setup.exe"
  !define WELCOME_BITMAP "..\build\installer_graphics\welcome_pro.bmp"
  !define SUBTITLE_TEXT "ISO/IEC 17025 & ANSI/NCSL Z540.3 Accredited Engineering Setup"
!else
  !define PRODUCT_NAME "CALIBRA Metrology Workstation 7 (Community Demo)"
  !define PRODUCT_SHORT "CALIBRA Metrology Workstation"
  !define DEFAULT_OUTFILE "..\dist\Metrology-Workstation-Demo-v7.0.0-Setup.exe"
  !define WELCOME_BITMAP "..\build\installer_graphics\welcome_demo.bmp"
  !define SUBTITLE_TEXT "Free Community Evaluation Setup (50-Digit GUM Uncertainty)"
!endif

!ifndef OUTFILE
  !define OUTFILE "${DEFAULT_OUTFILE}"
!endif

Name "${PRODUCT_NAME}"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\MetrologyWorkstation"
InstallDirRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "InstallLocation"
RequestExecutionLevel user
ManifestDPIAware true

; Modern UI 2 Includes
!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

; Interface Configuration
!define MUI_ICON "..\assets\calibra_icon.ico"
!define MUI_UNICON "..\assets\calibra_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "..\build\installer_graphics\header.bmp"
!define MUI_HEADERIMAGE_RIGHT
!define MUI_WELCOMEFINISHPAGE_BITMAP "${WELCOME_BITMAP}"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${WELCOME_BITMAP}"
!define MUI_ABORTWARNING

; Welcome Page Configuration
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${PRODUCT_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${PRODUCT_NAME} v${PRODUCT_VERSION} on your computer.$\r$\n$\r$\n${SUBTITLE_TEXT}$\r$\n$\r$\n• 100% Offline Local-First Engineering Architecture$\r$\n• 50-Digit Deterministic Measurement Kernel$\r$\n• JCGM 100:2008 & ANSI Z540.3 Uncertainty Engines$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

; License Agreement Page
!define MUI_LICENSEPAGE_TEXT_TOP "Please review the license terms before installing CALIBRA Metrology Workstation:"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "If you accept the terms of the agreement, select the checkbox below to continue."
!define MUI_LICENSEPAGE_CHECKBOX
!define MUI_LICENSEPAGE_CHECKBOX_TEXT "I accept the terms of the License Agreement and quality terms"
!insertmacro MUI_PAGE_LICENSE "..\build\installer_graphics\eula.txt"

; Destination Directory Page
!define MUI_DIRECTORYPAGE_TEXT_TOP "Setup will install ${PRODUCT_NAME} into the following directory:"
!insertmacro MUI_PAGE_DIRECTORY

; Installation Files Progress Page
!insertmacro MUI_PAGE_INSTFILES

; Finish Page Configuration
!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "${PRODUCT_NAME} has been successfully installed on your computer.$\r$\n$\r$\nClick Finish to exit this wizard."
!define MUI_FINISHPAGE_RUN "$INSTDIR\MetrologyWorkstation.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch CALIBRA Metrology Workstation"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcutOpt

!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language selection
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT_SHORT}"
VIAddVersionKey "Comments" "${SUBTITLE_TEXT}"
VIAddVersionKey "CompanyName" "${COMPANY}"
VIAddVersionKey "LegalCopyright" "© 2026 ${COMPANY}. All rights reserved."
VIAddVersionKey "FileDescription" "${PRODUCT_NAME} Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}.0"

; ------------------------------------------------------------------------------
; Installer Section
; ------------------------------------------------------------------------------
Section "MainSection" SecMain
  SetOutPath "$INSTDIR"

  ; Ensure 64-bit architecture
  ${IfNot} ${RunningX64}
    MessageBox MB_OK|MB_ICONSTOP "This software requires a 64-bit (x64) version of Windows."
    Abort
  ${EndIf}

  ; Install main application executable
  File "..\dist\MetrologyWorkstation\MetrologyWorkstation.exe"
  File "..\assets\calibra_icon.ico"

  ; Install procedures and standards templates
  SetOutPath "$INSTDIR\procedures"
  File /r "..\metrology_app\procedures\*.*"

  SetOutPath "$INSTDIR\standards"
  File /r "..\standards\*.*"

  ; Write edition marker
  SetOutPath "$INSTDIR"
  FileOpen $0 "$INSTDIR\edition.txt" w
  FileWrite $0 "${EDITION}"
  FileClose $0

  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_SHORT}"
  CreateShortcut "$SMPROGRAMS\${PRODUCT_SHORT}\${PRODUCT_NAME}.lnk" "$INSTDIR\MetrologyWorkstation.exe" "" "$INSTDIR\calibra_icon.ico" 0
  CreateShortcut "$SMPROGRAMS\${PRODUCT_SHORT}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0

  ; Create Desktop Shortcut by default
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\MetrologyWorkstation.exe" "" "$INSTDIR\calibra_icon.ico" 0

  ; Write Uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Register in Windows Control Panel (Add/Remove Programs)
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "Publisher" "${COMPANY}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "URLInfoAbout" "${URL}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "DisplayIcon" "$INSTDIR\calibra_icon.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "NoRepair" 1

  ; Compute EstimatedSize in KB
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation" "EstimatedSize" "$0"
SectionEnd

Function CreateDesktopShortcutOpt
  CreateShortcut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\MetrologyWorkstation.exe" "" "$INSTDIR\calibra_icon.ico" 0
FunctionEnd

; ------------------------------------------------------------------------------
; Uninstaller Section
; ------------------------------------------------------------------------------
Section "Uninstall"
  ; Remove installed files
  Delete "$INSTDIR\MetrologyWorkstation.exe"
  Delete "$INSTDIR\calibra_icon.ico"
  Delete "$INSTDIR\edition.txt"
  Delete "$INSTDIR\Uninstall.exe"

  RMDir /r "$INSTDIR\procedures"
  RMDir /r "$INSTDIR\standards"
  RMDir "$INSTDIR"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\${PRODUCT_SHORT}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_SHORT}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_SHORT}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"

  ; Remove Registry Keys
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation"
SectionEnd
