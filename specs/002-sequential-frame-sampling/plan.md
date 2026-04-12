# Implementation Plan: Sequential Video Frame Decode Sampling Optimization

**Branch**: `002-sequential-frame-sampling` | **Date**: 2026-04-12 | **Spec**: `specs/002-sequential-frame-sampling/spec.md`
**Input**: Feature specification from `/specs/002-sequential-frame-sampling/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Replace per-sample random frame seeking in `VideoService.iterate_frames_with_timestamps` with sequential decode and sample filtering while preserving timestamp fidelity, frame selection determinism, and OCR output parity for long game-session videos (15 minutes to 4+ hours). Add guarded runtime fallback to legacy seek-based iteration for decode failures or severe startup underperformance, with debug observability for verification.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: `opencv-python`, `yt-dlp`, `numpy`, `pytesseract`, stdlib logging  
**Storage**: N/A (in-memory iteration; CSV artifacts handled by existing export service)  
**Testing**: `pytest` (unit + integration + performance)  
**Target Platform**: Windows desktop (primary), cross-platform Python runtime supported by OpenCV/yt-dlp
**Project Type**: Desktop application (Tkinter) with service-layer pipeline  
**Performance Goals**: 
- >=50% faster frame iteration for 1-hour videos at `fps=1`
- Stable performance scaling through 2-hour videos
- No timestamp drift (0 ms deviation from baseline)
**Constraints**: 
- Preserve existing method signature and behavior contracts
- Maintain OCR result parity and frame count variance within +-1 frame
- Preserve fail-fast behavior on read errors unless guarded fallback is triggered
- Keep memory RSS stable within +-10% checkpoints across 2-hour runs
**Scale/Scope**: 
- Video durations: 15 minutes to 4+ hours
- Target codecs/containers for validation: H.264/MP4 and VP9/WebM
- Change scope limited to frame iteration strategy and related test instrumentation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-Phase 0 Gate Review (PASS):

- Principle I (Simple and Modular Architecture): PASS
  - Change localized to `src/services/video_service.py` with isolated fallback path.
- Principle II (Readability Over Cleverness): PASS
  - Sequential decode loop with explicit sampling math and minimal branching.
- Principle III (Testing for Business Logic): PASS
  - Add/extend unit, integration, and performance assertions for timestamps, parity, fallback, and memory behavior.
- Principle IV (Minimal Dependencies): PASS
  - No new runtime dependencies required; optional measurement tooling remains test/dev scope.
- Principle V (No Secrets in Repository): PASS
  - No secrets introduced.
- Principle VI (Windows-Friendly Development): PASS
  - Uses existing OpenCV/yt-dlp path; no OS-specific changes beyond current baseline.
- Principle VII (Incremental Changes and Working State): PASS
  - Small, contained implementation with backward-compatible fallback.

Post-Phase 1 Design Re-check (PASS):

- Design artifacts preserve single-service responsibility, backward compatibility, and explicit test gates.
- Contracts and quickstart define deterministic verification flow and rollback-safe behavior.

## Project Structure

### Documentation (this feature)

```text
specs/002-sequential-frame-sampling/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── main.py
├── config.py
├── services/
│   ├── video_service.py
│   ├── analysis_service.py
│   ├── ocr_service.py
│   └── export_service.py
├── data/
│   └── models.py
└── components/
  └── ...

tests/
├── unit/
│   ├── test_video_service.py
│   └── ...
└── integration/
  ├── test_us1_workflow.py
  └── test_performance_sc001.py
```

**Structure Decision**: Single-project desktop application structure retained. Implementation is constrained to service-layer frame iteration (`src/services/video_service.py`) plus targeted tests under `tests/unit` and `tests/integration`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
