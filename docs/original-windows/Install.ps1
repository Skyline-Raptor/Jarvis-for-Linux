param([switch]$SkipVoice)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
Start-Transcript -Path 'install.log' -Append
try {
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        throw 'This package targets Windows 11 x64. ARM64 native packages have not been validated.'
    }
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    $python = $null
    if ($pyCommand) {
        foreach ($version in @('-3.11','-3.12')) {
            try {
                $candidate = & py $version -c 'import sys; print(sys.executable)' 2>$null
                if ($LASTEXITCODE -eq 0) { $python = ($candidate | Select-Object -Last 1).Trim(); break }
            } catch { continue }
        }
    }
    if (-not $python) {
        Write-Host 'Installing free Python 3.11 using Windows Package Manager...'
        & winget install --id Python.Python.3.11 --exact --source winget --scope user --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 x64 from python.org and rerun this installer.' }
        $python = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
        if (-not (Test-Path $python)) { throw 'Python installed in a different location. Reopen Windows and rerun the installer.' }
    }
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        & $python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install --no-index --find-links wheelhouse --upgrade pip==26.2.1
    if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
    & '.\.venv\Scripts\python.exe' -m pip install --no-index --find-links wheelhouse -r requirements.txt -c constraints.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed; see install.log' }
    & '.\.venv\Scripts\python.exe' scripts\run_tests.py
    if ($LASTEXITCODE -ne 0) { throw 'Core tests failed; review test-results before using Jarvis' }
    $dataRoot = Join-Path $env:LOCALAPPDATA 'JarvisFresh'
    New-Item -ItemType Directory -Force -Path $dataRoot | Out-Null
    # Inheritance from a user's profile normally already excludes other ordinary users;
    # explicitly restrict this folder to the current SID, SYSTEM, and Administrators.
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    & icacls $dataRoot /inheritance:r /grant:r "*${sid}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Could not secure the Jarvis data folder' }
    if (-not $SkipVoice) {
        & "$PSScriptRoot\InstallVoice.ps1"
    }
    & '.\.venv\Scripts\python.exe' -m pip freeze | Set-Content resolved-environment.txt
    Write-Host 'Jarvis installed. Next run Install_Models.cmd, then Start_Jarvis.cmd.'
    Write-Host 'See SETUP_STEP_BY_STEP.md for accounts, remote devices, voice, and native checks.'
} finally {
    Stop-Transcript
}
