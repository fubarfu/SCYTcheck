# Implementation Plan: Video-Centric Review History

**Branch**: `012-from-3c6f0ff` | **Date**: 2026-04-27 | **Spec**: [specs/012-video-review-history/spec.md](specs/012-video-review-history/spec.md)
**Input**: Feature specification from `specs/012-video-review-history/spec.md`

## Summary

Reframe prior top-panel review-history behavior into a bottom-panel edit history model anchored to a per-video workspace. Each state-changing review mutation writes a full append-only snapshot into a single per-video history container, enabling deterministic restore while preserving all historical entries (older entries may be compressed). Enforce single-writer locking for each video workspace and support read-only fallback for concurrent viewers. UI structure and visual hierarchy are driven by Stitch project `projects/1293475510601425942` and newly generated 012-specific screens.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (Vite) frontend  
**Primary Dependencies**: Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; existing web stack in `src/web/frontend`  
**Storage**: CSV outputs + per-result sidecar JSON + per-video append-only history container in selected output location  
**Testing**: `pytest` (unit/integration/contract) + frontend Vitest state/component tests  
**Target Platform**: Windows desktop app serving local browser UI (`localhost`)  
**Project Type**: Web UI + local backend API enhancement  
**Performance Goals**: Restore action visible in UI <=500ms and hydrated state available <=2s for dataset sizes of 100, 500, and 1,000 history entries; history list render remains smooth with 1,000+ entries  
**Constraints**: No breaking behavior for existing results without history; no new mandatory third-party dependencies; local-first/offline operation  
**Scale/Scope**: One feature slice across review UI, session/history persistence, and review mutation pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Simple and Modular Architecture): PASS. Reuses existing review routes/services and extends sidecar/history handling incrementally.
- Principle II (Readability Over Cleverness): PASS. Explicit snapshot and lock semantics documented in model and API contracts.
- Principle III (Testing for Business Logic): PASS. Adds required tests for snapshot creation triggers, restore determinism, and lock/read-only behavior.
- Principle IV (Minimal Dependencies): PASS. No required new dependency introduced.
- Principle V (No Secrets in Repository): PASS. File-based local data only.
- Principle VI (Windows-Friendly Development): PASS. Preserves current Windows-first runtime and scripts.
- Principle VII (Incremental Changes and Working State): PASS. Change surface decomposes cleanly by persistence, API, and UI slices.
- Principle VIII (Google Stitch as UI Design Authority): PASS. Active Stitch project/design system consulted and 012 screens generated/downloaded.

Stitch authority verification:
- Stitch project: `projects/1293475510601425942`
- Design system: `assets/6844205393644582333` (`SCYTcheck Dark`)
- 012 generated screens:
  - `projects/1293475510601425942/screens/58b4fe5ef0c14e6ead4a05b7128c76e1` (Review - Edit History Update)
  - `projects/1293475510601425942/screens/bf9df208fb654424b42f496d79def82b` (Review - Restored Snapshot State)
  - `projects/1293475510601425942/screens/866f61b774804cccaea05150abdbb421` (Review View - Read-Only)
- Downloaded artifacts: `specs/012-video-review-history/stitch/*.html` and `specs/012-video-review-history/stitch/*.png`

Deliberate design deviations from Stitch: None currently planned.

## Project Structure

### Documentation (this feature)

```text
specs/012-video-review-history/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── video-review-history-api.md
├── stitch/
│   ├── README.md
│   ├── review-edit-history-update.html
│   ├── review-edit-history-update.png
│   ├── review-restored-snapshot-state.html
│   ├── review-restored-snapshot-state.png
│   ├── review-read-only-lock-state.html
│   └── review-read-only-lock-state.png
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── web/
│   ├── frontend/
│   │   └── src/
│   │       ├── pages/
│   │       │   └── ReviewPage.tsx                    # ENHANCED
│   │       ├── components/
│   │       │   ├── EditHistoryPanel.tsx              # NEW
│   │       │   └── ReviewLockBanner.tsx              # NEW
│   │       └── state/
│   │           └── reviewStore.ts                    # ENHANCED
│   ├── api/
│   │   ├── routes/
│   │   │   ├── review_sessions.py                    # ENHANCED
│   │   │   ├── review_actions.py                     # ENHANCED
│   │   │   └── review_history.py                     # NEW/ENHANCED route surface
│   │   └── schemas.py                                # ENHANCED
│   └── app/
│       ├── review_sidecar_store.py                   # ENHANCED
│       ├── review_history_store.py                   # NEW
│       ├── review_lock_service.py                    # NEW
│       └── review_mutation_service.py                # ENHANCED
└── [existing structure]

tests/
├── contract/
│   └── test_video_review_history_api_012.py          # NEW
├── unit/
│   ├── test_review_history_snapshots_012.py          # NEW
│   ├── test_review_history_restore_012.py            # NEW
│   └── test_review_lock_behavior_012.py              # NEW
└── integration/
    ├── test_review_history_panel_flow_012.py         # NEW
    └── test_review_history_readonly_lock_012.py      # NEW
```

**Structure Decision**: Extend existing web review architecture in place (`src/web/frontend`, `src/web/api`, `src/web/app`) and avoid any parallel service stack.

## Phase 0: Research (COMPLETE)

Phase 0 resolves snapshot model, lock behavior, snapshot trigger boundaries, retention/compression strategy, and folder identity strategy. See [research.md](research.md).

## Phase 1: Design and Contracts (COMPLETE)

- Data model captured in [data-model.md](data-model.md)
- API contract captured in [contracts/video-review-history-api.md](contracts/video-review-history-api.md)
- Developer validation workflow captured in [quickstart.md](quickstart.md)
- Stitch-generated UI prototypes downloaded and indexed in [stitch/README.md](stitch/README.md)

Phase 1 constitution re-check: PASS (all principles remain compliant).

## Complexity Tracking

No constitution violations requiring justification.
