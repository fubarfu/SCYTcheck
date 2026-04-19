param(
    [string]$DestinationRoot = "third_party/paddleocr/x64",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$destRoot = Resolve-Path -LiteralPath $repoRoot
$target = Join-Path $destRoot $DestinationRoot

$downloads = @(
    @{ Name = 'det_en'; Url = 'https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar' },
    @{ Name = 'cls'; Url = 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar' },
    @{ Name = 'rec_en'; Url = 'https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_rec_infer.tar' },
    @{ Name = 'rec_de'; Url = 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/multilingual/german_mobile_v2.0_rec_infer.tar' }
)

Ensure-Directory -Path $target

foreach ($item in $downloads) {
    $archive = Join-Path $target ($item.Name + '.tar')
    $extractPath = Join-Path $target $item.Name

    if ((Test-Path $extractPath) -and (-not $Force)) {
        Write-Host "[models] Skipping existing $($item.Name). Use -Force to redownload."
        continue
    }

    if (Test-Path $extractPath) {
        Remove-Item -Path $extractPath -Recurse -Force
    }

    Write-Host "[models] Downloading $($item.Name)"
    Invoke-WebRequest -Uri $item.Url -OutFile $archive

    $extractTemp = Join-Path $target ($item.Name + '_tmp')
    if (Test-Path $extractTemp) {
        Remove-Item -Path $extractTemp -Recurse -Force
    }
    Ensure-Directory -Path $extractTemp

    tar -xf $archive -C $extractTemp

    $topLevelDirs = @(Get-ChildItem -Path $extractTemp -Directory)
    if ($topLevelDirs.Count -eq 1) {
        Move-Item -Path $topLevelDirs[0].FullName -Destination $extractPath
    } else {
        Ensure-Directory -Path $extractPath
        Copy-Item -Path (Join-Path $extractTemp '*') -Destination $extractPath -Recurse -Force
    }

    if (Test-Path $extractTemp) {
        Remove-Item -Path $extractTemp -Recurse -Force
    }
    Remove-Item -Path $archive -Force

    Write-Host "[models] Staged $($item.Name) at $extractPath"
}

Write-Host "[models] Complete. Assets are staged under $target"
