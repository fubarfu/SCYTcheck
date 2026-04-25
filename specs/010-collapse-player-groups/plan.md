# Implementation Plan: Collapsable Review Groups with Player Name Management

**Branch**: `010-collapse-player-groups` | **Date**: 2026-04-25 | **Spec**: [specs/010-collapse-player-groups/spec.md](specs/010-collapse-player-groups/spec.md)
**Input**: Feature specification from `specs/010-collapse-player-groups/spec.md`

## Summary

Enhance the review interface with collapsible candidate groups that automatically collapse when all candidates in a group have identical spellings (consensus reached) and expand when candidates have different spellings (issue to resolve). Implement radio-button interaction for candidate selection, visible-but-marked rejection workflow, inline validation feedback with context-aware error messages, and uniqueness constraint enforcement to prevent duplicate player names across groups. UI design is driven by Google Stitch (active project, design system, and generated screens), with all behavioral logic specified in this plan.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (Vite) frontend  
**Primary Dependencies**: Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; frontend React stack already in `src/web/frontend`  
**Storage**: CSV result files, sidecar review JSON (`<result>.review.json`), auto-save to local file system, integrated with existing export service  
**Testing**: `pytest` (unit/integration/contract), React component tests for collapse/expand and validation UI  
**Target Platform**: Windows desktop, local browser on `localhost` (continuation of 007-web-player-ui)  
**Project Type**: Web UI enhancement (React component library + backend API extensions)  
**Performance Goals**: Collapse/expand state toggle <=100ms; validation feedback <=500ms; render up to 50 groups with 1-50 candidates each  
**Constraints**: No breaking changes to existing review workflow; must integrate seamlessly with 007-web-player-ui Review view; data integrity (zero duplicate names); local-first operation  
**Scale/Scope**: Single feature enhancement within Review view; reuses existing web architecture; no new major dependencies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Principle I (Simple and Modular Architecture): PASS. Enhancement to existing web UI module; no new repository structure required.
- Principle II (Readability Over Cleverness): PASS. Collapse/expand logic and validation rules are explicit and testable.
- Principle III (Testing for Business Logic): PASS. Requires tests for consensus detection, uniqueness validation, group state transitions, and collapse state persistence.
- Principle IV (Minimal Dependencies): PASS. Uses existing tech stack; no new third-party dependencies introduced.
- Principle V (No Secrets in Repository): PASS. Local file system storage only; no secrets involved.
- Principle VI (Windows-Friendly Development): PASS. Builds on existing Windows-first 007-web-player-ui architecture.
- Principle VII (Incremental Changes and Working State): PASS. Work decomposes into UI component, validation logic, persistence, and integration slices.
- Principle VIII (Google Stitch as UI Design Authority): PASS. Will consult/extend Stitch project from 007-web-player-ui and generate/refine screens for collapsible group UI patterns.

Stitch authority verification:
- Base Stitch project (from 007): `projects/1293475510601425942`
- Base design system (from 007): `assets/6844205393644582333`
- New screens to generate:
  - Collapsible group component in expanded state (conflicting candidates)
  - Collapsible group component in collapsed state (consensus)
  - Candidate with radio button selected (success feedback)
  - Candidate selection error state (duplicate name conflict)
  - Rejected candidate visual state (marked/strikethrough)

Deliberate design deviations from Stitch: None anticipated; design will be driven by Stitch.

## Project Structure

### Documentation (this feature)

```text
specs/010-collapse-player-groups/
├── plan.md                  # This file
├── research.md              # Phase 0 output (TBD)
├── data-model.md            # Phase 1 output (TBD)
├── quickstart.md            # Phase 1 output (TBD)
├── contracts/               # Phase 1 output (TBD)
│   └── review-groups-api.md
├── stitch/                  # UI designs from Google Stitch
│   ├── screens/             # Exported screen images
│   └── design-system.md     # Stitch design system reference
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── web/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── CandidateGroupCard.tsx    # ENHANCED
│   │   │   │   ├── CandidateRow.tsx          # ENHANCED
│   │   │   │   └── ValidationFeedback.tsx    # NEW
│   │   │   └── utils/
│   │   │       ├── groupLogic.ts             # NEW
│   │   │       └── validationRules.ts        # NEW
│   │   └── tests/
│   │       └── review/                       # NEW frontend tests
│   │   └── [existing structure]
│   ├── api/
│   │   ├── routes/
│   │   │   ├── review_sessions.py            # ENHANCED
│   │   │   ├── review_actions.py             # ENHANCED
│   │   │   └── review_export.py              # ENHANCED
│   │   └── schemas.py                        # ENHANCED
│   ├── app/
│   │   ├── review_sidecar_store.py           # ENHANCED
│   │   ├── review_grouping.py                # ENHANCED
│   │   └── group_mutation_service.py         # ENHANCED
│   └── [existing structure]
├── data/
│   └── models.py                             # ENHANCED
└── [existing structure]

tests/
├── contract/
│   └── test_review_groups_api_010.py         # NEW
├── unit/
│   ├── test_review_group_foundation_010.py   # NEW
│   ├── test_review_group_mutations_010.py    # NEW
│   └── test_review_group_uniqueness_010.py   # NEW
├── integration/
│   ├── test_review_groups_consensus_flow_010.py     # NEW
│   ├── test_review_groups_conflict_flow_010.py      # NEW
│   ├── test_review_groups_validation_flow_010.py    # NEW
│   └── test_review_groups_toggle_persistence_010.py # NEW
└── [existing structure]
```

