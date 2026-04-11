# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: April 11, 2026 | **Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a Windows desktop app that analyzes on-demand YouTube video frames inside user-defined regions, extracts player names using configurable context patterns, and exports a fixed-schema deduplicated CSV summary. The system must validate URL format and accessibility before analysis, aggregate repeated detections into appearance events with a default 1.0s merge threshold, and support portable signed distribution bundles for x64/x86.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter  
**Storage**: CSV files + local JSON settings file (`scytcheck_settings.json`)  
**Testing**: pytest (unit + integration)  
**Target Platform**: Windows x64 and x86  
**Project Type**: Desktop GUI application  
**Performance Goals**: Analyze a 10-minute video in under 5 minutes while keeping dedup memory bounded by unique normalized names  
**Constraints**: Portable bundled runtime with FFmpeg/Tesseract data, no required external installs, code-signing for releases  
**Scale/Scope**: Single-window UI with region selector, advanced settings (context patterns + filtering + gap threshold), deduplicated summary export

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 assessment:
1. PASS - Simple and Modular Architecture: extends existing `components/services/data` layering.
2. PASS - Readability Over Cleverness: business rules are explicit (pattern matching, normalization, event merge).
3. PASS - Testing for Business Logic: plan includes unit/integration validation for extraction and aggregation logic.
4. PASS - Minimal Dependencies: no new external dependency required for clarified functionality.
5. PASS - No Secrets in Repository: settings file stores non-secret preferences only.
6. PASS - Windows-Friendly Development: requirements and release steps target Windows explicitly.
7. PASS - Incremental Changes and Working State: phased rollout preserves independent user-story checkpoints.

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

**Structure Decision**: Keep the single-project desktop structure and add clarified behavior in existing modules (`analysis_service`, `ocr_service`, `video_service`, `main_window`, and `export_service`) without introducing new top-level subsystems.

## Phase 0: Research & Resolution

All major unknowns are resolved in [specs/001-youtube-text-analyzer/research.md](research.md):
- On-demand frame retrieval from YouTube (no full download requirement)
- URL preflight accessibility validation strategy
- Context-pattern extraction and compound matching behavior
- Deduplication and fixed CSV schema for `PlayerSummary`
- Event-based occurrence aggregation with configurable threshold (default 1.0s)
- Windows packaging, signing, and dependency bundling strategy

No `NEEDS CLARIFICATION` items remain.

## Phase 1: Design & Contracts

Design artifacts aligned with FR-001 through FR-032:
- [specs/001-youtube-text-analyzer/data-model.md](data-model.md)
- [specs/001-youtube-text-analyzer/contracts/ocr_service.md](contracts/ocr_service.md)
- [specs/001-youtube-text-analyzer/contracts/video_streaming.md](contracts/video_streaming.md)
- [specs/001-youtube-text-analyzer/quickstart.md](quickstart.md)

## Post-Design Constitution Check

1. PASS - Architecture remains modular and incremental.
2. PASS - Core business logic is explicit and testable.
3. PASS - Dependency surface remains minimal.
4. PASS - Windows distribution requirements remain first-class.

**Gate Result**: PASS

## Complexity Tracking

No constitution violations requiring justification.
