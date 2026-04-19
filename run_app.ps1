# SCYTcheck Application Launcher (PowerShell)
# This script ensures Scoop tools are configured

$env:PATH = "C:\Users\SteSt\scoop\shims;$env:PATH"
Set-Location "C:\Users\SteSt\source\SCYTcheck"

Write-Host "Starting SCYTcheck..." -ForegroundColor Green
& .venv\Scripts\python.exe -m src.main
