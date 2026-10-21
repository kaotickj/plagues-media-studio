; Plague's Media Studio installer
#define MyAppName "Plague's Media Studio"
#define MyAppVersion "0.1.0"
[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\PlaguesMediaStudio
DefaultGroupName={#MyAppName}
OutputDir=..\dist
OutputBaseFilename=PlaguesMediaStudio-Windows-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
[Files]
Source: "..\dist\PlaguesMediaStudio\*"; DestDir: "{app}"; Flags: recursesubdirs
[Icons]
Name: "{group}\Plague's Media Studio"; Filename: "{app}\PlaguesMediaStudio.exe"
Name: "{autodesktop}\Plague's Media Studio"; Filename: "{app}\PlaguesMediaStudio.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"
