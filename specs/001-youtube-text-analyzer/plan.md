# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: April 11, 2026 | **Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a Windows desktop app that analyzes on-demand YouTube frames within user-defined regions, extracts player names using configurable context patterns, and exports fixed-schema deduplicated CSV summaries. The workflow includes two-stage URL validation, event-based occurrence aggregation with default 1.0-second merge threshold, and portable signed packaging for x64 and x86 distributions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter  
**Storage**: CSV output files + local JSON settings file (`scytcheck_settings.json`)  
**Testing**: pytest (unit + integration)  
**Target Platform**: Windows x64 and x86  
**Project Type**: Desktop GUI application  
**Performance Goals**: Analyze a 10-minute video in under 5 minutes (SC-001) while keeping memory bounded by unique normalized-name aggregates  
**Constraints**: No full video download required, portable bundled runtime, bundled FFmpeg/Tesseract assets, signed release artifacts  
**Scale/Scope**: Single desktop application with region selector, advanced settings, OCR/aggregation pipeline, and CSV export

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 assessment:
1. PASS - Simple and Modular Architecture: retains existing `components/services/data` layering.
2. PASS - Readability Over Cleverness: business rules are explicit (normalization, extraction boundaries, event merging).
3. PASS - Testing for Business Logic: plan/tasks include unit and integration tests for OCR extraction and aggregation behavior.
4. PASS - Minimal Dependencies: no additional dependencies beyond approved stack.
5. PASS - No Secrets in Repository: persisted settings contain only non-sensitive preferences.
6. PASS - Windows-Friendly Development: implementation and packaging targets remain Windows-first.
7. PASS - Incremental Changes and Working State: phased execution supports independent story validation.

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

**Structure Decision**: Keep the current single-project desktop layout and extend behavior in existing modules rather than introducing new top-level subsystems.

## Phase 0: Research & Resolution

Research artifacts in [specs/001-youtube-text-analyzer/research.md](research.md) resolve all technical unknowns:
- On-demand frame retrieval strategy via yt-dlp/ffmpeg semantics
- Two-stage YouTube URL validation approach
- Context-pattern matching and extraction-boundary behavior
- Deduplication model and event-based occurrence semantics
- Fixed CSV schema and no-text export behavior
- Windows packaging/signing strategy including bundled FFmpeg and Tesseract assets

No open `NEEDS CLARIFICATION` items remain.

## Phase 1: Design & Contracts

Design artifacts are complete and aligned to FR-001 through FR-032:
- [specs/001-youtube-text-analyzer/data-model.md](data-model.md)
- [specs/001-youtube-text-analyzer/contracts/ocr_service.md](contracts/ocr_service.md)
- [specs/001-youtube-text-analyzer/contracts/video_streaming.md](contracts/video_streaming.md)
- [specs/001-youtube-text-analyzer/quickstart.md](quickstart.md)

## Post-Design Constitution Check

1. PASS - Architecture remains modular and incremental.
2. PASS - Core business logic is explicit and testable.
3. PASS - Dependency surface remains minimal and justified.
4. PASS - Windows distribution and release requirements remain first-class.

**Gate Result**: PASS

## Complexity Tracking

No constitution violations requiring justification.
