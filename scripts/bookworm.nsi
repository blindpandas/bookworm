!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"
Unicode true
CRCCheck on
ManifestSupportedOS all
XPStyle on
Name "$%IAPP_DISPLAY_NAME%"
OutFile "$%IAPP_DISPLAY_NAME%-$%IAPP_VERSION%-$%IAPP_ARCH%-setup.exe"
InstallDir "$PROGRAMFILES\$%IAPP_DISPLAY_NAME%"
InstallDirRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "InstallLocation"
RequestExecutionLevel admin
SetCompress auto
SetCompressor /solid lzma
SetDatablockOptimize on
VIAddVersionKey ProductName "$%IAPP_DISPLAY_NAME%"
VIAddVersionKey LegalCopyright "$%IAPP_COPYRIGHT%"
VIAddVersionKey ProductVersion "$%IAPP_VERSION%"
VIAddVersionKey FileVersion "$%IAPP_VERSION%"
VIProductVersion "$%IAPP_VERSION_EX%"
VIFileVersion "$%IAPP_VERSION_EX%"
!define MUI_ICON "builder\assets\$%IAPP_NAME%.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "builder\assets\$%IAPP_NAME%.bmp"
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_WELCOMEFINISHPAGE_BITMAP "builder\assets\$%IAPP_NAME%-logo.bmp"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_LINK "$%IAPP_WEBSITE%"
!define MUI_FINISHPAGE_LINK_LOCATION $%IAPP_WEBSITE%

# Remember the selected installer language and reuse it for the uninstaller.
# A dedicated key is used so an older uninstaller cannot remove the setting
# while the current installer is upgrading an existing Bookworm installation.
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM"
!define MUI_LANGDLL_REGISTRY_KEY "Software\Blind Pandas\Bookworm"
!define MUI_LANGDLL_REGISTRY_VALUENAME "InstallerLanguage"
# Preserve Bookworm's existing behavior of showing the language selector on
# every interactive installation while preselecting the remembered language.
!define MUI_LANGDLL_ALWAYSSHOW

# Variables to store old version info and language dialog text.
Var /GLOBAL OldInstallPath
Var /GLOBAL OldVersionFound
Var /GLOBAL LanguageDialogTitle
Var /GLOBAL LanguageDialogInfo

!insertmacro MUI_PAGE_WELCOME
!define MUI_LICENSEPAGE_RADIOBUTTONS
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU startmenu $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Arabic"
!insertmacro MUI_LANGUAGE "Bulgarian"
!insertmacro MUI_LANGUAGE "Finnish"
# Use Bookworm's professionally reviewed Hungarian NSIS language files instead
# of the stock NSIS Hungarian translation.
!insertmacro MUI_LANGUAGEEX "languages" "Hungarian"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "PortugueseBR"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "Turkish"
!insertmacro MUI_LANGUAGE "Ukrainian"

# The language selector is shown before the user has chosen a language. These
# variables let Hungarian Windows users (and users with a remembered Hungarian
# preference) see that first dialog in Hungarian without changing the existing
# English fallback for other languages.
!define MUI_LANGDLL_WINDOWTITLE "$LanguageDialogTitle"
!define MUI_LANGDLL_INFO "$LanguageDialogInfo"
!insertmacro MUI_RESERVEFILE_LANGDLL

Section
  ${If} $OldVersionFound == 1
    ${If} $LANGUAGE == ${LANG_HUNGARIAN}
      DetailPrint "Korábbi $%IAPP_DISPLAY_NAME%-verzió található. Eltávolítás..."
    ${Else}
      DetailPrint "Previous version detected. Uninstalling..."
    ${EndIf}
    # Kill the old running process if it exists
    IfFileExists "$OldInstallPath\Bookworm.exe" 0 +2
      ExecWait '\"$OldInstallPath\Bookworm.exe\" kill-other-instances'
    # Set the working directory and execute the old uninstaller
    SetOutPath "$OldInstallPath"
    ExecWait '\"$OldInstallPath\Uninstall.exe\" /S _?=$INSTDIR'
    ${If} $LANGUAGE == ${LANG_HUNGARIAN}
      DetailPrint "A korábbi $%IAPP_DISPLAY_NAME%-verzió eltávolítása befejeződött."
    ${Else}
      DetailPrint "Previous version has been uninstalled."
    ${EndIf}
  ${EndIf}

