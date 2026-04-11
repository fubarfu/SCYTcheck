param(
    [string]$InputPath,
    [string]$CertificatePath,
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $InputPath) {
    Write-Host "[sign] No input provided."
    Write-Host "[sign] TODO: implement signtool invocation for built executables and packages."
    exit 0
}

if (-not (Test-Path $InputPath)) {
    throw "Input path not found: $InputPath"
}

Write-Host "[sign] Target: $InputPath"
Write-Host "[sign] Certificate: $CertificatePath"
Write-Host "[sign] Timestamp: $TimestampUrl"
Write-Host "[sign] TODO: call signtool.exe with SHA-256 digest and timestamp."
