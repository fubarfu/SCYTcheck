# Implementation Plan: Improve Text Analysis

**Branch**: `007-improve-analysis-robustness` | **Date**: 2026-04-15 | **Spec**: `specs/005-improve-text-analysis/spec.md`
**Input**: Feature specification from `specs/005-improve-text-analysis/spec.md`

## Summary

Improve text analysis reliability and throughput by switching multiline context matching to a joined-region-text-only path, adding precision guardrails (nearest bounded span max 6 tokens + token validity checks), exposing a global fuzzy tolerance control, and enforcing frame-change gating with run-time counters and optional detailed sidecar records.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `tkinter` (stdlib)  
**Storage**: CSV outputs + local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback local)  
**Testing**: `pytest` + integration/performance suites  
**Target Platform**: Windows desktop local execution (cross-platform-compatible Python)  
**Project Type**: Single-project desktop application  
**Performance Goals**: SC-003 runtime reduction >=30% with gating; SC-005 throughput improvement >=15% when detailed logging off  
**Quality Goals**: SC-001 multiline extraction >=95% recall; SC-002 relaxed tolerance true-positive improvement >=20%; SC-004 gated vs non-gated accepted-detection variance <=1%  
**Constraints**: Preserve baseline strict behavior by default (`tolerance=0.75`), keep gated vs non-gated variance <=1%, joined-only matching path (no per-line matching)  
**Scale/Scope**: Long videos (up to hours), multiple regions, sampled processing (for example 1 fps) with per-frame-region gating decisions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate Check

- **I. Simple and Modular Architecture**: PASS  
  Keep changes scoped to `OCRService`, `AnalysisService`, `config`, and UI settings wiring.
- **II. Readability Over Cleverness**: PASS  
  Use explicit joined-text flow and deterministic guardrails rather than heuristic branching.
- **III. Testing for Business Logic**: PASS  
  Add/update unit + integration + performance coverage for joined-only matching and gating behavior.
- **IV. Minimal Dependencies**: PASS  
  Reuse existing dependencies; add no new third-party packages.
- **V. No Secrets in Repository**: PASS  
  No secrets introduced; unchanged.
- **VI. Windows-Friendly Development**: PASS  
  Preserve PowerShell/run scripts and local desktop workflow.
- **VII. Incremental Changes and Working State**: PASS  
  Implement in small service-layer steps with regression tests.

### Post-Phase 1 Design Re-Check

All principles remain PASS. No justified violations required.

## Project Structure

### Documentation (this feature)

```text
specs/005-improve-text-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── ocr_normalization.md
│   ├── ocr_tolerance.md
│   └── analysis_gating.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── config.py
├── main.py
├── components/
├── data/
└── services/

tests/
├── integration/
└── unit/
```

**Structure Decision**: Use existing single-project layout under `src/` and `tests/`; no structural refactor required.

## Complexity Tracking

No constitution violations requiring justification.
