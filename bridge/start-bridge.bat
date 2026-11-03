@echo off
title Online4Tech Bridge
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is not installed on this computer.
  echo 1. Download it from https://nodejs.org  ^(the LTS button^)
  echo 2. Install it, then double-click this file again.
  echo.
  pause
  exit /b 1
)
cd /d "%~dp0"
node telnet-bridge.js
echo.
echo The bridge has stopped.
pause
