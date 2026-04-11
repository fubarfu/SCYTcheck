param(
    [ValidateSet('x64', 'x86')]
    [string]$Architecture = 'x64',
    [switch]$BundleOnly,
    [string]$ThirdPartyRoot,
    [string]$SpecPath,
    [string]$PythonExe = 'python'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Copy-OptionalTree {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Label
    )

    Ensure-Directory -Path $Destination
    if (Test-Path $Source) {
        Copy-Item -Path (Join-Path $Source '*') -Destination $Destination -Recurse -Force
        Write-Host "[build] Bundled $Label from $Source"
    } else {
        Write-Warning "[build] $Label bundle not found at $Source. Continuing without bundled assets."
    }
}

function Resolve-PythonCommand {
    param([string]$PythonExe)
    $command = Get-Command $PythonExe -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "Python executable not found: $PythonExe"
    }
    return $command.Source
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$distDir = Join-Path $repoRoot 'dist'
$buildRoot = Join-Path $distDir 'build'
$releaseRoot = Join-Path $distDir 'release'
$bundleRoot = Join-Path $releaseRoot $Architecture
$appRoot = Join-Path $bundleRoot 'SCYTcheck'
$vendorRoot = if ($ThirdPartyRoot) { $ThirdPartyRoot } else { Join-Path $repoRoot 'third_party' }
$ffmpegSource = Join-Path $vendorRoot (Join-Path 'ffmpeg' $Architecture)
$tesseractSource = Join-Path $vendorRoot (Join-Path 'tesseract' $Architecture)
$specFile = if ($SpecPath) { $SpecPath } else { Join-Path $repoRoot 'build-config.spec' }
$zipPath = Join-Path $releaseRoot ("SCYTcheck-{0}.zip" -f $Architecture)

Write-Host "[build] Architecture: $Architecture"
Write-Host "[build] Repo root: $repoRoot"
Write-Host "[build] Spec: $specFile"

Ensure-Directory -Path $distDir
Ensure-Directory -Path $buildRoot
Ensure-Directory -Path $releaseRoot
Ensure-Directory -Path $bundleRoot
Ensure-Directory -Path $appRoot

if (-not $BundleOnly) {
    if (-not (Test-Path $specFile)) {
        throw "PyInstaller spec not found: $specFile"
    }

    $pythonCommand = Resolve-PythonCommand -PythonExe $PythonExe
    $pyInstallerDist = Join-Path $buildRoot ("pyinstaller-{0}" -f $Architecture)
    $pyInstallerWork = Join-Path $buildRoot ("work-{0}" -f $Architecture)
    if (Test-Path $pyInstallerDist) {
        Remove-Item -Path $pyInstallerDist -Recurse -Force
    }

    & $pythonCommand -m PyInstaller $specFile --noconfirm --clean --distpath $pyInstallerDist --workpath $pyInstallerWork

    $builtApp = Join-Path $pyInstallerDist 'SCYTcheck'
    if (-not (Test-Path $builtApp)) {
        throw "PyInstaller did not produce the expected bundle directory: $builtApp"
    }

    Copy-Item -Path $builtApp -Destination $bundleRoot -Recurse -Force
}

$ffmpegDestination = Join-Path $appRoot 'ffmpeg'
$tesseractDestination = Join-Path $appRoot 'tesseract'
$tessdataDestination = Join-Path $tesseractDestination 'tessdata'

Copy-OptionalTree -Source $ffmpegSource -Destination $ffmpegDestination -Label 'FFmpeg'
Copy-OptionalTree -Source $tesseractSource -Destination $tesseractDestination -Label 'Tesseract'
Ensure-Directory -Path $tessdataDestination

if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}
Compress-Archive -Path (Join-Path $bundleRoot '*') -DestinationPath $zipPath -Force

Write-Host "[build] Release bundle ready: $bundleRoot"
Write-Host "[build] Portable ZIP ready: $zipPath"
