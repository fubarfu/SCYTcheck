# Quickstart: Collapsable Review Groups Development

**Feature**: 010-collapse-player-groups | **Version**: 1.1 | **Date**: 2026-04-26

## Overview

This guide validates feature 010 against the current SCYTcheck runtime architecture.

## 1. Setup

### 1.1 Python environment

```powershell
cd c:\Users\SteSt\source\SCYTcheck
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1.2 Frontend dependencies

```powershell
cd src/web/frontend
npm install
```

## 2. Run the App

The app starts from the project entrypoint and hosts the API + static frontend via the local web server.

```powershell
cd c:\Users\SteSt\source\SCYTcheck
python -m src.main
```

Expected result:
- Browser opens to `/analysis`.
- API is reachable under `/api/...`.

## 3. Run Tests

From repo root:

### 3.1 Unit tests

```powershell
pytest tests/unit/test_review_group_foundation_010.py -v
pytest tests/unit/test_review_group_mutations_010.py -v
pytest tests/unit/test_review_group_uniqueness_010.py -v
```

### 3.2 Contract tests

```powershell
pytest tests/contract/test_review_groups_api_010.py -v
```

### 3.3 Integration tests

```powershell
pytest tests/integration/test_review_groups_consensus_flow_010.py -v
pytest tests/integration/test_review_groups_conflict_flow_010.py -v
pytest tests/integration/test_review_groups_validation_flow_010.py -v
pytest tests/integration/test_review_groups_toggle_persistence_010.py -v
```

### 3.4 Frontend Vitest

```powershell
cd src/web/frontend
npm test -- tests/review/CandidateGroupCard.test.tsx
npm test -- tests/review/CandidateRow.test.tsx
npm test -- tests/review/reviewStore.test.ts
npm test -- tests/review/perfBenchmark.test.tsx
```

## 4. Manual Validation Flow

1. Open Review view and load a result CSV.
2. Verify consensus groups start collapsed.
3. Verify conflict groups start expanded.
4. Confirm a candidate and verify inline success feedback.
5. Deselect the selected candidate and verify:
   - accepted name clears,
   - group becomes unresolved,
   - group remains expanded.
6. Try selecting a duplicate accepted name across groups and verify inline error with conflict group reference.
7. Toggle collapse state manually for both resolved and unresolved groups; reload session and confirm state persistence.

## 5. Completion and Export Gate Validation

### 5.1 Export blocked for unresolved groups

- Leave at least one group without accepted name.
- Trigger export.
- Expect `422 completion_gate_failed`.

### 5.2 Export blocked for duplicate accepted names

- Force duplicate accepted name across two groups.
- Trigger export.
- Expect `422 completion_gate_failed` with duplicate conflict details.

### 5.3 Export succeeds for valid session

- Ensure every group has one accepted name and all accepted names are unique.
- Trigger export.
- Expect `200` and output files:
  - `<result>.names.csv`
  - `<result>.occurrences.csv`

## 6. Performance Checks

### SC-003 (resolve under 10s)

- Use integration test stopwatch around a scripted resolve workflow.
- Pass condition: total workflow duration for a single group is `< 10,000 ms`.

### SC-003b (validation under 500ms)

- Use perf benchmark assertions in `tests/review/perfBenchmark.test.tsx` and integration timing hooks.
- Pass condition: duplicate-validation feedback appears in `< 500 ms`.

## 7. Key Implementation Files

| File | Purpose |
| --- | --- |
| `src/web/frontend/src/components/CandidateGroupCard.tsx` | Group container and collapse UI |
| `src/web/frontend/src/components/CandidateRow.tsx` | Candidate selection/reject/deselect actions |
| `src/web/frontend/src/components/ValidationFeedback.tsx` | Inline success/error feedback |
| `src/web/frontend/src/pages/ReviewPage.tsx` | Review orchestration and export interactions |
| `src/web/frontend/src/state/reviewStore.ts` | Session state transitions |
| `src/web/api/routes/review_sessions.py` | Session load/get and payload hydration |
| `src/web/api/routes/review_actions.py` | Action endpoint for confirm/reject/deselect/toggle |
| `src/web/api/routes/review_export.py` | Completion and export gating |
| `src/web/app/group_mutation_service.py` | Business rules for mutation and uniqueness |
| `src/web/app/review_sidecar_store.py` | Sidecar JSON persistence |

## 8. Definition of Done

- All feature 010 tests pass.
- Export gate rejects unresolved or duplicate sessions.
- Deselect behavior matches FR-020 semantics.
- Timing criteria SC-003 and SC-003b are asserted in automated checks.
- Stitch alignment notes captured in `specs/010-collapse-player-groups/stitch/README.md`.
