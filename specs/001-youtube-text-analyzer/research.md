# Research Findings: YouTube Text Analyzer

**Date**: April 11, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Decision: YouTube Video Access Method

**Chosen**: Use yt-dlp for on-demand frame retrieval via stream URL negotiation and ffmpeg seeking, without requiring full-video downloads.

**Rationale**: On-demand frame retrieval aligns with FR-003 semantics while keeping dependencies minimal. yt-dlp reliably handles YouTube access, and ffmpeg supports second-based frame seeks for region selection and analysis.

**Alternatives Considered**:
- pafy + youtube-dl: Similar to yt-dlp, but yt-dlp is more maintained.
- Direct API: YouTube API doesn't provide video streams for analysis.
- Browser automation: Too heavy, violates minimal dependencies.

## Decision: URL Validation Strategy

**Chosen**: Two-stage validation before analysis: URL format validation followed by accessibility preflight check.

**Rationale**: Separates fast local validation from network-dependent reachability checks, producing clear user-facing errors and reducing wasted analysis startup.

**Alternatives Considered**:
- Format-only validation: defers failures too late.
- Runtime-only failure handling: unclear UX and noisy errors.

## Decision: Context Pattern Matching Strategy

**Chosen**: Case-insensitive substring matching against OCR text, with per-pattern optional `before_text` and `after_text` fields.

**Rationale**: This handles common OCR casing variance while avoiding regex complexity. Compound rules (both before and after set) provide precise extraction for predictable message templates.

**Alternatives Considered**:
- Exact matching only: Too brittle for OCR text variance.
- Regex-based patterns: More powerful but too complex for a lean UI and higher user error risk.

## Decision: Name Extraction Boundaries

**Chosen**: Extract trimmed substring based on pattern configuration:
- after only: text before `after_text`
- before only: text after `before_text`
- both: text between `before_text` and `after_text`

**Rationale**: Deterministic, easy to test, and consistent with user expectation for predictable surrounding text.

**Alternatives Considered**:
- Adjacent-token extraction only: Breaks multi-word names.
- Heuristic NLP extraction: unnecessary complexity.

## Decision: Deduplication and Occurrence Semantics

**Chosen**: Deduplicate by normalized player-name key across the entire video and output one CSV row per normalized name. Occurrence count is event-based, not frame-based.

**Normalization Rule**:
- lowercase
- trim leading/trailing whitespace
- collapse repeated internal whitespace

**Rationale**: Prevents duplicate rows from repeated frame detections and repeated appearances while preserving meaningful frequency as event counts.

**Alternatives Considered**:
- Frame-count frequencies: Inflated and less meaningful.
- Exact-string dedup only: Too sensitive to OCR variance.

## Decision: Appearance Event Merging

**Chosen**: Merge detections into one appearance event using a configurable detection-gap threshold, default 1.0 seconds.

**Rationale**: Tolerates intermittent OCR misses and avoids splitting one visual appearance into multiple false events.

**Alternatives Considered**:
- Strict contiguous-frame events: Over-splits due to OCR dropouts.
- Large fixed time buckets: Too coarse.

## Decision: OCR Implementation

**Chosen**: pytesseract with OpenCV preprocessing for frame text detection.

**Rationale**: pytesseract is the standard Python OCR library, free, and works well with OpenCV for image processing. Preprocessing (grayscale, thresholding) improves accuracy for game text.

**Alternatives Considered**:
- Google Cloud Vision: Requires API key, not minimal.
- EasyOCR: Similar to pytesseract, but pytesseract is more established.

## Decision: User-Defined Region Selection

**Chosen**: OpenCV window with mouse callbacks for rectangle selection.

**Rationale**: Allows users to draw rectangles on a paused frame. Simple, no extra dependencies.

**Alternatives Considered**:
- Tkinter canvas: Possible, but OpenCV provides better video integration.
- Config file: Less interactive.

## Decision: CSV Output Format

**Chosen**: Fixed-schema CSV with one row per normalized player name and event-based occurrence counts.

**Required Columns (in order)**: `PlayerName`, `NormalizedName`, `OccurrenceCount`, `FirstSeenSec`, `LastSeenSec`, `RepresentativeRegion`

**Rationale**: Preserves deduplicated business output while keeping enough metadata for verification and debugging.

**Alternatives Considered**:
- JSON: More complex for users.
- Plain text: Lacks structure.

## Decision: Application Bundling Strategy (Phase 0 - April 2026)

**Chosen**: PyInstaller with onedir mode + bundled FFmpeg, Tesseract, language data.

**Rationale**: PyInstaller is the standard for Python → Windows .exe. Onedir structure allows easy bundling of native binaries (FFmpeg, tesseract.exe) alongside Python runtime. Produces separate x64/x86 packages as per FR-011.

