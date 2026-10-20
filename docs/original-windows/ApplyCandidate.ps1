$ErrorActionPreference = 'Stop'
$install = Split-Path $PSScriptRoot -Parent
Set-Location $install
Write-Host 'Quit Jarvis on this computer first. This changes the running application source.'
$candidate = Read-Host 'Paste the complete candidate folder path'
if (-not (Test-Path (Join-Path $candidate 'candidate.json'))) { throw 'Candidate manifest missing' }
$resolved = (Resolve-Path $candidate).Path
if ($resolved -eq $install -or -not (Test-Path (Join-Path $resolved 'jarvis\__main__.py'))) { throw 'Invalid candidate' }
# Validation is itself code execution: require explicit owner confirmation before running it.
Write-Host "Candidate code and tests will run with your Windows user permissions: $resolved"
if ((Read-Host 'Type TEST to run candidate tests') -cne 'TEST') { throw 'Cancelled' }
Push-Location $resolved
try {
    & (Join-Path $install '.venv\Scripts\python.exe') scripts\run_tests.py
    if ($LASTEXITCODE -ne 0) { throw 'Candidate tests failed; application not changed' }
} finally { Pop-Location }
if ((Read-Host 'Type APPLY to back up and replace application source') -cne 'APPLY') { throw 'Cancelled' }
$backupDir = Join-Path $env:LOCALAPPDATA 'JarvisFresh\CoreBackups'
New-Item -ItemType Directory -Force $backupDir | Out-Null
$backup = Join-Path $backupDir ("Jarvis-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
Compress-Archive -Path (Join-Path $install 'jarvis'),(Join-Path $install 'tests'),(Join-Path $install 'scripts') -DestinationPath $backup
foreach ($folder in @('jarvis','tests','scripts')) {
    Copy-Item -Path (Join-Path $resolved "$folder\*") -Destination (Join-Path $install $folder) -Recurse -Force
}
Write-Host "Applied. Rollback archive: $backup"
Write-Host 'If startup fails, close Jarvis and expand that archive into the installation folder with replacement.'
