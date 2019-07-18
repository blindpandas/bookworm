!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
Unicode true
CRCCheck on
ManifestSupportedOS all
XPStyle on
Name "Bookworm"
OutFile "Bookworm-setup.exe"
InstallDir "$PROGRAMFILES\bookworm"
InstallDirRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "InstallLocation"
RequestExecutionLevel admin
SetCompress auto
SetCompressor /solid lzma
SetDatablockOptimize on
VIAddVersionKey ProductName "Bookworm"
VIAddVersionKey LegalCopyright "Copyright (c) 2019 Musharraf Omer."
VIAddVersionKey ProductVersion "0.1b1"
VIAddVersionKey FileVersion "0.1b1"
VIProductVersion "0.1.0.0"
VIFileVersion "0.1.0.0"
!define MUI_ICON "builder\artifacts\bookworm.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "builder\artifacts\bookworm.bmp"
!define MUI_HEADERIMAGE_RIGHT
!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU startmenu $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\Bookworm.exe"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_RESERVEFILE_LANGDLL
Section
SetShellVarContext All
SetOutPath "$INSTDIR"
File /r builder\dist\Bookworm\*
CreateShortCut "$DESKTOP\Bookworm.lnk" "$INSTDIR\Bookworm.exe"
!insertmacro MUI_STARTMENU_WRITE_BEGIN startmenu
CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Bookworm.lnk" "$INSTDIR\Bookworm.exe"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Bookworm User Manual.lnk" "$INSTDIR\resources\docs\bookworm.html"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall Bookworm.lnk" "$INSTDIR\Uninstall.exe"
!insertmacro MUI_STARTMENU_WRITE_END
WriteUninstaller "$INSTDIR\Uninstall.exe"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "DisplayName" "Bookworm"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "UninstallString" '"$INSTDIR\uninstall.exe"'
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall" "InstallLocation" $INSTDIR
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall" "Publisher" "Musharraf Omer"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "DisplayVersion" "0.1b1"
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "VersionMajor" 0
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "VersionMinor" 1
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "NoModify" 1
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm" "NoRepair" 1
SectionEnd
Section "Uninstall"
SetShellVarContext All
DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\bookworm"
RMDir /r /REBOOTOK $INSTDIR
Delete "$DESKTOP\Bookworm.lnk"
!insertmacro MUI_STARTMENU_GETFOLDER startmenu $StartMenuFolder
RMDir /r "$SMPROGRAMS\$StartMenuFolder"
SectionEnd
Function .onInit
${If} ${RunningX64}
StrCpy $instdir "$programfiles64\bookworm"
${EndIf}
!insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd
