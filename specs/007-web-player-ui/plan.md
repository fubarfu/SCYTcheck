# Implementation Plan: Web-Based Player Name Verification UI

**Branch**: `feature/007-web-based-player-ui` | **Date**: 2026-04-21 | **Spec**: [specs/007-web-player-ui/spec.md](specs/007-web-player-ui/spec.md)
**Input**: Feature specification from `specs/007-web-player-ui/spec.md`

## Summary

Deliver a full web replacement for the legacy Tkinter UI using a local Python server and browser frontend, with full analysis-control parity on the Analysis view and end-to-end candidate review workflow on the Review view. Google Stitch is used as the authoritative design source (project, design system, and screen artifacts), and all feature behavior (including persistence, grouping, undo, manual regrouping, export, and theme handling) is planned against the generated Stitch screens.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript/HTML/CSS (frontend)  
**Primary Dependencies**: `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, local HTTP API layer under `src/web/api`, browser UI assets under `src/web/frontend`  
**Storage**: CSV outputs, sidecar JSON session state (`<result>.review.json`), thumbnail/frame image files in sibling folder, existing `scytcheck_settings.json` for settings/theme  
**Testing**: `pytest` (unit/integration/contract), frontend workflow tests where applicable  
**Target Platform**: Windows desktop (primary), local browser on `localhost`  
**Project Type**: Single repository desktop-local web application (embedded local server + static frontend)  
**Performance Goals**: SC-005 actions/search response <=200ms for up to 500 candidates; SC-007 app startup to functional UI <=5s  
**Constraints**: No loss of legacy controls (FR-018 parity), immediate sidecar persistence on mutations, local-only runtime, Stitch-authoritative design, dark-first launch behavior with persisted override  
**Scale/Scope**: Two primary views (Analysis/Review), five canonical Stitch screens, up to 500 on-screen candidates and multi-session review switching

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Simple and Modular Architecture): PASS. Plan keeps existing repository structure and isolates web concerns under `src/web` plus existing services.
- Principle II (Readability Over Cleverness): PASS. Contracts and data model use explicit entities/actions and predictable mutation flows.
- Principle III (Testing for Business Logic): PASS. Requires dedicated tests for grouping, undo stack, persistence, validation gating, export, and parity-critical analysis controls.
- Principle IV (Minimal Dependencies): PASS. No new mandatory third-party dependency introduced in planning artifacts.
- Principle V (No Secrets in Repository): PASS. Local-only operation; no secret flow introduced.
- Principle VI (Windows-Friendly Development): PASS. Local browser + Python runtime remain Windows-first and compatible with existing packaging flow.
- Principle VII (Incremental Changes and Working State): PASS. Work decomposed into analysis/review/session/export/state slices with independent testability.
- Principle VIII (Google Stitch as UI Design Authority): PASS. Active Stitch project `projects/1293475510601425942`, design system asset `assets/6844205393644582333`, and generated screens are used as authoritative UI reference.

Stitch authority verification:
- Consulted Stitch project: `projects/1293475510601425942`
- Applied design system: `assets/6844205393644582333`
- Generated canonical screens:
  - `projects/1293475510601425942/screens/860c4f4ace1a440f871b8de136d04b33` (Analysis View)
  - `projects/1293475510601425942/screens/be5b3692817f4a81b652870f75c6c2ca` (Analysis Running)
  - `projects/1293475510601425942/screens/27b2ad687bd547429e2066b8447378cb` (Review View)
  - `projects/1293475510601425942/screens/86073009f5014d538492307fd9be599e` (Thumbnail Modal)
  - `projects/1293475510601425942/screens/b28f75f678a54812994bedd7291de13c` (Region Selector Modal)

Deliberate design deviations from Stitch: None at planning stage.

Post-design re-check: PASS. Research/design/contracts remain aligned with constitution and Stitch artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/007-web-player-ui/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── analysis-api.md
│   └── review-api.md
├── stitch/
│   ├── screens/
│   └── screenshots/
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── web/
│   ├── api/
│   │   └── routes/
│   ├── app/
│   └── frontend/
├── services/
├── data/
└── components/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use existing single-repo structure and current `src/web` layout for web delivery. Keep analysis/OCR/export behavior in existing backend services and expose all workflows through local API + browser frontend without introducing a split-repo architecture.

## Phase 0: Research Output

- `research.md` resolves all previously open technical decisions, including Stitch authority usage, screen scope, grouping logic, persistence strategy, thumbnail source policy, recommendation behavior, theme behavior, and schema-gating behavior.

## Phase 1: Design Output

- `data-model.md` defines core entities for sources, settings, analysis runs, candidates, groups, review sessions, undo actions, and export bundles with validation and state transitions.
- `contracts/analysis-api.md` defines Analysis view server contracts for settings, preview frame, start/progress/stop/result lifecycle.
- `contracts/review-api.md` defines Review view contracts for session load/list, thresholds, mutating actions, undo, thumbnails, and export.
- `quickstart.md` defines local run path, parity verification checks, review workflow validation, export validation, and Stitch artifact references.

Stitch artifact export path (downloaded):
- `specs/007-web-player-ui/stitch/screens/analysis-view.html`
- `specs/007-web-player-ui/stitch/screens/analysis-running.html`
- `specs/007-web-player-ui/stitch/screens/review-view.html`
- `specs/007-web-player-ui/stitch/screens/thumbnail-modal.html`
- `specs/007-web-player-ui/stitch/screens/region-selector-modal.html`
- `specs/007-web-player-ui/stitch/screenshots/analysis-view.png`
- `specs/007-web-player-ui/stitch/screenshots/analysis-running.png`
- `specs/007-web-player-ui/stitch/screenshots/review-view.png`
- `specs/007-web-player-ui/stitch/screenshots/thumbnail-modal.png`
- `specs/007-web-player-ui/stitch/screenshots/region-selector-modal.png`

## Complexity Tracking

No constitution violations requiring justification.
