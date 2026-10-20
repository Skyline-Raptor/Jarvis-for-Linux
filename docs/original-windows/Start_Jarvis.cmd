@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Install_Jarvis.cmd first.
  pause
  exit /b 1
)
if not exist "%LOCALAPPDATA%\JarvisFresh" mkdir "%LOCALAPPDATA%\JarvisFresh"
".venv\Scripts\python.exe" -m jarvis %* >> "%LOCALAPPDATA%\JarvisFresh\runtime.log" 2>&1
if errorlevel 1 (
  echo Jarvis stopped with an error. See %%LOCALAPPDATA%%\JarvisFresh\runtime.log
  pause
)
