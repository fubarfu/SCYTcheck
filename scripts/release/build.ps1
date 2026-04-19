param(
    [ValidateSet('x64', 'x86')]
    [string]$Architecture = 'x64',
    [switch]$BundleOnly,
    [string]$ThirdPartyRoot,
    [string]$SpecPath,
    [string]$PythonExe = 'python',
    [string]$ReleaseVersion
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

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

function Test-RequiredPaddleOCRAssets {
    param([string]$Source)

    if (-not (Test-Path $Source)) {
        throw "PaddleOCR bundle is required for portable release but was not found at $Source. Run scripts/download_paddleocr_models.ps1 first."
    }

    $detDir = Get-ChildItem -Path $Source -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name.ToLower().StartsWith('det') } |
        Select-Object -First 1
    $recDir = Get-ChildItem -Path $Source -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name.ToLower().StartsWith('rec') } |
        Select-Object -First 1

    if ($null -eq $detDir -or $null -eq $recDir) {
        throw "PaddleOCR bundle at $Source is incomplete. Expected both det* and rec* model directories."
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

function Resolve-AppVersion {
    param(
        [string]$RepoRoot,
        [string]$ReleaseVersion
    )

    if ($ReleaseVersion) {
        return $ReleaseVersion
    }

    $pyprojectPath = Join-Path $RepoRoot 'pyproject.toml'
    if (-not (Test-Path $pyprojectPath)) {
        throw "pyproject.toml not found: $pyprojectPath"
    }

    foreach ($line in Get-Content -Path $pyprojectPath) {
        if ($line -match '^\s*version\s*=\s*"([^"]+)"\s*$') {
            return $Matches[1]
        }
    }

    throw "Unable to resolve release version from $pyprojectPath"
}

function Resolve-PythonModuleFile {
    param(
        [string]$PythonCommand,
        [string]$ModuleName
    )

    $modulePath = & $PythonCommand -c "import $ModuleName; print($ModuleName.__file__)"
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($modulePath)) {
        throw "Unable to resolve Python module path for $ModuleName"
    }
    return $modulePath.Trim()
}

function New-ZipFromDirectory {
    param(
        [string]$SourceDirectory,
        [string]$DestinationZipPath
    )

    if (Test-Path $DestinationZipPath) {
        Remove-Item -Path $DestinationZipPath -Force
    }

    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $SourceDirectory,
        $DestinationZipPath,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appVersion = Resolve-AppVersion -RepoRoot $repoRoot -ReleaseVersion $ReleaseVersion
$distDir = Join-Path $repoRoot 'dist'
$buildRoot = Join-Path $distDir 'build'
$releaseRoot = Join-Path $distDir 'release'
$bundleRoot = Join-Path $releaseRoot $Architecture
$appRoot = Join-Path $bundleRoot 'SCYTcheck'
$stagingBaseRoot = Join-Path $buildRoot ("release-staging-{0}" -f $Architecture)
$stagingRoot = $stagingBaseRoot
$stagingBundleRoot = Join-Path $stagingRoot $Architecture
$stagingAppRoot = Join-Path $stagingBundleRoot 'SCYTcheck'
$vendorRoot = if ($ThirdPartyRoot) { $ThirdPartyRoot } else { Join-Path $repoRoot 'third_party' }
$ffmpegSource = Join-Path $vendorRoot (Join-Path 'ffmpeg' $Architecture)
$paddleocrSource = Join-Path $vendorRoot (Join-Path 'paddleocr' $Architecture)
$specFile = if ($SpecPath) { $SpecPath } else { Join-Path $repoRoot 'build-config.spec' }
$zipPath = Join-Path $releaseRoot ("SCYTcheck-{0}-{1}.zip" -f $appVersion, $Architecture)

Write-Host "[build] Architecture: $Architecture"
Write-Host "[build] Version: $appVersion"
Write-Host "[build] Repo root: $repoRoot"
Write-Host "[build] Spec: $specFile"

Ensure-Directory -Path $distDir
Ensure-Directory -Path $buildRoot
Ensure-Directory -Path $releaseRoot
if (Test-Path $stagingRoot) {
    try {
        Remove-Item -Path $stagingRoot -Recurse -Force
    } catch {
        $suffix = Get-Date -Format 'yyyyMMdd-HHmmss'
        $stagingRoot = Join-Path $buildRoot ("release-staging-{0}-{1}" -f $Architecture, $suffix)
        $stagingBundleRoot = Join-Path $stagingRoot $Architecture
        $stagingAppRoot = Join-Path $stagingBundleRoot 'SCYTcheck'
        Write-Warning "[build] Could not clear staging directory due to locked files. Using $stagingRoot instead."
    }
}
Ensure-Directory -Path $stagingBundleRoot
Ensure-Directory -Path $stagingAppRoot

Test-RequiredPaddleOCRAssets -Source $paddleocrSource

$pythonCommand = $null

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

    Copy-Item -Path $builtApp -Destination $stagingBundleRoot -Recurse -Force
}

$ffmpegDestination = Join-Path $stagingAppRoot 'ffmpeg'
$paddleocrDestination = Join-Path $stagingAppRoot 'paddleocr_models'
$internalDestination = Join-Path $stagingAppRoot '_internal'

if (-not $pythonCommand) {
    $pythonCommand = Resolve-PythonCommand -PythonExe $PythonExe
}

$decoratorSource = Resolve-PythonModuleFile -PythonCommand $pythonCommand -ModuleName 'decorator'

Copy-OptionalTree -Source $ffmpegSource -Destination $ffmpegDestination -Label 'FFmpeg'
Copy-OptionalTree -Source $paddleocrSource -Destination $paddleocrDestination -Label 'PaddleOCR'
Copy-Item -Path $decoratorSource -Destination (Join-Path $internalDestination 'decorator.py') -Force

# Cleanup stale release ZIPs for this architecture (legacy and older versioned naming).
$staleZipCandidates = @(
    Get-ChildItem -Path $releaseRoot -Filter ("SCYTcheck-{0}.zip" -f $Architecture) -File -ErrorAction SilentlyContinue
    Get-ChildItem -Path $releaseRoot -Filter ("SCYTcheck-*-{0}.zip" -f $Architecture) -File -ErrorAction SilentlyContinue
) | Where-Object { $_.FullName -ne $zipPath } | Sort-Object FullName -Unique

foreach ($staleZip in $staleZipCandidates) {
    Write-Host "[build] Removing stale ZIP: $($staleZip.FullName)"
    Remove-Item -Path $staleZip.FullName -Force
}

New-ZipFromDirectory -SourceDirectory $stagingBundleRoot -DestinationZipPath $zipPath

$releaseBundleRefreshed = $true
if (Test-Path $bundleRoot) {
    try {
        Remove-Item -Path $bundleRoot -Recurse -Force
    } catch {
        $releaseBundleRefreshed = $false
        Write-Warning "[build] Could not refresh $bundleRoot because existing files are locked. Portable ZIP was created from staging."
    }
}

if ($releaseBundleRefreshed) {
    Ensure-Directory -Path $bundleRoot
    Copy-Item -Path $stagingAppRoot -Destination $bundleRoot -Recurse -Force
}

if ($releaseBundleRefreshed) {
    Write-Host "[build] Release bundle ready: $bundleRoot"
} else {
    Write-Host "[build] Release staging bundle ready: $stagingBundleRoot"
}
Write-Host "[build] Portable ZIP ready: $zipPath"
