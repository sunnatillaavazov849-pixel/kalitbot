; Sunat.cc Plaginlar - o'rnatuvchi (Inno Setup 6)
; Yig'ish: iscc /DAppExe=<SunatPlaginlar.exe yo'li> /DAppVersion=2.0.0 setup.iss
; Administrator huquqi kerak emas: foydalanuvchi papkasiga o'rnatiladi.

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#ifndef AppExe
  #define AppExe "SunatPlaginlar\bin\Release\net48\SunatPlaginlar.exe"
#endif

[Setup]
AppId={{6F0B6C1E-5B7A-4C4E-9D3B-2A7E8C1F5D90}
AppName=Sunat.cc Plaginlar
AppVersion={#AppVersion}
AppPublisher=Sunat.cc
AppPublisherURL=https://sunat.cc
AppSupportURL=https://t.me/sunat_aa
DefaultDirName={localappdata}\Programs\Sunat.cc Plaginlar
DefaultGroupName=Sunat.cc Plaginlar
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=SunatPlaginlar-Setup
SetupIconFile=SunatPlaginlar\app.ico
UninstallDisplayIcon={app}\SunatPlaginlar.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Ish stolida belgi yaratish"; Flags: checkedonce

[Files]
Source: "{#AppExe}"; DestDir: "{app}"; DestName: "SunatPlaginlar.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\Sunat.cc Plaginlar"; Filename: "{app}\SunatPlaginlar.exe"
Name: "{userdesktop}\Sunat.cc Plaginlar"; Filename: "{app}\SunatPlaginlar.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SunatPlaginlar.exe"; Description: "Sunat.cc Plaginlar'ni ochish"; Flags: nowait postinstall skipifsilent