SetShellVarContext All
SetOutPath "$INSTDIR"
File /r "$%IAPP_FROZEN_DIRECTORY%\*"

${If} $LANGUAGE == ${LANG_HUNGARIAN}
  CreateShortCut "$DESKTOP\$%IAPP_DISPLAY_NAME%.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "" "" "" SW_SHOWNORMAL "" "$%IAPP_DISPLAY_NAME% – akadálymentes dokumentumolvasó ($%IAPP_AUTHOR%, $%IAPP_WEBSITE%)"
  CreateShortCut "$DESKTOP\Könyvespolc.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "bookshelf" "$INSTDIR\bookshelf.ico" "" SW_SHOWNORMAL "" "$%IAPP_DISPLAY_NAME% Könyvespolc – dokumentumok rendszerezése ($%IAPP_WEBSITE%)"
${Else}
  CreateShortCut "$DESKTOP\$%IAPP_DISPLAY_NAME%.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "" "" "" SW_SHOWNORMAL "" "$%IAPP_DESCRIPTION% from $%IAPP_AUTHOR% ($%IAPP_WEBSITE%)"
  CreateShortCut "$DESKTOP\Bookshelf.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "bookshelf" "$INSTDIR\bookshelf.ico" "" SW_SHOWNORMAL "" "Bookworm Bookshelf from $%IAPP_AUTHOR% ($%IAPP_WEBSITE%)"
${EndIf}

!insertmacro MUI_STARTMENU_WRITE_BEGIN startmenu
CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$%IAPP_DISPLAY_NAME%.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe"
${If} $LANGUAGE == ${LANG_HUNGARIAN}
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Könyvespolc.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "bookshelf" "$INSTDIR\bookshelf.ico"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$%IAPP_DISPLAY_NAME% magyar felhasználói kézikönyve.lnk" "$INSTDIR\resources\userguide\hu\$%IAPP_NAME%.html"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$%IAPP_DISPLAY_NAME% eltávolítása.lnk" "$INSTDIR\Uninstall.exe"
${Else}
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Bookshelf.lnk" "$INSTDIR\$%IAPP_DISPLAY_NAME%.exe" "bookshelf" "$INSTDIR\bookshelf.ico"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$%IAPP_DISPLAY_NAME% English User Guide.lnk" "$INSTDIR\resources\userguide\en\$%IAPP_NAME%.html"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall $%IAPP_DISPLAY_NAME%.lnk" "$INSTDIR\Uninstall.exe"
${EndIf}
!insertmacro MUI_STARTMENU_WRITE_END

WriteUninstaller "$INSTDIR\Uninstall.exe"
${If} $LANGUAGE == ${LANG_HUNGARIAN}
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "DisplayName" "$%IAPP_DISPLAY_NAME% – akadálymentes dokumentumolvasó"
${Else}
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "DisplayName" "$%IAPP_DISPLAY_NAME% -  $%IAPP_DESCRIPTION%"
${EndIf}
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "InstallLocation" $INSTDIR
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "Publisher" "$%IAPP_AUTHOR%"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "DisplayVersion" "$%IAPP_VERSION%"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "Silent Uninstall" "$\"$INSTDIR\uninstall.exe$\" /S"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "DisplayIcon" "$\"$INSTDIR\bookworm.ico$\""
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "NoModify" 1
WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "NoRepair" 1
SectionEnd

