# Implementation Plan: Optimize Analysis Hotpaths

**Branch**: `feature/008-improve-analysis-speed` | **Date**: 2026-04-18 | **Spec**: [specs/006-optimize-analysis-hotpaths/spec.md](specs/006-optimize-analysis-hotpaths/spec.md)
**Input**: Feature specification from `specs/006-optimize-analysis-hotpaths/spec.md`

## Summary

Implement and validate three analysis hotpath optimizations while preserving strict behavioral parity: OpenCV-native gating math, single grayscale conversion reuse per sampled frame, and precompiled normalization regex. Add lightweight per-stage timing output (decode, gating, OCR, post-processing) that is emitted only when detailed logging is enabled, with instrumentation overhead constrained to <=2% on the representative benchmark suite.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, `tkinter` (stdlib)  
**Storage**: CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback local) + optional sidecar CSV  
**Testing**: `pytest` (unit + integration + performance)  
**Target Platform**: Windows desktop (primary), cross-platform-safe Python code  
**Project Type**: Desktop application (Tkinter)  
**Performance Goals**: SC-001 >=15% total runtime improvement, SC-005 >=20% gating hotpath improvement, SC-013 timing overhead <=2%  
**Constraints**: No public API breaks, no behavioral drift, no OCR model/tolerance/sampling redesign, timing output only under detailed logging  
**Scale/Scope**: Analysis loop over full video timeline with multi-region frame sampling and OCR-heavy workloads

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Simple and Modular Architecture): PASS. Changes are isolated to existing services and models.
- Principle II (Readability Over Cleverness): PASS. Straightforward instrumentation and metric aggregation; no metaprogramming.
- Principle III (Testing for Business Logic): PASS. Unit/integration/performance coverage required for parity and timing-overhead constraints.
- Principle IV (Minimal Dependencies): PASS. No new third-party dependency required.
- Principle V (No Secrets in Repository): PASS. No secret handling changes.
- Principle VI (Windows-Friendly Development): PASS. Uses existing Python/pytest/PowerShell workflow.
- Principle VII (Incremental Changes and Working State): PASS. Feature staged with parity gates and rollback plan.

Post-design re-check: PASS. Artifacts preserve modularity, explicit contracts, and testability.

## Project Structure

### Documentation (this feature)

```text
specs/006-optimize-analysis-hotpaths/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── timing-output-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── components/
├── data/
└── services/

tests/
├── fixtures/
├── integration/
└── unit/

scripts/
```

**Structure Decision**: Use existing single-project desktop structure. Implement instrumentation inside `src/services/analysis_service.py` and surface summaries through existing logging/export and UI status paths without introducing new modules unless necessary.

## Phase 0: Research Output

- `research.md` resolves implementation choices for cv2 gating math parity, grayscale reuse, precompiled regex semantics, per-stage timing boundaries, and <=2% overhead measurement strategy.

## Phase 1: Design Output

- `data-model.md` defines runtime metrics entities and invariants, including `TimingBreakdown` and `AnalysisRuntimeMetrics`.
- `contracts/timing-output-contract.md` defines when timing is emitted, required fields, formatting, and backward-compatibility behavior.
- `quickstart.md` defines enablement flow, validation commands, and expected timing output behavior under logging-enabled/disabled modes.

## Complexity Tracking

No constitution violations requiring justification.
