# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a portable Windows desktop application that analyzes YouTube video frames in user-selected regions, extracts player names via OCR, and exports a simplified summary CSV (`PlayerName`, `StartTimestamp`). Context matching is recall-oriented using fuzzy substring search over normalized OCR text, boundary-clipped acceptance, and single-token extraction rules for player names. Deduplication remains normalization-key-based while exported `PlayerName` preserves the earliest accepted on-screen extracted form for each normalized group. Optional sidecar logging captures per-candidate diagnostics including raw and normalized tested strings.

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
| I. Simple and Modular Architecture | PASS | Existing `src/components`, `src/services`, `src/data` separation retained |
| II. Readability Over Cleverness | PASS | Clarified extraction/output rules are explicit and deterministic |
| III. Testing for Business Logic | PASS | Plan/task/test updates cover extraction, output-display, and schema behavior |
| IV. Minimal Dependencies | PASS | No additional dependencies required |
| V. No Secrets in Repository | PASS | No secrets introduced |
| VI. Windows-Friendly Development | PASS | `%APPDATA%` behavior, launcher scripts, and Windows packaging preserved |
| VII. Incremental Changes and Working State | PASS | Changes scoped to extraction/output behavior plus supporting docs/tests |

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
