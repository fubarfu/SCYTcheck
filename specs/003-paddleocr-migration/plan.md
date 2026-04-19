# Implementation Plan: PaddleOCR Migration

**Branch**: `003-paddleocr-migration` | **Date**: 2026-04-14 | **Spec**: `specs/003-paddleocr-migration/spec.md`
**Input**: Feature specification from `/specs/003-paddleocr-migration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Replace the current Tesseract-based OCR path with a bundled PaddleOCR-based path that improves player-name recognition on compressed gameplay footage while preserving the existing SCYTcheck workflow, output schemas, saved settings safety, and fully offline portable Windows packaging. The implementation will keep region-based analysis and downstream matching behavior intact, add bundled local PaddleOCR model/runtime assets to the release, and introduce repeatable baseline-vs-migration validation on maintained reference samples.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `yt-dlp`, `numpy`, `thefuzz`, `Pillow`, `paddleocr`, `paddlepaddle` (CPU inference), Tkinter stdlib  
**Storage**: Local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to app/local directory), CSV exports, bundled local OCR model files inside release package  
**Testing**: `pytest` (unit + integration + release-bundle checks), `ruff check`  
**Target Platform**: Windows desktop portable package (primary), developer source run on Windows  
**Project Type**: Desktop application (Tkinter) with service-layer OCR/video/export pipeline  
**Performance Goals**:

- Improve player-name recognition quality versus the current Tesseract baseline on the maintained reference set
- Keep end-to-end analysis practical for normal `fps=1` gameplay workflows on CPU-only Windows systems
- Avoid workflow-breaking startup or inference delays in the packaged app

**Constraints**:

- No paid OCR services or online inference dependencies
- Fully offline portable ZIP after extraction, including bundled PaddleOCR models/runtime assets
- Preserve current region-selection, export schemas, and downstream matching behavior
- Safely migrate or ignore obsolete Tesseract-specific settings without breaking upgrades
- Keep dependency growth and packaging complexity justified and bounded

**Scale/Scope**:

- Existing single-desktop-app codebase under `src/` and `tests/`
- Supported recordings are YouTube gameplay sessions processed through selected on-screen text regions
- Release target for this feature is `x64` portable ZIP; `x86` support is deferred pending explicit PaddleOCR runtime/model feasibility validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 Gate Review (PASS):

- Principle I (Simple and Modular Architecture): PASS
  - Engine migration remains localized to OCR integration, configuration, packaging, and validation surfaces.
- Principle II (Readability Over Cleverness): PASS
  - Plan favors an adapter-style OCR service replacement and explicit packaging paths over opaque dynamic behavior.
- Principle III (Testing for Business Logic): PASS
  - Adds focused OCR baseline comparison, workflow regression, and release-bundle validation.
- Principle IV (Minimal Dependencies): PASS WITH JUSTIFICATION
  - New OCR runtime dependencies are necessary for the feature goal; scope is constrained to PaddleOCR CPU inference and bundled local assets only.
- Principle V (No Secrets in Repository): PASS
  - No credentials, tokens, or paid-service integrations are introduced.
- Principle VI (Windows-Friendly Development): PASS
  - Design centers on Windows portable packaging and local CPU inference.
- Principle VII (Incremental Changes and Working State): PASS
  - Migration is staged through adapter, packaging, and validation work with backward-compatible user workflow.

Post-Phase 1 Design Re-check (PASS):

- Design artifacts keep the project structure unchanged, isolate the OCR-engine swap behind existing service boundaries, and add explicit packaging and validation contracts.
- No constitution violations require exception handling beyond the justified dependency increase inherent to the feature.

## Project Structure

### Documentation (this feature)

```text
specs/003-paddleocr-migration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
```text
src/
├── main.py
├── config.py
├── services/
│   ├── ocr_service.py
│   ├── analysis_service.py
│   ├── export_service.py
│   ├── video_service.py
│   └── logging.py
├── data/
│   └── models.py
└── components/
  └── ...

tests/
├── unit/
│   ├── test_ocr_service.py
│   ├── test_config.py
│   └── ...
└── integration/
  ├── test_us1_workflow.py
  ├── test_release_bundle_fr010_fr013.py
  └── ...

scripts/
├── validate_ocr_baseline.py
├── download_paddleocr_models.ps1
└── release/
  └── build.ps1

build-config.spec

third_party/
├── ffmpeg/
├── tesseract/
└── paddleocr/
  └── x64/
```

**Structure Decision**: Retain the existing single-project desktop application structure. Implementation is centered on `src/services/ocr_service.py`, `src/config.py`, release packaging (`scripts/release/build.ps1`, `build-config.spec`), and targeted tests under `tests/unit` and `tests/integration`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| None | N/A | N/A |
