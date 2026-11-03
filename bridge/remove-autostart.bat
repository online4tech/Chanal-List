@echo off
title Online4Tech Bridge - remove auto start
set "VBS=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Online4Tech-Bridge.vbs"
if exist "%VBS%" (
  del "%VBS%"
  echo Auto start has been removed.
) else (
  echo Auto start was not enabled.
)
echo.
echo If the bridge is running right now, restart the computer to stop it,
echo or end "Node.js JavaScript Runtime" in Task Manager.
echo.
pause
