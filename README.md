# SCYTcheck

SCYTcheck watches selected regions of a YouTube (or local) video, reads text using OCR, and exports a CSV of detected player names with their first-seen timestamps.

An optional detailed log CSV is also available for troubleshooting.

## 60-Second Quick Start

1. Download the latest `SCYTcheck-<version>-<arch>.zip` from Releases.
2. Extract the ZIP.
3. Open the extracted folder and run `SCYTcheck.exe`.
4. SCYTcheck opens in your browser on the **Analysis** view.
5. Paste a YouTube URL (or switch to **Local file**) and click **Load**.
6. Draw one or more scan regions on the preview frame.
7. Click **Run analysis**.
8. Review opens automatically when scanning finishes.

If Windows SmartScreen appears, choose **More info** and then **Run anyway**.

## Recommended for Most Users: Portable Package (Windows)

Use the portable release package. You do not need to install Python or run pip.

1. Download the latest portable ZIP from the repository Releases page.
2. Extract it to a writable folder (for example Desktop or Documents).
3. Open the extracted `SCYTcheck` folder.
4. Run `SCYTcheck.exe`.
5. If Windows SmartScreen appears, select **More info** and then **Run anyway**.

Settings are saved between runs in `%APPDATA%/SCYTcheck/scytcheck_settings.json`.
If `%APPDATA%` is unavailable, SCYTcheck falls back to a local `scytcheck_settings.json`.

## Detailed Workflow

1. Open **Analysis** and enter a YouTube URL or local file path.
2. Click **Load** to fetch a preview frame from the video.
3. Draw one or more scan regions over the areas that show player names.
4. Optionally expand **Analysis settings** and **Text patterns** to fine-tune detection.
5. Click **Run analysis** to start. SCYTcheck will tell you whether it is creating a new project or merging into an existing one.
6. **Review** opens automatically when scanning finishes.
7. In Review, confirm, reject, or edit candidate names and resolve grouped spellings.

## How Projects Work

Each video has a single project that accumulates data across multiple analysis runs.

- Running analysis on a video you have analyzed before merges the new results into the existing project rather than overwriting it.
- Review always shows the combined, up-to-date picture for that video, including decisions you made in previous sessions.
- The **Videos** tab lists all projects found in your configured project location. Click any entry to open it in Review.
- The **Settings** gear icon lets you change the project location and verify it is writable.

## Robustness and Speed Controls

The **Analysis settings** panel includes controls for OCR robustness and speed:

| Setting | Default | Effect |
|---------|---------|--------|
| Matching tolerance | `0.75` | How closely OCR output must match a known pattern. Lower values (e.g. `0.65`) tolerate more OCR errors; raise it to reduce false positives. Range: `0.60`–`0.95`. |
| Gating enabled | Off | Skips OCR on a region when it has not visually changed since the last frame. Speeds up analysis on static overlays without affecting accuracy. |
| Gating threshold | `0.02` | Sensitivity of the change detector. Lower values require more change before OCR runs. |
| Detailed sidecar log | Off | Writes a full per-frame log CSV alongside the summary for troubleshooting. |
| Validate RSI player profiles | On | Checks each detected name against `robertsspaceindustries.com` as scanning runs (max 1 request/second). Found names score higher in recommendations; not-found names score lower. |

When gating is enabled, analysis completion shows:

```text
Gating Summary: Evaluated <total>, OCR Executed <executed>, OCR Skipped <skipped> (<skip_pct>%).
```

## Where Files Are Saved

All output goes into the **Project location** set in **Settings** (default: `%APPDATA%\SCYTcheck\projects`). Inside that folder, each video gets its own sub-folder identified by a hash of the video URL. Each analysis run writes `result_latest.csv` and keeps a sidecar file that stores your review decisions.

## Reset Settings to Defaults

To reset all analysis settings back to app defaults:

1. Close SCYTcheck.
2. Delete the persisted settings file:
	- Preferred location: `%APPDATA%/SCYTcheck/scytcheck_settings.json`
	- Fallback location (when `%APPDATA%` is unavailable): local `scytcheck_settings.json`
3. Start SCYTcheck again. A fresh settings file is created automatically with default values.

## Output Formats

Summary CSV header:

```text
PlayerName,StartTimestamp
```

Optional sidecar log CSV header:

```text
TimestampSec,TestedStringNormalized,Accepted,RejectionReason,ExtractedName,RegionId,MatchedPattern,NormalizedName,OccurrenceCount,StartTimestamp,EndTimestamp,RepresentativeRegion
```

## Troubleshooting

**App does not start**
- Run `SCYTcheck.exe` from the extracted folder, not from inside the ZIP.
- Check that security software has not quarantined bundled files.

**No text detected**
- Make sure your scan regions cover the area where names appear.
- Try a higher video quality in Analysis settings.
- Lower matching tolerance (e.g. `0.65`) if OCR often misreads characters.

**Analysis is slow**
- Enable **Gating** in Analysis settings to skip OCR on unchanged frames.
- Make sure the gating threshold is near `0.02`.

**YouTube URL not accepted or video unavailable**
- Use a standard `youtube.com/watch?v=...` or `youtu.be/...` URL.
- Confirm you have internet access and the video is publicly available.

## For Developers (Source Run)

This section is for contributors working on SCYTcheck itself.

For UI changes, the Google Stitch project is the design authority. Consult it before implementing any frontend work and note any deviations in the relevant spec.

Requirements:
- Python 3.11+
- Windows
- PaddleOCR model assets available under `third_party/paddleocr/x64` (or configured with `SCYTCHECK_PADDLEOCR_MODEL_ROOT`)

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
powershell -ExecutionPolicy Bypass -File scripts/release/build.ps1 -Architecture x64 -ReleaseVersion 1.2
```

Optional signing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/sign.ps1 -InputPath dist/release/x64/SCYTcheck -CertificatePath C:\path\to\certificate.pfx
```

## Validation

Run validation locally with:

```powershell
pytest tests/ -q
ruff check src tests --select=E,F,W
```