Section "Uninstall"
SetShellVarContext All
nsExec::ExecToStack '\"$INSTDIR\Bookworm.exe\" shell --shell-disintegrate'
DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%"
RMDir /r /REBOOTOK $INSTDIR
Delete "$DESKTOP\$%IAPP_DISPLAY_NAME%.lnk"
${If} $LANGUAGE == ${LANG_HUNGARIAN}
  Delete "$DESKTOP\Könyvespolc.lnk"
${Else}
  Delete "$DESKTOP\Bookshelf.lnk"
${EndIf}
!insertmacro MUI_STARTMENU_GETFOLDER startmenu $StartMenuFolder
RMDir /r "$SMPROGRAMS\$StartMenuFolder"
# Remove the remembered installer language after it has been used by the
# uninstaller. The parent key is removed only if no other values exist.
DeleteRegValue HKLM "Software\Blind Pandas\Bookworm" "InstallerLanguage"
DeleteRegKey /ifempty HKLM "Software\Blind Pandas\Bookworm"
DeleteRegKey /ifempty HKLM "Software\Blind Pandas"
SectionEnd

Function .onInit
  # Use the correct registry view before reading either the remembered language
  # or information about an existing installation.
  ${If} $%IAPP_ARCH% == "x64"
    SetRegView 64
  ${EndIf}

  # The first language dialog has no selected UI language yet. Prefer Hungarian
  # wording if Hungarian is the detected or previously remembered language.
  StrCpy $LanguageDialogTitle "Installer Language"
  StrCpy $LanguageDialogInfo "Please select a language."
  StrCpy $0 ""
  ReadRegStr $0 HKLM "Software\Blind Pandas\Bookworm" "InstallerLanguage"
  ${If} $0 == ${LANG_HUNGARIAN}
    StrCpy $LanguageDialogTitle "A telepítés nyelve"
    StrCpy $LanguageDialogInfo "Válassza ki a telepítés nyelvét."
  ${ElseIf} $0 == ""
    ${If} $LANGUAGE == ${LANG_HUNGARIAN}
      StrCpy $LanguageDialogTitle "A telepítés nyelve"
      StrCpy $LanguageDialogInfo "Válassza ki a telepítés nyelvét."
    ${EndIf}
  ${EndIf}
  !insertmacro MUI_LANGDLL_DISPLAY

  # Initialize the flag to '0' (meaning 'not found').
  StrCpy $OldVersionFound 0
  ReadRegStr $OldInstallPath HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\$%IAPP_NAME%" "InstallLocation"
  IfErrors done
  # If ReadRegStr was successful, it means an old version exists. Set the flag to '1' (meaning 'found').
  StrCpy $OldVersionFound 1
done:

  ${If} $%IAPP_ARCH% == "x64"
    StrCpy $instdir "$programfiles64\$%IAPP_DISPLAY_NAME%"
  ${Else}
    StrCpy $instdir "$programfiles32\$%IAPP_DISPLAY_NAME%"
  ${EndIf}

  IfFileExists "$INSTDIR\Bookworm.exe" 0 +2
    ExecWait '\"$INSTDIR\Bookworm.exe\" kill-other-instances'
FunctionEnd

Function un.onInit
  # Read the language preference from the same registry view used by the installer.
  ${If} $%IAPP_ARCH% == "x64"
    SetRegView 64
  ${EndIf}

  # MUI_UNGETLANGUAGE normally uses the language remembered during installation.
  # If an older installation has no stored preference, localize the fallback
  # language selector according to the Windows UI language.
  StrCpy $LanguageDialogTitle "Installer Language"
  StrCpy $LanguageDialogInfo "Please select a language."
  ${If} $LANGUAGE == ${LANG_HUNGARIAN}
    StrCpy $LanguageDialogTitle "Az eltávolítás nyelve"
    StrCpy $LanguageDialogInfo "Válassza ki az eltávolítás nyelvét."
  ${EndIf}
  !insertmacro MUI_UNGETLANGUAGE

  IfFileExists "$INSTDIR\Bookworm.exe" 0 +2
    ExecWait '\"$INSTDIR\Bookworm.exe\" kill-other-instances'
FunctionEnd
