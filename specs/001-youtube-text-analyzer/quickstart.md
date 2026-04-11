# Quickstart: YouTube Text Analyzer

**Date**: April 12, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Prerequisites

- Python 3.11+
- Windows OS
- Internet connection
- FFmpeg available (bundled in packaged builds)
- Tesseract OCR with English/German data (bundled in packaged builds)

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Ensure Tesseract is installed for development runs.

## Usage

1. Run `python -m src.main`.
2. Enter a YouTube URL and confirm validation (format + accessibility preflight).
3. Choose video quality for retrieval (default is best available quality).
4. Launch region selection and verify the popup opens in the foreground.
5. Confirm instruction text is shown in a dedicated area below the video preview and does not overlay video content.
6. Use the time scrollbar to pick a representative frame, create one or more regions, adjust as needed, and confirm the final set.
7. Open Advanced Settings and review context patterns:
   - default `after_text`: `joined`
   - default `after_text`: `connected`
8. Optional: Add additional before/after pattern rules, toggle pattern-only output filtering, adjust OCR sensitivity for lower-quality video, and tune event-gap threshold (default 1.0 sec).
9. Optional: Enable analysis logging (default is off) to generate a sidecar `<output_base>_log.csv` file.
10. Select only an output folder (filename is auto-generated).
11. Start analysis and wait for completion.
12. If export fails because the file is locked or otherwise unavailable, use `Retry Export` to write the summary again without rerunning OCR.
13. Open summary CSV output and verify exact headers:
   `PlayerName, StartTimestamp`.
14. Verify `PlayerName` values preserve on-screen extracted form (not lowercased/normalized), while duplicate rows are still grouped by normalized key.

15. If logging was enabled, open sidecar log CSV and verify columns are:
   `TimestampSec, RawString, TestedStringRaw, TestedStringNormalized, Accepted, RejectionReason, ExtractedName, RegionId, MatchedPattern, NormalizedName, OccurrenceCount, StartTimestamp, EndTimestamp, RepresentativeRegion`.

## Release Smoke Check

1. Run `powershell -ExecutionPolicy Bypass -File scripts/release/build.ps1 -Architecture x64 -BundleOnly` to stage a portable bundle layout.
2. Confirm the script creates `dist/release/x64/SCYTcheck` and `dist/release/SCYTcheck-x64.zip`.
3. Packaging is valid without signing; no certificate is required for portable bundle output.
4. Optional: if a signing certificate is available, run `powershell -ExecutionPolicy Bypass -File scripts/release/sign.ps1 -InputPath dist/release/x64/SCYTcheck -CertificatePath <certificate.pfx>`.

## Development

- Run all tests: `pytest tests/`
- Run unit tests only: `pytest tests/unit/`
- Key business rules to test:
  - context-pattern matching and extraction boundaries
  - single-token extraction rule
  - display-name selection vs normalization-key grouping
  - appearance event merging using the configured gap threshold
