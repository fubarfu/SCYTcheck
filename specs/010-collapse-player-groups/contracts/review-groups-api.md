# API Contract: Review Groups Management

**Feature**: 010-collapse-player-groups | **Contract Type**: HTTP REST API | **Version**: 1.1 | **Date**: 2026-04-26

## Overview

This contract extends the existing review API surface used by the local web runtime. It does not introduce a parallel service layer.

**Base URL**: `http://localhost:<dynamic-port>/api`  
**Authentication**: None (local desktop app)  
**Content-Type**: `application/json`

Primary implementation files:
- `src/web/api/routes/review_sessions.py`
- `src/web/api/routes/review_actions.py`
- `src/web/api/routes/review_export.py`
- `src/web/app/group_mutation_service.py`
- `src/web/app/review_sidecar_store.py`

## Behavior Rules

1. Conflict groups are expanded by default, but users may manually collapse them. Manual collapse state is persisted in sidecar JSON for the session.
2. Deselect is explicit: deselecting the currently selected candidate clears `accepted_name`, marks the group unresolved, and keeps the group expanded.
3. Completion and export are gated: export is blocked unless every group has an accepted name and accepted names are unique across groups.

## Endpoints

### 1) GET /api/review/sessions

List loaded review sessions.

**Response** (200):
```json
{
  "sessions": [
    {
      "session_id": "sess_example",
      "display_name": "result.csv",
      "csv_path": "C:/.../result.csv",
      "updated_at": "2026-04-26T10:00:00Z"
    }
  ]
}
```

### 2) POST /api/review/sessions/load

Load a review session from CSV + sidecar.

**Request**:
```json
{
  "csv_path": "C:/.../analysis_result.csv"
}
```

**Response** (200):
```json
{
  "session_id": "sess_example",
  "csv_path": "C:/.../analysis_result.csv",
  "schema_version": "1.0",
  "source_type": "local_file",
  "source_value": "C:/.../video.mp4"
}
```

### 3) GET /api/review/sessions/{session_id}

Return hydrated review payload with recomputed groups.

**Response** (200):
```json
{
  "session_id": "sess_example",
  "csv_path": "C:/.../analysis_result.csv",
  "updated_at": "2026-04-26T10:00:00Z",
  "candidates": [],
  "groups": [
    {
      "group_id": "grp_1",
      "accepted_name": "John Smith",
      "is_collapsed": true,
      "resolution_status": "RESOLVED",
      "rejected_candidate_ids": []
    }
  ]
}
```

### 4) POST /api/review/sessions/{session_id}/actions

Apply a review action and persist sidecar.

**Supported action types**:
- `confirm`
- `reject`
- `unreject`
- `deselect`
- `toggle_collapse`

Out-of-scope legacy actions remain available in the runtime for backward compatibility, but they are not part of feature 010 acceptance and are not required to satisfy 010-specific invariants.

**Request**:
```json
{
  "action_type": "confirm",
  "target_ids": ["candidate_123"],
  "payload": {
    "group_id": "grp_1"
  }
}
```

**Success Response** (200):
```json
{
  "session_id": "sess_example",
  "action_id": "act_abc123",
  "persisted": true,
  "updated_at": "2026-04-26T10:01:00Z"
}
```

**Validation Failure Response** (422):
```json
{
  "error": "validation_error",
  "message": "Accepted name already used by group grp_3",
  "validation": {
    "is_valid": false,
    "candidate_name": "Michael Jordan",
    "conflict_group_id": "grp_3",
    "hint": "Choose a different candidate in this group"
  }
}
```

**Deselect semantics**:
- Clears accepted candidate for the group.
- Sets group resolution state to unresolved.
- Forces group expanded state until a valid new selection is made.

**Toggle semantics**:
- Allowed for both resolved and unresolved groups.
- Collapse state is persisted and rehydrated in session payload.

### 5) POST /api/review/sessions/{session_id}/undo

Undo last action in history.

**Response** (200):
```json
{
  "session_id": "sess_example",
  "undone_action_id": "act_abc123",
  "remaining_undo_count": 4
}
```

### 6) POST /api/review/sessions/{session_id}/export

Export deduplicated names and occurrences, with completion gate checks.

**Gate conditions**:
- Every group has an accepted name.
- Accepted names are unique across groups.

**Success Response** (200):
```json
{
  "session_id": "sess_example",
  "deduplicated_names_csv_path": "C:/.../analysis_result.names.csv",
  "occurrences_csv_path": "C:/.../analysis_result.occurrences.csv",
  "confirmed_count": 22,
  "deduplicated_count": 10
}
```

**Gate Failure Response** (422):
```json
{
  "error": "completion_gate_failed",
  "message": "Review cannot be exported until all groups are resolved and accepted names are unique",
  "details": {
    "unresolved_group_ids": ["grp_2"],
    "duplicate_name_conflicts": [
      {
        "name": "John Smith",
        "group_ids": ["grp_1", "grp_4"]
      }
    ]
  }
}
```

## Error Model

All errors follow:

```json
{
  "error": "validation_error",
  "message": "Human-readable message",
  "details": {}
}
```

Common status codes:
- `200` success
- `400` malformed request
- `404` session/group/candidate not found
- `422` business-rule validation or completion-gate failure
- `500` unexpected server error

## Frontend Integration

- `CandidateGroupCard.tsx`: collapse/expand controls and group header state.
- `CandidateRow.tsx`: confirm/reject/unreject/deselect action dispatch.
- `ValidationFeedback.tsx`: inline success and duplicate-conflict error rendering.
- `ReviewPage.tsx` + `reviewStore.ts`: hydration, rollback, and gate failure display on export.

## Test Coverage Requirements

Contract and integration tests must cover:
1. Confirm/reject/unreject/deselect action behavior.
2. Duplicate accepted-name conflict blocking.
3. Manual collapse persistence for unresolved and resolved groups.
4. Export completion gate (unresolved and duplicate cases return 422).
5. Success export path with unique accepted names across all groups.
