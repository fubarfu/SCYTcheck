# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: April 11, 2026 | **Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-text-analyzer/spec.md`

## Summary

Build a Windows desktop app that analyzes YouTube gameplay videos for player names in user-defined regions, supports configurable surrounding-text extraction rules, and exports deduplicated CSV output. Extraction uses case-insensitive context-pattern matching with optional before/after compound rules, and aggregates repeated detections into per-player appearance events with a default 1.0s event-gap merge threshold.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter  
**Storage**: CSV files + local JSON settings file (`scytcheck_settings.json`)  
**Testing**: pytest (unit + integration)  
**Target Platform**: Windows x64 and x86  
**Project Type**: Desktop GUI application  
**Performance Goals**: Analyze a 10-minute video in under 5 minutes; avoid duplicate rows and keep aggregation memory bounded by unique normalized names  
**Constraints**: Portable offline-capable bundled runtime, bundled FFmpeg and Tesseract (eng/deu), code-signing for release, no mandatory external installs  
**Scale/Scope**: Single-window app with advanced settings, OCR region analysis, name extraction and dedup aggregation, CSV export

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 assessment:
1. PASS - Simple and Modular Architecture: service/component layering remains intact.
2. PASS - Readability Over Cleverness: rules are explicit (normalization and event merge policy).
3. PASS - Testing for Business Logic: new logic (pattern extraction and dedup) is testable via deterministic unit tests.
4. PASS - Minimal Dependencies: no new external dependency introduced for pattern matching/dedup.
5. PASS - No Secrets in Repository: unchanged; config file stores non-secret user settings.
6. PASS - Windows-Friendly Development: feature targets Windows and bundled deployment workflow.
7. PASS - Incremental Changes and Working State: additions are isolated to services/components and backward-compatible defaults.

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

**Structure Decision**: Keep the existing single-project desktop architecture; extend `services` for extraction, normalization, and dedup/event aggregation logic; extend `components` for advanced settings UI.

## Phase 0: Research & Resolution

All technical unknowns from updated requirements are resolved in [specs/001-youtube-text-analyzer/research.md](research.md):
- On-demand video access with yt-dlp + ffmpeg seeking.
- Case-insensitive context-pattern matching without regex.
- Compound before/after rule evaluation.
- Dedup by normalized key across whole video.
- Appearance-event counting with configurable gap threshold (default 1.0s).

No unresolved clarifications remain.

## Phase 1: Design & Contracts

Design artifacts produced and aligned with FR-001 to FR-030:
- [specs/001-youtube-text-analyzer/data-model.md](data-model.md)
- [specs/001-youtube-text-analyzer/contracts/ocr_service.md](contracts/ocr_service.md)
- [specs/001-youtube-text-analyzer/contracts/video_streaming.md](contracts/video_streaming.md)
- [specs/001-youtube-text-analyzer/quickstart.md](quickstart.md)

## Post-Design Constitution Check

1. PASS - Architecture remains modular with explicit responsibilities.
2. PASS - Business rules are explicit and testable.
3. PASS - No unnecessary dependency added.
4. PASS - Windows packaging/deployment constraints preserved.

**Gate Result**: PASS

## Complexity Tracking

No constitution violations requiring justification.
