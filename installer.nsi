!define APPNAME "Digital Book AI Editor"
!define COMPANYNAME "AhimKTI"
!define DESCRIPTION "Aplikasi AI Document Editor & Reader"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

Name "${APPNAME}"
OutFile "DigitalBook_Installer_v1.0.exe"
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"

; Pages for the installer wizard
Page directory
Page instfiles

Section "Install"
  ; Set output path to the installation directory
  SetOutPath $INSTDIR
  
  ; Include all files from PyInstaller dist directory
  ; Make sure to run build_exe.bat BEFORE compiling this NSIS script!
  File /r "dist\Digital Book\*.*"
  
  ; Create Desktop Shortcut
  CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\Digital Book.exe"
  
  ; Create Start Menu Shortcut
  CreateDirectory "$SMPROGRAMS\${COMPANYNAME}"
  CreateShortcut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\Digital Book.exe"
  
  ; Create Uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Add/Remove Programs registry keys
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\Digital Book.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
SectionEnd

Section "Uninstall"
  ; Remove all files in the installation directory
  RMDir /r "$INSTDIR"
  
  ; Remove Desktop shortcut
  Delete "$DESKTOP\${APPNAME}.lnk"
  
  ; Remove Start Menu shortcut
  RMDir /r "$SMPROGRAMS\${COMPANYNAME}"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
