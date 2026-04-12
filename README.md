# SCYTcheck - YouTube Text Analyzer

SCYTcheck analyzes a YouTube video for text in user-selected regions and exports a minimal player summary CSV plus an optional detailed sidecar log.

## Requirements

- Python 3.11+
- Tesseract OCR installed on Windows

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For packaged Windows builds, the release pipeline expects optional third-party bundles under `third_party/ffmpeg/<arch>` and `third_party/tesseract/<arch>`.

## Run

```bash
python -m src.main
```

## Workflow

1. Enter a YouTube URL
2. Choose an output folder; the summary filename is generated automatically from the video ID and timestamp
3. Optional: open Advanced Settings to change quality, context patterns, OCR sensitivity, event-gap threshold, and logging
4. Click "Select Regions + Analyze"
5. In the region selector, use the time scrollbar to choose frames and confirm one or more regions; instructions are shown below the video preview
6. Wait for progress completion and open the summary CSV output
7. If logging is enabled, inspect the matching `_log.csv` sidecar for detailed OCR and aggregation records

The summary CSV always uses this exact schema:

```text
PlayerName,StartTimestamp
```

When logging is enabled, the sidecar log uses this schema:

```text
TimestampSec,RawString,TestedStringRaw,TestedStringNormalized,Accepted,RejectionReason,ExtractedName,RegionId,MatchedPattern,NormalizedName,OccurrenceCount,StartTimestamp,EndTimestamp,RepresentativeRegion
```

If export fails after analysis, use the `Retry Export` button to write the files again without rerunning video detection.

## Release Packaging

Create a portable bundle with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/build.ps1 -Architecture x64
```

The build script will:

- run the PyInstaller spec in `build-config.spec`
- stage optional FFmpeg and Tesseract bundles when present
- create a portable ZIP in `dist/release`

Sign built binaries with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/sign.ps1 -InputPath dist/release/x64/SCYTcheck -CertificatePath C:\path\to\certificate.pfx
```

## Development

```bash
pytest
ruff check .
black --check .
```

## Latest Validation

- Date: 2026-04-12
- `pytest tests/ -q`: 156 passed
- `ruff check src tests --select=E,F,W`: all checks passed
