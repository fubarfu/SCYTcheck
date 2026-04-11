# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: April 11, 2026 | **Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a Windows desktop app that analyzes YouTube video frames in user-defined regions, extracts player names via configurable context patterns, and exports deduplicated fixed-schema CSV summaries. The implementation remains recall-first for context-matched names, includes configurable OCR sensitivity for lower-quality video, and enforces UI legibility/accessibility constraints such as non-overlapping labels and a foreground region-selection popup with clearly readable instructions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter, numpy  
**Storage**: CSV output files + local JSON settings file (`scytcheck_settings.json`)  
**Testing**: pytest (unit + integration)  
**Target Platform**: Windows x64 and x86  
**Project Type**: Desktop GUI application  
**Performance Goals**: SC-001 (10-minute video analyzed in under 5 minutes), aspirational high recall for context-matched names under standard video quality  
**Constraints**: On-demand retrieval (no full download), bundled FFmpeg/Tesseract for packaged builds, signed artifacts, clear foreground popup and legible instruction overlays during region selection  
**Scale/Scope**: Single-process desktop app with `src/components`, `src/services`, `src/data`, and corresponding `tests/` suites

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 assessment:
1. PASS - **Simple and Modular Architecture**: Existing `components/services/data` separation remains intact.
2. PASS - **Readability Over Cleverness**: Business rules (pattern matching, normalization, event merging, UI constraints) are explicit and testable.
3. PASS - **Testing for Business Logic**: Unit/integration tests cover OCR extraction, aggregation semantics, settings persistence, and UI interaction behavior.
4. PASS - **Minimal Dependencies**: No new external frameworks required.
5. PASS - **No Secrets in Repository**: Configuration is non-sensitive.
6. PASS - **Windows-Friendly Development**: Runtime and packaging targets remain Windows-first.
7. PASS - **Incremental Changes and Working State**: Story-based tasking with independent checkpoints is preserved.

**Gate Result**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-text-analyzer/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ocr_service.md
│   └── video_streaming.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── main.py
├── config.py
├── components/
│   ├── main_window.py
│   ├── url_input.py
│   ├── file_selector.py
│   ├── region_selector.py
│   └── progress_display.py
├── services/
│   ├── analysis_service.py
│   ├── export_service.py
│   ├── ocr_service.py
│   ├── video_service.py
│   └── logging.py
└── data/
    └── models.py

tests/
├── unit/
└── integration/
```

**Structure Decision**: Continue with the existing single-project desktop structure and implement new clarified behavior (recall-first extraction, quality guidance, foreground popup, instruction legibility, and layout non-overlap) within current UI/service modules.

## Phase 0: Research & Resolution

Research outputs in [specs/001-youtube-text-analyzer/research.md](research.md) resolve all open technical questions, including:
- Recall-first extraction behavior for context-pattern-matched player names.
- OCR sensitivity tuning strategy for low-quality video.
- Foreground/focus behavior for region-selection popup.
- Legible instruction text requirements in region selector.

No `NEEDS CLARIFICATION` items remain.

## Phase 1: Design & Contracts

Design outputs are updated and aligned with FR-001 through FR-037:
- [specs/001-youtube-text-analyzer/data-model.md](data-model.md)
- [specs/001-youtube-text-analyzer/contracts/ocr_service.md](contracts/ocr_service.md)
- [specs/001-youtube-text-analyzer/contracts/video_streaming.md](contracts/video_streaming.md)
- [specs/001-youtube-text-analyzer/quickstart.md](quickstart.md)

## Post-Design Constitution Check

1. PASS - Architecture remains modular with no extra subsystem complexity.
2. PASS - Clarified business behavior is explicit and covered by testable contracts.
3. PASS - Dependency set remains unchanged and minimal.
4. PASS - Windows-friendly packaging/runtime constraints are preserved.

**Gate Result**: PASS

## Complexity Tracking

No constitution violations requiring justification.
