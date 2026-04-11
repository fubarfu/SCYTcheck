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