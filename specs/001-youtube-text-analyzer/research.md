# Research Findings: YouTube Text Analyzer

**Date**: April 11, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Decision: YouTube Video Access Method

**Chosen**: Use yt-dlp for downloading video segments on-demand, as streaming full videos in real-time is complex and unreliable with minimal dependencies.

**Rationale**: While the spec clarified "stream the video", practical implementation requires buffering/downloading frames for OCR processing. yt-dlp is lightweight, widely used, and handles YouTube access reliably. It can download in segments to simulate streaming.

**Alternatives Considered**:
- pafy + youtube-dl: Similar to yt-dlp, but yt-dlp is more maintained.
- Direct API: YouTube API doesn't provide video streams for analysis.
- Browser automation: Too heavy, violates minimal dependencies.

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

**Chosen**: CSV with columns: Text, X, Y, Width, Height, Frequency

**Rationale**: Includes position and size for regions, frequency for grouping. Standard CSV readable in Excel/sheets.

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

## Decision: YouTube Streaming with Time-Based Frame Navigation

**Chosen**: yt-dlp for stream format negotiation + ffmpeg for frame seeking and extraction.

**Rationale**: yt-dlp reliably handles YouTube access. ffmpeg `-ss` flag enables arbitrary-second seeking, enabling scrollbar-based frame navigation (FR-018). No full download required.

**Alternatives Considered**:
- youtube-dl: Deprecated; yt-dlp is maintained fork.
- YouTube API: Requires OAuth; yt-dlp handles auth automatically.

**Implementation Details**:
- Use existing `video_service.py` pattern
- yt-dlp extracts live stream URL
- ffmpeg pipes frames to OpenCV at specified start_sec with fps control
- Region selector UI triggers frame extraction at scrollbar time value

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
- ✅ Bundling strategy: PyInstaller + onedir
- ✅ Code signing: Authenticode (self-signed or CA)
- ✅ YouTube streaming: yt-dlp + ffmpeg
- ✅ Tesseract bundling: Subfolder + env var
- ✅ Tkinter freezing: hiddenimports + TCL_LIBRARY

**Status**: Ready for Phase 1 Design (data-model.md, contracts/, quickstart.md)