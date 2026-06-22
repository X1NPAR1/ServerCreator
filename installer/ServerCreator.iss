; ===========================================================================
;  ServerCreator — Inno Setup installer script
;  Publisher: X1NPAR1
;
;  Build steps:
;    1) pyinstaller ServerCreator.spec --noconfirm
;    2) "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\ServerCreator.iss
;
;  Produces: installer\Output\ServerCreator-Setup-<version>.exe
; ===========================================================================

#define MyAppName "ServerCreator"
#define MyAppVersion "1.76.2"
#define MyAppPublisher "X1NPAR1"
#define MyAppExeName "ServerCreator.exe"
#define MyAppURL "https://github.com/X1NPAR1/ServerCreator"

[Setup]
AppId={{8F2C4E10-7B5A-49D2-9C13-X1NPAR1SRVCR}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=ServerCreator-Setup-{#MyAppVersion}
SetupIconFile=..\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
; The installer chrome language follows the user's Windows language; the
; application's own UI language is chosen on first launch and is permanent.
ShowLanguageDialog=auto
; Auto-update support: the running application holds this named mutex, so the
; setup waits for it to close (and the Restart Manager closes it) before
; replacing any files. This prevents file-in-use errors during a silent update.
AppMutex=ServerCreatorSingleInstanceMutex
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; One-folder build: ship the whole dist\ServerCreator directory.
Source: "..\dist\ServerCreator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

[Run]
; No "skipifsilent": this entry also runs during a silent auto-update, so the
; application is relaunched automatically once the update finishes installing.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\ServerCreator"
