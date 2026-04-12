param(
    [string]$InputPath,
    [string]$CertificatePath,
    [string]$CertificatePassword,
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-SignTool {
    $command = Get-Command 'signtool.exe' -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return $command.Source
    }

    $sdkRoots = @(
        "$Env:ProgramFiles(x86)\Windows Kits\10\bin",
        "$Env:ProgramFiles\Windows Kits\10\bin"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $sdkRoots) {
        $candidate = Get-ChildItem -Path $root -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($null -ne $candidate) {
            return $candidate.FullName
        }
    }

    throw 'signtool.exe was not found in PATH or Windows SDK locations.'
}

function Get-SignableFiles {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        return ,(Get-Item -Path $Path)
    }

    Get-ChildItem -Path $Path -Recurse -File | Where-Object {
        $_.Extension -in '.exe', '.dll', '.msi'
    }
}

if (-not $InputPath) {
    Write-Host "[sign] No input provided."
    Write-Host "[sign] Provide -InputPath and -CertificatePath to sign release binaries."
    exit 0
}

if (-not (Test-Path $InputPath)) {
    throw "Input path not found: $InputPath"
}

if (-not $CertificatePath) {
    Write-Host "[sign] No certificate provided."
    Write-Host "[sign] Skipping signing step."
    exit 0
}

if (-not (Test-Path $CertificatePath)) {
    throw "Certificate path not found: $CertificatePath"
}

$signTool = Resolve-SignTool
$targets = @(Get-SignableFiles -Path $InputPath)

if ($targets.Count -eq 0) {
    Write-Host "[sign] No signable files found under $InputPath"
    exit 0
}

Write-Host "[sign] Using signtool: $signTool"
Write-Host "[sign] Timestamp: $TimestampUrl"

foreach ($target in $targets) {
    $arguments = @(
        'sign',
        '/fd', 'SHA256',
        '/td', 'SHA256',
        '/tr', $TimestampUrl,
        '/f', $CertificatePath
    )

    if ($CertificatePassword) {
        $arguments += @('/p', $CertificatePassword)
    }

    $arguments += $target.FullName

    Write-Host "[sign] Signing $($target.FullName)"
    & $signTool @arguments
}
