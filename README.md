# SCYTcheck

SCYTcheck analyzes text in selected regions of a YouTube video and exports:
- a summary CSV (player name + first seen timestamp)
- an optional detailed log CSV for troubleshooting and validation

## 60-Second Quick Start

1. Download the latest `SCYTcheck-<version>-<arch>.zip` from Releases.
2. Extract the ZIP.
3. Open the extracted folder and run `SCYTcheck.exe`.
4. Paste a YouTube URL.
5. Pick an output folder.
6. Click **Select Regions + Analyze**, select regions, and confirm.
7. Open the exported CSV when analysis finishes.

If Windows SmartScreen appears, choose **More info** and then **Run anyway**.

## Recommended for Most Users: Portable Package (Windows)

Use the portable release package. You do not need to install Python or run pip.

1. Download the latest portable ZIP from the repository Releases page.
2. Extract it to a writable folder (for example Desktop or Documents).
3. Open the extracted `SCYTcheck` folder.
4. Run `SCYTcheck.exe`.
5. If Windows SmartScreen appears, select **More info** and then **Run anyway**.

Settings are saved between runs in `%APPDATA%/SCYTcheck/scytcheck_settings.json` when writable, otherwise next to the executable.

## First Run Workflow

1. Enter a valid YouTube URL.
2. Choose an output folder. The filename is generated automatically.
3. Optional: open **Advanced Settings** to adjust video quality, OCR confidence, context patterns, event-gap threshold, and detailed logging.
4. Click **Select Regions + Analyze**.
5. In the region selector, choose one or more regions and confirm.
6. Wait for analysis to complete.
7. Open the exported summary CSV.
8. If logging is enabled, review the matching `_log.csv` sidecar file.

If export fails after analysis (for example due to file lock or permissions), use **Retry Export** to write output again without re-running OCR.

## Output Formats

Summary CSV header:

```text
PlayerName,StartTimestamp
```

Optional sidecar log CSV header:

```text
TimestampSec,RawString,TestedStringRaw,TestedStringNormalized,Accepted,RejectionReason,ExtractedName,RegionId,MatchedPattern,NormalizedName,OccurrenceCount,StartTimestamp,EndTimestamp,RepresentativeRegion
```

## Troubleshooting

App does not start:
- Ensure the app is run from the extracted folder, not from inside the ZIP.
- Verify security software did not quarantine bundled files.

No text detected:
- Re-check selected regions.
- Lower OCR confidence in Advanced Settings.
- Choose a clearer video quality.

YouTube URL rejected or inaccessible:
- Confirm the URL is a standard YouTube link.
- Confirm internet access and that the video is available.

## For Developers (Source Run)

Use this path only if you are developing SCYTcheck.

Requirements:
- Python 3.11+
- Windows
- Tesseract OCR available on PATH or installed in a standard location

Setup:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run:

```powershell
python -m src.main
```

## Build Portable Bundle (Maintainers)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/build.ps1 -Architecture x64
```

Optional signing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/sign.ps1 -InputPath dist/release/x64/SCYTcheck -CertificatePath C:\path\to\certificate.pfx
```

## Development Validation

```powershell
pytest tests/ -q
ruff check src tests --select=E,F,W
```

## Latest Validation

- Date: 2026-04-12
- `pytest tests/ -q`: 156 passed
- `ruff check src tests --select=E,F,W`: all checks passed
