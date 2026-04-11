# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a portable Windows desktop application that analyzes YouTube video frames in user-selected regions, extracts player names via OCR, and exports a simplified summary CSV (`PlayerName`, `StartTimestamp`). Context matching is recall-oriented using fuzzy substring search over normalized region text. Optional sidecar logging captures per-candidate diagnostics including both raw and normalized tested strings to support false-negative debugging. Distribution targets unsigned x64/x86 portable ZIP bundles with bundled runtime dependencies.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter` (stdlib), `numpy`, `thefuzz`, `Pillow`  
**Storage**: CSV output files plus persisted local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local file)  
**Testing**: `pytest` (unit and integration), `ruff` linting  
**Target Platform**: Windows 10+ (x64 and x86)  
**Project Type**: Desktop app (single process, GUI)  
**Performance Goals**: SC-001 (10-minute analysis under 5 minutes under representative conditions)  
**Constraints**: On-demand frame retrieval (no full pre-download), deterministic CSV schemas, optional logging without prompts when disabled, unsigned release flow supported  
**Scale/Scope**: Single local-user analysis workflow, one session at a time, videos may exceed 1 hour

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simple and Modular Architecture | PASS | Existing `src/components`, `src/services`, `src/data` layout remains intact |
| II. Readability Over Cleverness | PASS | Clarified deterministic matching/logging rules and explicit schema guarantees |
| III. Testing for Business Logic | PASS | Task plan includes FR/SC traceability and unit/integration coverage |
| IV. Minimal Dependencies | PASS | Dependencies remain unchanged and feature-justified |
| V. No Secrets in Repository | PASS | No secret-bearing services introduced |
| VI. Windows-Friendly Development | PASS | Windows launcher/build scripts and `%APPDATA%` config behavior retained |
| VII. Incremental Changes and Working State | PASS | Changes scoped to service logic plus schema/documentation updates |

**Constitution Check Result**: PASS (no unjustified violations).

**Post-Design Re-check**: PASS (design artifacts remain consistent and testable).

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
├── config.py
├── main.py
├── components/
│   ├── file_selector.py
│   ├── main_window.py
│   ├── progress_display.py
│   ├── region_selector.py
│   └── url_input.py
├── data/
│   └── models.py
└── services/
    ├── analysis_service.py
    ├── export_service.py
    ├── logging.py
    ├── ocr_service.py
    └── video_service.py

tests/
├── integration/
│   ├── test_log_schema_fr049.py
│   ├── test_output_schema_sc004_sc005.py
│   ├── test_performance_sc001.py
│   ├── test_release_bundle_fr010_fr013.py
│   ├── test_release_signing_fr014.py
│   ├── test_us1_workflow.py
│   └── test_us2_settings_workflow.py
└── unit/
    ├── test_analysis_service.py
    ├── test_config.py
    ├── test_export_service.py
    ├── test_file_selector.py
    ├── test_main.py
    ├── test_main_window.py
    ├── test_models.py
    ├── test_ocr_service.py
    ├── test_region_selector.py
    └── test_video_service.py
```

**Structure Decision**: Single-project desktop architecture with domain/service/UI separation; no additional project roots required.

## Complexity Tracking

No constitution violations requiring complexity exemptions.
