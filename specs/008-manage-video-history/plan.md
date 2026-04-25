# Implementation Plan: Managed Video Analysis History

**Branch**: `009-prepare-spec-branch` | **Date**: 2026-04-25 | **Spec**: [specs/008-manage-video-history/spec.md](specs/008-manage-video-history/spec.md)
**Input**: Feature specification from `specs/008-manage-video-history/spec.md`

## Summary

Add a dedicated video history management flow to the web UI so repeated analyses for the same video merge into one canonical entry, reopening restores persisted analysis context, and review artifacts auto-load from the entry output folder. UI layout and interaction presentation remain Stitch-authoritative using the active SCYTcheck Stitch project and downloaded screen artifacts as the implementation reference.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (Vite) frontend  
**Primary Dependencies**: Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; frontend React stack already in `src/web/frontend`; no new third-party dependency required for planning  
**Storage**: CSV result files, sidecar review JSON (`<result>.review.json`), persistent app settings in `%APPDATA%/SCYTcheck/scytcheck_settings.json` (with local fallback), new persistent video-history index file under app data  
**Testing**: `pytest` (`tests/unit`, `tests/integration`, `tests/contract`) plus existing frontend workflow tests for run/review paths  
**Target Platform**: Windows desktop local runtime (`localhost` web UI + Python backend)
**Project Type**: Single-repo local web application (Python API + browser frontend)  
**Performance Goals**: Reopen history to review-ready state in <=5s for local result folders; list/render history actions in <=200ms for up to 500 entries  
**Constraints**: Must merge by canonical source URI/path + duration seconds; missing/malformed duration must create potential-duplicate entry; Stitch is design authority; no regression to existing analysis/review behavior  
**Scale/Scope**: Adds third "History" view, merge/reopen/delete workflows, and persistence for up to hundreds of local video entries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Simple and Modular Architecture): PASS. Extend existing `src/services` and `src/web/api`/`src/web/frontend` modules without new architectural layers.
- Principle II (Readability Over Cleverness): PASS. Deterministic merge key and explicit history/reopen contracts avoid hidden behavior.
- Principle III (Testing for Business Logic): PASS. Plan requires unit/integration/contract coverage for merge identity, potential-duplicate handling, and reopen restore behavior.
- Principle IV (Minimal Dependencies): PASS. No new dependency required; persistence can use stdlib JSON/CSV/pathlib.
- Principle V (No Secrets in Repository): PASS. Local-only metadata paths and settings; no secret inputs introduced.
- Principle VI (Windows-Friendly Development): PASS. Paths and persistence align with existing `%APPDATA%` behavior and local filesystem assumptions.
- Principle VII (Incremental Changes and Working State): PASS. Feature decomposed into persistence, API, and UI slices with independent validation.
- Principle VIII (Google Stitch as UI Design Authority): PASS. Consulted Stitch project `projects/1293475510601425942` and current screen set for layout direction.

Stitch authority evidence:
- Project consulted: `projects/1293475510601425942` (SCYTcheck Web UI)
- Screens consulted:
  - `projects/1293475510601425942/screens/f7402167a28248a180a5efdf3a46c1cc` (Analysis View)
  - `projects/1293475510601425942/screens/4352dbb3d1494ac085550568aed93e84` (Analysis Running State)
  - `projects/1293475510601425942/screens/2c0fa9c23fdd48d7a913dfd6744c3f21` (Review View)
  - `projects/1293475510601425942/screens/b28f75f678a54812994bedd7291de13c` (Scan Region Selector Overlay)
  - `projects/1293475510601425942/screens/c9dcec9785d34d23b03e296fc5b3c2c1` (Frame Thumbnail Modal Overlay)
- Downloaded planning artifacts are tracked in `specs/008-manage-video-history/stitch/` and indexed in `specs/008-manage-video-history/stitch/README.md`.

Post-design re-check: PASS. Phase 0/1 artifacts preserve modularity, explicit tests, and Stitch authority with no planned deviations.

## Project Structure

### Documentation (this feature)

```text
specs/008-manage-video-history/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── history-api.md
├── stitch/
│   ├── *.html
│   ├── *.png
│   └── README.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── services/
│   ├── analysis_service.py
│   ├── export_service.py
│   └── video_service.py
├── web/
│   ├── api/
│   │   ├── app/
│   │   └── routes/
│   └── frontend/
│       └── src/
│           ├── App.tsx
│           ├── pages/
│           ├── components/
│           ├── state/
│           └── styles/
└── data/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Keep the existing single-repo web architecture. Introduce history persistence/service logic in backend service and API route modules, then add History page/state/components in `src/web/frontend/src` with navigation updates in `src/web/frontend/src/App.tsx`.

## Phase 0: Research Output

- `research.md` resolves merge-key edge handling, persistence format, derived-review loading behavior, and Stitch consumption approach for the new History view.

## Phase 1: Design Output

- `data-model.md` defines `VideoHistoryEntry`, `AnalysisRunRecord`, `PersistedAnalysisContext`, and `DerivedReviewResultSet` with validation and state transitions.
- `contracts/history-api.md` defines local API contracts for listing, reopening, deleting, and writing merged history entries.
- `quickstart.md` defines end-to-end local verification for merge/reopen/delete and missing-duration/missing-output-folder edge behavior.

## Stitch Asset Consumption Strategy

Design authority and artifact handling:
- Stitch project `projects/1293475510601425942` remains authoritative for layout and visual structure decisions.
- Downloaded HTML/PNG artifacts under `specs/008-manage-video-history/stitch/` are treated as planning-time references and implementation baselines.

Planned frontend integration points:
- Navigation and third-view routing: `src/web/frontend/src/App.tsx`
- New page shell and history list layout derived from Stitch hierarchy: `src/web/frontend/src/pages/HistoryPage.tsx`
- Reusable history row/card actions (reopen/delete/potential-duplicate badge): `src/web/frontend/src/components/HistoryEntryRow.tsx`
- Data loading and optimistic action state: `src/web/frontend/src/state/historyStore.ts`
- Shared style token alignment and section-specific layout rules: `src/web/frontend/src/styles/app.css` and `src/web/frontend/src/styles/theme.css`

Asset-to-surface mapping for implementation:
- `analysis-view.html/png` and `analysis-running-state.html/png`: preserve Analysis page component hierarchy while adding entry points to History navigation.
- `review-view.html/png`: validate reopen target behavior and auto-load review context presentation.
- `scan-region-selector-overlay.html/png` and `frame-thumbnail-modal-overlay.html/png`: ensure modal/overlay visual language remains consistent when reused from History-triggered flows.

Deviation policy:
- If technical constraints require deviating from downloaded Stitch structure, document the rationale in implementation notes and tests before merge.

## Complexity Tracking

No constitution violations requiring justification.
