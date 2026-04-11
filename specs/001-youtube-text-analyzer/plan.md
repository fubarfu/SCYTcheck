# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-11 | **Spec**: `specs/001-youtube-text-analyzer/spec.md`
**Input**: Feature specification from `C:\Users\SteSt\source\SCYTcheck\specs\001-youtube-text-analyzer\spec.md`

## Summary

Build a Windows desktop app that analyzes on-demand YouTube video frames inside user-selected regions, extracts player names with OCR and context-pattern rules, deduplicates detections into event-based summaries, and exports deterministic CSV output. The implementation includes advanced controls for video quality selection (default best, no auto-downgrade), OCR sensitivity tuning, and optional sidecar audit logging with fixed schema and timestamp format.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter, numpy  
**Storage**: CSV output files + local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json` fallback to local file)  
**Testing**: pytest (unit + integration), ruff linting  
**Target Platform**: Windows desktop (x64 and x86 packaged builds)  
**Project Type**: Desktop application  
**Performance Goals**: Complete 10-minute analysis in under 5 minutes under representative conditions (SC-001)  
**Constraints**: On-demand frame retrieval only (no full download), retry failed frame retrieval up to 3 times, stream processing without full-frame history retention, keyboard-operable core workflow, deterministic CSV schemas  
**Scale/Scope**: Single-user local workflow per session, one analyzed video at a time, support for long videos (>1 hour) with bounded memory behavior

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase-0 gate check:
- Principle I (Simple and Modular Architecture): PASS. Service-layer contracts and focused UI components keep responsibilities separated.
- Principle II (Readability Over Cleverness): PASS. Deterministic extraction/dedup rules are explicit and testable.
- Principle III (Testing for Business Logic): PASS. Non-trivial logic (pattern matching, event merging, logging semantics) is planned for unit/integration coverage.
- Principle IV (Minimal Dependencies): PASS. Uses existing project stack only; no new heavyweight libraries required.
- Principle V (No Secrets in Repository): PASS. No secret-bearing changes; config remains local/user-scoped.
- Principle VI (Windows-Friendly Development): PASS. Windows packaging, signing, and dependency bundling remain first-class.
- Principle VII (Incremental Changes and Working State): PASS. Requirements are integrated in small, traceable increments.

Post-Phase-1 re-check:
- PASS. Data model, contracts, and quickstart preserve modularity, testability, and Windows-focused delivery without adding unnecessary complexity.

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
│   ├── region_selector.py
│   ├── url_input.py
│   ├── file_selector.py
│   └── progress_display.py
├── services/
│   ├── analysis_service.py
│   ├── video_service.py
│   ├── ocr_service.py
│   ├── export_service.py
│   └── logging.py
└── data/
    └── models.py

tests/
├── unit/
└── integration/
```

**Structure Decision**: Keep the current single-project desktop-app structure. Extend existing `services`, `components`, and `data` modules to implement new quality-selection, logging, and region-selector presentation requirements while preserving current module boundaries.

## Complexity Tracking

No constitution violations requiring justification.