**Structure Decision**: Enhance existing `src/web/frontend`, `src/web/api/routes`, and `src/web/app` modules that already power review sessions. Reuse existing review workflow infrastructure and sidecar persistence, avoiding parallel service abstractions.

---

## Phase 0: Research (COMPLETE ✓)

**Inputs**: Feature spec, Constitution  
**Process**: Resolved all technical unknowns through architectural pattern analysis  
**Output**: [research.md](research.md)

**Key Research Findings**:
1. Consensus detection: exact string matching (vs fuzzy matching alternatives)
2. Persistence: sidecar JSON (vs CSV column, vs in-memory, vs settings file)
3. Validation: backend service + frontend feedback (vs frontend-only, vs batch validation)
4. Rejection workflow: visual marking + state tracking (vs deletion, vs modal confirmation)
5. Feedback pattern: inline contextual errors (vs toast, vs modals)
6. Data integrity: backend constraint enforcement (vs soft constraints)
7. UI state: auto-collapse on consensus + manual toggle (vs always collapsed/expanded)
8. Integration: extend existing modules (vs separate microservice)

**Constitution Re-Check** (Phase 0 Completion): All 8 principles remain PASS ✓

---

## Phase 1: Design (COMPLETE ✓)

**Inputs**: research.md, existing 007-web-player-ui architecture  
**Process**: Define data model, API contracts, integration points  
**Output**: [data-model.md](data-model.md), [contracts/review-groups-api.md](contracts/review-groups-api.md), [quickstart.md](quickstart.md)

### 1.1 Data Model (COMPLETE ✓)

**Entities**:
- `CandidateGroup`: Collection of spelling variants with consensus state
- `Candidate`: Individual spelling variant with confidence score
- `ReviewSession`: Container for all groups in a video analysis
- `ValidationResult`: Validation response with conflict details

**Key Properties**:
- Auto-consensus detection: `is_consensus_reached` property
- State persistence: sidecar JSON (`<result>.review.json`)
- Validation constraints: uniqueness, immutability during consensus
- Non-destructive rejection: `rejected_candidate_ids` array

**[Full Details](data-model.md)**

### 1.2 API Contracts (COMPLETE ✓)

**Endpoints** (existing route surface, enhanced):
1. `GET /api/review/sessions/{session_id}` - Load hydrated session state
2. `POST /api/review/sessions/{session_id}/actions` - Confirm/reject/unreject/deselect/toggle-collapse actions
3. `POST /api/review/sessions/{session_id}/undo` - Undo last action
4. `POST /api/review/sessions/{session_id}/export` - Export with completion/uniqueness gating
5. `GET /api/review/sessions` and `POST /api/review/sessions/load` - Session discovery and load

**Error Handling**: Standard HTTP codes + JSON error responses with conflict details

**Persistence**: All operations persist immediately to sidecar JSON

**[Full Details](contracts/review-groups-api.md)**

### 1.3 Development Quickstart (COMPLETE ✓)

**Sections**:
- Backend setup (Python venv, dependencies)
- Frontend setup (React, Vite dev server)
- API server (local web server under `src.main`, API mounted at `/api`)
- Unit/contract/integration test execution
- Manual validation (end-to-end workflow)
- Persistence verification (sidecar JSON, CSV immutability)
- Development checklist
- Troubleshooting guide
- Performance targets (<100ms collapse, <500ms validation)

**[Full Details](quickstart.md)**

### 1.4 UI Design (COMPLETE ✓)

**Screens Generated via Google Stitch** (3 screens):
1. **Review - Candidate Groups**: Groups in consensus (collapsed), conflict (expanded), and resolved states
2. **Review - Validation Error State**: Inline error with duplicate name conflict, context reference, hint
3. **Review - Expanded Candidate Group**: Selection with success feedback, rejected candidate (strikethrough), active candidates

**Design System**: SCYTcheck Dark (blue #3B82F6, red error #fa746f, Geist/Inter fonts)  
**Device**: Desktop 1280px (continuation of 007-web-player-ui)  
**Project**: `projects/1293475510601425942` (shared with 007)  
**Screens Generated**: 
- `projects/1293475510601425942/screens/a23aacacd8ea459b938c8b40cdcebedc`
- `projects/1293475510601425942/screens/364907151ac748b39532e40a370685ac`
- `projects/1293475510601425942/screens/73b8b2b06c2f42969899f241fdb3ef4e`

### 1.5 Integration with 007 Architecture (DOCUMENTED ✓)

**Reuse**:
- Existing `src/web/frontend` React/Vite stack
- Existing `src/web/api/routes` handlers and router wiring
- Existing `review_sidecar_store.py` persistence path (enhanced, not replaced)
- Existing CSV export artifacts with added completion-gate validation

**New Components**:
- `CandidateGroupCard.tsx` - Main group UI component (enhanced)
- `CandidateRow.tsx` - Candidate-level radio select, reject, and deselect behavior (enhanced)
- `ValidationFeedback.tsx` - Error/success display
- `group_mutation_service.py` - Backend mutation and uniqueness logic

**Constitution Re-Check** (Phase 1 Completion): All 8 principles remain PASS ✓

---

## Complexity Tracking

No violations. Feature is simple, modular, and adds no new dependencies.