**Alternatives Considered**:
- cx_Freeze: Cross-platform but steeper curve; PyInstaller more mature for Windows.
- py2exe: Deprecated; PyInstaller is successor.
- Nuitka: Adds complexity; overkill for desktop app.

**Implementation Details**:
- Create `build-config.spec` with hiddenimports=[' tkinter', '_tkinter']
- Use `--onedir` mode for folder-based distribution
- Post-build: Copy FFmpeg binaries, tesseract.exe, tessdata/ into dist/ folder
- Create scytcheck.bat wrapper to launch dist/main.exe with correct PATH

## Decision: Code Signing for Distributed Packages

**Chosen**: Use Microsoft Authenticode with self-signed cert for dev; CA cert for production release.

**Rationale**: Reduces SmartScreen warnings on user download. SHA-256 signature required for Windows 10+. signtool.exe handles signing post-build.

**Alternatives Considered**:
- No signing: Acceptable for dev/testing; not for production.
- EV Certificate: Overkill unless brand reputation critical.

**Implementation Details**:
- Dev: Self-signed cert via PowerShell `New-SelfSignedCertificate`
- Prod: Obtain from CA (DigiCert, GlobalSign) ~$300-500/year
- Sign with signtool: `signtool sign /f cert.pfx /p password /t {timestamp_url} /fd SHA256 dist/main.exe`

## Decision: On-Demand Video Retrieval with Time-Based Frame Navigation

**Chosen**: yt-dlp for source URL negotiation + ffmpeg for frame seeking and extraction.

**Rationale**: yt-dlp reliably handles YouTube access. ffmpeg `-ss` flag enables arbitrary-second seeking, enabling scrollbar-based frame navigation (FR-018). No full download required.

**Alternatives Considered**:
- youtube-dl: Deprecated; yt-dlp is maintained fork.
- YouTube API: Requires OAuth; yt-dlp handles auth automatically.

**Implementation Details**:
- Use existing `video_service.py` pattern
- yt-dlp extracts live stream URL
- ffmpeg pipes frames to OpenCV at specified start_sec with fps control
- Region selector UI triggers frame extraction at scrollbar time value

## Decision: Region Interaction Scope

**Chosen**: Require explicit user capability to create, adjust, and confirm one or more rectangular regions before analysis starts.

**Rationale**: Converts implied behavior into testable requirement language and aligns implementation tasks with FR-032.

**Alternatives Considered**:
- Implicit-only behavior via FR-009: too ambiguous for task mapping.

## Decision: Tesseract Integration in Bundled Executables

**Chosen**: Bundle tesseract.exe + tessdata/ (eng, deu) in dist/tesseract/ subfolder.

**Rationale**: Tesseract is native binary; cannot pip install. Language data must be present. pytesseract supports runtime path config via env var (already in config.py).

**Alternatives Considered**:
- System tesseract: Violates bundling requirement (FR-010).
- Download on first run: Adds network dependency.

**Implementation Details**:
- Download Windows binaries from UB Mannheim
- Extract: dist/tesseract/tesseract.exe + dist/tesseract/tessdata/{eng, deu}.traineddata
- App startup: `os.environ['TESSERACT_CMD'] = os.path.join(app_dir, 'tesseract/tesseract.exe')`

## Decision: Tkinter Freezing with PyInstaller

**Chosen**: Include explicit hiddenimports + TCL_LIBRARY environment setup at runtime.

**Rationale**: Tkinter is bundled with CPython. PyInstaller handles it well in recent versions. Main issue: TCL/TK shared libraries must be found. Explicit setup prevents runtime failures on clean Windows machines.

**Alternatives Considered**:
- Qt/PySide: Heavier; overkill for simple UI.
- PySimpleGUI: Adds dependency layer.

**Implementation Details**:
- spec file: `hiddenimports=['tkinter', '_tkinter']`
- main.py startup:
  ```python
  import os, tkinter
  tcl_path = os.path.join(app_dir, 'tcl86/lib')
  os.environ['TCL_LIBRARY'] = tcl_path
  os.environ['TK_LIBRARY'] = tcl_path
  ```
- Test on clean Windows VM

---

## Summary: Research Complete

**All clarifications from spec have solutions identified**:
- Bundling strategy: PyInstaller + onedir
- Code signing: Authenticode (self-signed or CA)
- Video access: yt-dlp + ffmpeg seek
- Tesseract bundling: Subfolder + env var
- Tkinter freezing: hiddenimports + TCL_LIBRARY
- Context pattern matching: case-insensitive substring with optional before/after
- Dedup semantics: normalized-name dedup with event-based occurrence counting
- Performance-aware event aggregation: configurable gap threshold (default 1.0s)
- URL validation semantics: format + accessibility preflight
- Fixed CSV schema requirements for summary output
- Explicit region interaction requirement for create/adjust/confirm behavior

**Status**: Ready for Phase 1 design and task generation.