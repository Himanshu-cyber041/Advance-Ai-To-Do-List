; Optional: Inno Setup (free) -> makes a proper Setup.exe with Start-menu shortcut
[Setup]
AppName=Advance To-Do AI
AppVersion=2.0
DefaultDirName={autopf}\AdvanceTodoAI
DefaultGroupName=Advance To-Do AI
OutputBaseFilename=AdvanceTodoAI_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\AdvanceTodoAI.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Advance To-Do AI"; Filename: "{app}\AdvanceTodoAI.exe"
Name: "{autodesktop}\Advance To-Do AI"; Filename: "{app}\AdvanceTodoAI.exe"

[Run]
Filename: "{app}\AdvanceTodoAI.exe"; Description: "Launch now"; Flags: nowait postinstall skipifsilent
