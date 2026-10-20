$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host 'Install Ollama for Windows from https://ollama.com/download/windows then reopen this script.'
    Start-Process 'https://ollama.com/download/windows'
    exit 1
}
$choice = Read-Host 'Model profile: 1 = RTX 2060/4060 balanced (default), 2 = low-memory CPU'
$chat = if ($choice -eq '2') { 'qwen3:4b' } else { 'qwen3:8b' }
$env:OLLAMA_NO_CLOUD = '1'
[Environment]::SetEnvironmentVariable('OLLAMA_NO_CLOUD','1','User')
Write-Host 'Cloud inference disabled for future Ollama processes. Quit and reopen Ollama after this setup.'
foreach ($name in @($chat,'qwen2.5vl:3b','nomic-embed-text')) {
    & ollama pull $name
    if ($LASTEXITCODE -ne 0) { throw "Model download failed: $name. Rerun to resume." }
}
if (Test-Path '.venv\Scripts\python.exe') {
    & '.\.venv\Scripts\python.exe' -c "from jarvis.config import Config; Config().set(model='$chat')"
    if ($LASTEXITCODE -ne 0) { throw 'Could not save model selection' }
}
Write-Host 'Local models installed. Close unused GPU-heavy apps before testing.'
