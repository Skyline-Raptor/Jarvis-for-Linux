@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install.ps1" %*
if errorlevel 1 (echo Installation failed. Read install.log and the setup guide.)
pause
