# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-youtube-text-analyzer/spec.md`

## Summary

Build a portable Windows desktop app (tkinter) that accepts a YouTube URL, lets users draw one or more rectangular regions on a live video frame preview, then streams frames on-demand via yt-dlp + OpenCV to extract player names via Tesseract OCR. Extracted names are matched against configurable context patterns using **fuzzy substring search** on line-break-free normalized text (default similarity threshold 0.75), deduplicated by normalized name, merged into appearance events (default gap 1.0 s), and written to a fixed-schema CSV. An optional sidecar log CSV captures per-candidate audit rows. The app is distributed as a portable unsigned ZIP (x64 + x86) bundling FFmpeg and Tesseract language data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter` (stdlib), `numpy`, `thefuzz` (fuzzy substring matching), `Pillow`  
**Storage**: CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local file)  
**Testing**: `pytest` (unit + integration)  
**Target Platform**: Windows 10+ (x64 and x86 portable bundles)  
**Project Type**: Desktop app (single-process, no server)  
**Performance Goals**: 10-minute video analyzed in under 5 minutes from analysis start to CSV write (SC-001)  
**Constraints**: No full-video download; stream frames on-demand; no code-signing required; no external install by user  
**Scale/Scope**: Single-user local tool; one analysis session at a time; videos up to 1+ hour supported

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simple and Modular Architecture | PASS | Flat `src/` with `services/`, `components/`, `data/` — no nested layers or frameworks |
| II. Readability Over Cleverness | PASS | Services have single responsibilities; fuzzy matching uses a well-known library (`thefuzz`) |
| III. Testing for Business Logic | PASS | All services (OCR, analysis, export, video) covered by unit + integration tests |
| IV. Minimal Dependencies | PASS | 6–7 runtime libraries; all directly required by stated features |
| V. No Secrets in Repository | PASS | No API keys or credentials; YouTube access is anonymous public streaming |
| VI. Windows-Friendly Development | PASS | tkinter stdlib, Windows path handling, `%APPDATA%` config fallback |
| VII. Incremental Changes and Working State | PASS | Each service is independently testable; analysis pipeline stages are separable |

**Constitution Check Result**: All gates PASS. No violations to justify.

**Post-Design Re-check**: PASS — data model entities are small, focused, and directly map to spec requirements without added abstractions.

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-text-analyzer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── ocr_service.md
│   └── video_streaming.md
└── tasks.md             # Phase 2 output (/speckit.tasks — not created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py                        # Settings load/save, APPDATA path resolution
├── main.py                          # App entry point
├── components/
│   ├── __init__.py
│   ├── file_selector.py             # Output folder selection widget
│   ├── main_window.py               # Primary workflow UI
│   ├── progress_display.py          # Analysis progress feedback
│   ├── region_selector.py           # Foreground region-drawing popup
│   └── url_input.py                 # URL entry + two-stage validation
├── data/
│   ├── __init__.py
│   └── models.py                    # VideoAnalysis, TextDetection, PlayerSummary, ContextPattern, etc.
└── services/
    ├── __init__.py
    ├── analysis_service.py          # Frame loop, OCR dispatch, fuzzy-substring matching, event merging
    ├── export_service.py            # Summary CSV + sidecar log CSV writing
    ├── logging.py                   # Internal diagnostic logging (not user-facing log CSV)
    ├── ocr_service.py               # Tesseract OCR wrapper, region crop, normalization
    └── video_service.py             # yt-dlp stream resolution, OpenCV frame seek, quality fallback

tests/
├── conftest.py
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

**Structure Decision**: Single-project layout under `src/`. Components (UI), services (business logic), and data (models) are cleanly separated. No additional project roots needed.
