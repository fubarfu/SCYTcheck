param(
    [ValidateSet('x64', 'x86')]
    [string]$Architecture = 'x64',
    [switch]$BundleOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$distDir = Join-Path $repoRoot 'dist'
$ffmpegDir = Join-Path $distDir 'ffmpeg'
$tesseractDir = Join-Path $distDir 'tesseract'
$tessdataDir = Join-Path $tesseractDir 'tessdata'

Write-Host "[build] Architecture: $Architecture"
Write-Host "[build] Repo root: $repoRoot"

if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

# Scaffold placeholders for later implementation tasks (T041-TT047).
if (-not (Test-Path $ffmpegDir)) {
    New-Item -ItemType Directory -Path $ffmpegDir | Out-Null
}
if (-not (Test-Path $tessdataDir)) {
    New-Item -ItemType Directory -Path $tessdataDir -Force | Out-Null
}

Write-Host "[build] Scaffold complete."
Write-Host "[build] TODO: implement PyInstaller build, FFmpeg/Tesseract copy, and ZIP packaging."
