; Optional installer for the NEW source-based executable.
; Build source/dist/HaulFM-Overlay-New.exe with build.ps1 first.
; This installer is separate from the legacy v1.2.21 installer.

#define AppName "HaulFM Overlay New"
#define AppVersion "2.0.0"
#define AppExe "HaulFM-Overlay-New.exe"

[Setup]
AppId={{AEF0CD8D-D76E-4F75-8AE8-8489C3B71F6A}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\HaulFM Overlay New
DefaultGroupName={#AppName}
OutputDir=dist
OutputBaseFilename=HaulFM-Overlay-New-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExe}

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
