@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" scripts\native_check.py
pause
