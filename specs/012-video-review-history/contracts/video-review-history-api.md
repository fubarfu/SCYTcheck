# API Contract: Video Review History

**Feature**: 012-video-review-history | **Contract Type**: HTTP REST API | **Date**: 2026-04-27

## Overview

This contract extends the local review API to support per-video append-only snapshot history, deterministic restore, and single-writer lock behavior.

Base URL:
- `http://localhost:<dynamic-port>/api`

Auth model:
- Local desktop runtime (no external auth).

## Behavioral Guarantees

1. History entries are append-only full snapshots.
2. Restore uses selected entry snapshot directly (no delta replay required).
3. Only one writer session can mutate a workspace at a time.
4. Read-only sessions can inspect history and restore preview state but cannot mutate.

## Endpoints

### 1) GET /api/review/workspaces/{video_id}

Load workspace metadata and lock state.

Response `200`:
```json
{
  "video_id": "vid_6f2c...",
  "display_title": "Match Replay 27 Apr",
  "workspace_path": "C:/.../output/vid_6f2c...",
  "lock": {
    "mode": "writer",
    "owner_session_id": "sess_abc",
    "is_current_session_owner": false
  }
}
```

### 2) GET /api/review/workspaces/{video_id}/history

Return ordered history entry metadata for timeline panel.

Query params:
- `limit` (optional)
- `cursor` (optional)

Response `200`:
```json
{
  "video_id": "vid_6f2c...",
  "entries": [
    {
      "entry_id": "h_00124",
      "created_at": "2026-04-27T14:35:00Z",
      "group_count": 120,
      "resolved_count": 47,
      "unresolved_count": 73,
      "trigger_type": "confirm",
      "compressed": false
    }
  ],
  "next_cursor": null
}
```

### 3) GET /api/review/workspaces/{video_id}/history/{entry_id}

Return full snapshot payload for selected entry.

Response `200`:
```json
{
  "entry_id": "h_00124",
  "created_at": "2026-04-27T14:35:00Z",
  "snapshot": {
    "group_count": 120,
    "resolved_count": 47,
    "unresolved_count": 73,
    "groups": []
  }
}
```

### 4) POST /api/review/workspaces/{video_id}/history/{entry_id}/restore

Restore selected snapshot into active state.

Request:
```json
{
  "session_id": "sess_xyz",
  "create_restore_snapshot": true
}
```

Success response `200`:
```json
{
  "video_id": "vid_6f2c...",
  "restored_entry_id": "h_00124",
  "created_restore_entry_id": "h_00125",
  "status": "restored"
}
```

Error responses:
- `409` when workspace lock prevents mutation by current session.
- `404` when entry does not exist.

### 5) POST /api/review/workspaces/{video_id}/actions

Apply state-changing review mutation and append a new snapshot entry.

Request:
```json
{
  "session_id": "sess_xyz",
  "action_type": "confirm",
  "payload": {
    "group_id": "grp_1",
    "candidate_id": "cand_3"
  }
}
```

Success response `200`:
```json
{
  "video_id": "vid_6f2c...",
  "action_id": "act_991",
  "history_entry_id": "h_00126",
  "persisted": true
}
```

Conflict response `409`:
```json
{
  "error": "workspace_locked",
  "message": "Read-only: another editor is actively writing this video",
  "lock": {
    "owner_session_id": "sess_owner"
  }
}
```

### 6) GET /api/review/workspaces/{video_id}/lock

Inspect lock state for UI banner logic.

Response `200`:
```json
{
  "video_id": "vid_6f2c...",
  "mode": "writer",
  "owner_session_id": "sess_owner",
  "is_current_session_owner": false,
  "readonly": true
}
```

## Error Model

Common errors:
- `400` malformed request
- `404` workspace or history entry not found
- `409` lock conflict
- `422` validation failure
- `500` unexpected runtime failure

Error shape:
```json
{
  "error": "workspace_locked",
  "message": "Human-readable explanation",
  "details": {}
}
```

## Contract Test Requirements

Required coverage:
1. Append-only entry creation for state-changing actions.
2. No entry creation for non-state-changing UI interactions.
3. Deterministic restore of selected entry snapshot.
4. `409 workspace_locked` behavior for non-owner mutation attempts.
5. Read-only session can still fetch history and entry payloads.