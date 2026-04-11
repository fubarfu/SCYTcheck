# SCYTcheck Application Launcher (PowerShell)
# This script ensures Scoop tools and Tesseract language data are configured

$env:PATH = "C:\Users\SteSt\scoop\shims;$env:PATH"
$env:TESSDATA_PREFIX = "C:\Users\SteSt\scoop\apps\tesseract\current\tessdata"
Set-Location "C:\Users\SteSt\source\SCYTcheck"

Write-Host "Starting SCYTcheck..." -ForegroundColor Green
& .venv\Scripts\python.exe -m src.main
