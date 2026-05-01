# Implementation Plan: RSI Player Validation Signal

**Branch**: `014-add-rsi-player-validation` | **Date**: 2026-05-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-rsi-player-validation/spec.md`

## Summary

During analysis, each unique candidate spelling is validated against the RSI citizen profile page (`https://robertsspaceindustries.com/en/citizens/<PlayerName>`) via HTTP status check. Validation runs concurrently with video scanning using a rate-limited queue (1 req/sec, 10-sec timeout). Results influence recommendation scoring (found → +20, not-found → -10). Review page shows per-candidate validation state icons and supports manual single-candidate rechecks. Validation is user-togglable via analysis settings.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React Vite (frontend)  
**Primary Dependencies**: `opencv-python`, `paddleocr`, `yt-dlp`, `thefuzz`, `numpy`; Python stdlib `urllib.request`, `threading`, `queue` for validation; React, Vite, Material Symbols (frontend)  
**Storage**: Per-run review sidecar JSON (`result_<n>.review.json`) extended with `validation_outcomes` dict; local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`)  
**Testing**: pytest (backend), no frontend test framework currently active  
**Target Platform**: Windows desktop app (Electron-like local server + browser UI on port 8765)  
**Project Type**: Desktop application with local HTTP API + React frontend  
**Performance Goals**: Validation queue dispatches at ≤1 req/sec; each HTTP request completes within 10 sec timeout; scan throughput unaffected (validation is fully concurrent)  
**Constraints**: No new third-party HTTP library (stdlib `urllib.request`); zero cross-run result reuse; validation enabled/disabled without breaking other analysis outputs  
**Scale/Scope**: Typically 10–200 unique candidate spellings per run; 2 affected pages (Analysis, Review); ~8 affected source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Simple and modular architecture** ✅ — `ValidationService` is a single, self-contained class; it plugs into the existing analysis pipeline via a single callback. No new architectural layers or abstractions are introduced.
- **Readability over cleverness** ✅ — `urllib.request` is verbose but transparent; queue/thread logic is straightforward.
- **Testing for business logic** ✅ — Required: unit tests for `ValidationService` (queue deduplication, rate limiting, outcome mapping, timeout), `RecommendationService` extension (validation signal weighting), and the manual recheck API endpoint.
- **Minimal dependencies** ✅ — Python stdlib only (`urllib.request`, `threading`, `queue`); no new third-party library.
- **No secrets in repository** ✅ — RSI URL is a public, unauthenticated endpoint; no credentials involved.
- **Windows-friendly development** ✅ — stdlib HTTP and threading work identically on Windows.
- **Google Stitch as UI Design Authority** ✅ — Stitch screens designed in existing project "SCYTcheck Web UI" (`1293475510601425942`). Two screens added:
  - `2b3b3615129a4879ba1e0748e52aac38` — "Review - Expanded Candidate Group" with all 4 validation icon states (`found`/`not_found`/`checking`/`failed`) and per-candidate Re-check buttons.
  - `0576734766574b979811eadd1978f86c` — "Analysis View" with "Validate player names (RSI)" toggle in settings panel.
  - HTML and screenshots saved to `specs/014-rsi-player-validation/stitch/`.

## Project Structure

### Documentation (this feature)

```text
specs/014-rsi-player-validation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── stitch/              # UI design screens (Stitch project 1293475510601425942)
    ├── README.md
    ├── review-expanded-candidate-group-validation-states.html  # screen 2b3b3615129a4879ba1e0748e52aac38
    ├── review-expanded-candidate-group-validation-states.png
    ├── analysis-view-validation-toggle.html                    # screen 0576734766574b979811eadd1978f86c
    └── analysis-view-validation-toggle.png
```

### Source Code (repository root)

```text
src/
├── services/
│   └── validation_service.py       # NEW — ValidationService, ValidationOutcome, ValidationState
├── web/
│   ├── app/
│   │   ├── analysis_adapter.py     # MODIFY — add validation_outcomes & review_ready state per run
│   │   └── recommendation_service.py # MODIFY — extend score_candidate with validation signal
│   └── api/
│       ├── routes/
│       │   ├── analysis.py         # MODIFY — wire ValidationService into analysis work()
│       │   └── review_actions.py   # MODIFY — add manual recheck endpoint
│       └── router.py               # MODIFY — register new validation state & recheck routes
├── config.py                       # MODIFY — add validation_enabled to AdvancedSettings
└── data/
    └── models.py                   # MODIFY — no new model needed; ValidationOutcome lives in validation_service.py

src/web/frontend/src/
├── types/
│   └── index.ts                    # MODIFY — add ValidationState, extend Candidate and AnalysisProgress
├── components/
│   ├── CandidateRow.tsx            # MODIFY — add validation icon and recheck action
│   └── AnalysisSettingsPanel.tsx   # MODIFY — add validation_enabled toggle
├── pages/
│   ├── AnalysisPage.tsx            # MODIFY — show "View Results" on review_ready; poll validation state
│   └── ReviewPage.tsx              # MODIFY — live-update validation icons from polling
└── services/
    └── apiClient.ts (or equivalent) # MODIFY — add getValidationState(), postRecheck()

tests/
├── unit/
│   ├── test_validation_service.py  # NEW
│   └── test_recommendation_service.py # MODIFY — add validation signal tests
└── integration/
    └── test_validation_api.py      # NEW — recheck endpoint + validation state endpoint
```

**Structure Decision**: Single project layout (Option 1). The feature touches both the Python backend services layer and the React frontend component/settings layers. No new top-level directories are required; all new code slots into the existing `src/services/`, `src/web/api/routes/`, `src/web/app/`, and `src/web/frontend/src/` trees.

## Complexity Tracking

> No constitution violations identified. No entries required.
