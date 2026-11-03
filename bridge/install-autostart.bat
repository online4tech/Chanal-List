@echo off
title Online4Tech Bridge - auto start
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is not installed. Install it from https://nodejs.org first, then run this file again.
  pause
  exit /b 1
)
cd /d "%~dp0"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS=%STARTUP%\Online4Tech-Bridge.vbs"
> "%VBS%" echo Set sh = CreateObject("WScript.Shell")
>> "%VBS%" echo sh.CurrentDirectory = "%~dp0"
>> "%VBS%" echo sh.Run "cmd /c node telnet-bridge.js", 0, False
echo Starting the bridge now in the background...
wscript "%VBS%"
echo.
echo Done. The bridge will start automatically (hidden) every time Windows starts.
echo Do not move or delete this folder, or the bridge will not start.
echo To turn this off later, run remove-autostart.bat
echo.
pause
