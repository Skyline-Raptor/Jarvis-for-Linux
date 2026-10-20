$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Run Install_Jarvis.cmd first' }
& '.\.venv\Scripts\python.exe' -m pip install --no-index --find-links wheelhouse -r requirements-voice.txt -c constraints.txt
if ($LASTEXITCODE -ne 0) { throw 'Voice dependency installation failed' }
& '.\.venv\Scripts\python.exe' scripts\download_voice.py
if ($LASTEXITCODE -ne 0) { throw 'Voice asset download failed. Rerun Install_Voice.cmd to retry.' }
Write-Host 'British George and local speech recognition installed.'
