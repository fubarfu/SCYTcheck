# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-11 | **Spec**: `specs/001-youtube-text-analyzer/spec.md`
**Input**: Feature specification from `specs/001-youtube-text-analyzer/spec.md`

## Summary

Build a Windows desktop app that analyzes on-demand YouTube frames in user-defined regions, extracts player names via OCR and context patterns, and exports a minimal summary CSV containing `PlayerName` and `StartTimestamp`. Advanced settings provide quality selection (default best, no auto-downgrade), OCR sensitivity controls, and optional sidecar logging with a deterministic schema. When logging is disabled, analysis proceeds without warning prompts.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python, pytesseract, yt-dlp, tkinter, numpy  
**Storage**: CSV output files + local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json` fallback to local file)  
**Testing**: pytest (unit + integration), ruff check  
**Target Platform**: Windows desktop (x64 and x86 release bundles)  
**Project Type**: Desktop application  
**Performance Goals**: Complete 10-minute video analysis in under 5 minutes under representative conditions  
**Constraints**: On-demand retrieval only, no full download, retry transient retrieval up to 3 times, bounded memory streaming, keyboard-operable core flow, deterministic summary/log schemas, no warning/prompt when logging is disabled  
**Scale/Scope**: Single-user local analysis sessions, one video per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase-0 gate check:
- Principle I (Simple and Modular Architecture): PASS.
- Principle II (Readability Over Cleverness): PASS.
- Principle III (Testing for Business Logic): PASS.
- Principle IV (Minimal Dependencies): PASS.
- Principle V (No Secrets in Repository): PASS.
- Principle VI (Windows-Friendly Development): PASS.
- Principle VII (Incremental Changes and Working State): PASS.

Post-Phase-1 re-check:
- PASS. Updated artifacts remain modular, deterministic, and testable.

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
│   ├── file_selector.py
│   ├── url_input.py
│   └── progress_display.py
├── data/
│   └── models.py
└── services/
    ├── analysis_service.py
    ├── video_service.py
    ├── ocr_service.py
    ├── export_service.py
    └── logging.py

tests/
├── integration/
└── unit/
```

**Structure Decision**: Keep the existing single-project desktop layout and extend current component/service modules for quality selection, minimal summary export, and optional detailed sidecar logging.

## Complexity Tracking

No constitution violations requiring justification.
