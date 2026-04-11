# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: 2026-04-11 | **Spec**: `specs/001-youtube-text-analyzer/spec.md`
**Input**: Feature specification from `specs/001-youtube-text-analyzer/spec.md`

## Summary

Deliver a Windows desktop analyzer that processes YouTube video frames on-demand, extracts player names from user-defined regions using fuzzy context matching, and exports a minimal deduplicated CSV (`PlayerName`, `StartTimestamp`). The implementation prioritizes recall for context-matched names, includes optional detailed logging, and produces portable x64/x86 ZIP bundles without requiring signing certificates (optional signing remains supported when available).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter`, `numpy`  
**Storage**: CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json` fallback to local file)  
**Testing**: `pytest` for unit/integration; `ruff` for lint checks  
**Target Platform**: Windows desktop (x64 and x86 release bundles)  
**Project Type**: Desktop application  
**Performance Goals**: SC-001: 10-minute video analyzed in under 5 minutes under representative conditions  
**Constraints**: On-demand retrieval only (no full pre-download), no automatic quality downgrade, stream processing memory behavior, deterministic CSV schemas, packaging must not require signing certificate  
**Scale/Scope**: Single-user local analysis sessions for game-session videos; multiple regions per run; videos may exceed 1 hour

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Simple and Modular Architecture**: PASS. Changes remain in existing `services`, `components`, and `data` modules.
- **II. Readability Over Cleverness**: PASS. Deterministic matching and export rules are explicit and test-backed.
- **III. Testing for Business Logic**: PASS. Existing task set includes unit and integration coverage for OCR, aggregation, export, and packaging behavior.
- **IV. Minimal Dependencies**: PASS. Reuses existing stack; no additional runtime dependencies required.
- **V. No Secrets in Repository**: PASS. Optional signing uses external certificate path/password; no secrets committed.
- **VI. Windows-Friendly Development**: PASS. PowerShell scripts and portable bundles target Windows.
- **VII. Incremental Changes and Working State**: PASS. Clarifications and artifacts updated incrementally.

Post-design re-check: PASS. Phase 1 artifacts stay aligned with all seven principles.

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
├── components/
├── data/
├── services/
├── config.py
└── main.py

tests/
├── integration/
└── unit/

scripts/
└── release/
```

**Structure Decision**: Keep the existing single-project desktop layout. Service-layer behavior changes (OCR matching, aggregation, export/logging, video retrieval) remain under `src/services`, UI behavior under `src/components`, and release behavior under `scripts/release`.

## Phase 0: Research Output

`research.md` captures resolved technical decisions for:
- fuzzy context matching and OCR normalization
- boundary-clipped context acceptance rule
- optional logging schema and timestamp contracts
- unsigned-by-default portable packaging with optional signing step

## Phase 1: Design Output

- `data-model.md` defines entities, validation rules, and flow updates for fuzzy matching and optional signing-independent release behavior.
- `contracts/ocr_service.md` and `contracts/video_streaming.md` define service interfaces and guarantees aligned with current FR set.
- `quickstart.md` documents run/build/release flow, including unsigned release as default and optional signing.

## Complexity Tracking

No constitution violations requiring justification.
