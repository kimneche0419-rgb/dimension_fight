; Dimension Fight — Windows 설치 프로그램
; 일반 프로그램처럼: Program Files 설치 + 시작 메뉴/바탕화면 바로가기 + 제어판 제거
#define MyAppName "Dimension Fight"
#define MyAppVersion "1.0"
#define MyAppExeName "DimensionFightLauncher.exe"
#define MyAppPublisher "Dimension Fight Project"

[Setup]
AppId={{6F2C7C1A-3B7E-4E9A-9E2E-5D8C0A1E9B10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=DimensionFight_Setup
SetupIconFile=dimension_fight_cpp\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기 만들기"; GroupDescription: "추가 아이콘:"

[Files]
Source: "dimension_fight_cpp\build\DimensionFight.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\DimensionFightLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\local_proxy.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\*.dll"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\server_config.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\proxy_config.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "dimension_fight_cpp\build\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dimension_fight_cpp\assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
