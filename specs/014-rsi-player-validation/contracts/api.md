# API Contracts: RSI Player Validation Signal

**Feature**: 014-rsi-player-validation  
**Date**: 2026-05-01  
**Format**: HTTP REST (existing router pattern in `src/web/api/router.py`)

---

## Modified Contracts

### `POST /api/analysis/start`

**Change**: Accept optional `validation_enabled` in request body.

**Request body** (extension only — all existing fields unchanged):
```jsonc
{
  // ... existing fields ...
  "validation_enabled": true   // optional; default true if omitted
}
```

**Response** (202, unchanged structure — no change to response):
```jsonc
{
  "run_id": "run_abc123",
  "message": "...",
  "project_status": "creating|merging",
  "video_id": "..."
}
```

---

### `GET /api/analysis/progress/{run_id}`

**Change**: Response extended with three new optional fields.

**Response** (200):
```jsonc
{
  "status": "in_progress|completed|failed|idle",
  "progress_percent": 72,
  "message": "Scanning...",
  "review_ready": true,                   // NEW — true when scan done, even if validation pending
  "validation_queue_size": 3,             // NEW — remaining validations; 0 = all done or disabled
  "validation_outcomes": {                // NEW — current snapshot; null if disabled
    "playername": {
      "spelling": "PlayerName",
      "state": "found",
      "checked_at": "2026-05-01T12:34:56+00:00"
    },
    "anothername": {
      "spelling": "AnotherName",
      "state": "checking",
      "checked_at": null
    }
  },
  // ... all existing fields preserved ...
}
```

**Notes**:
- `review_ready` replaces ad-hoc polling for sidecar availability; frontend navigates to review when this is `true`
- `validation_outcomes` is keyed by normalized spelling (lowercase + stripped)
- `validation_queue_size > 0` with `review_ready: true` signals the review page to continue polling for live updates

---

## New Contracts

### `POST /api/review/candidates/{candidate_id}/validate`

Trigger an immediate, synchronous single-candidate validation check.

**Path parameter**:
- `candidate_id` — the candidate's ID (from the review context)

**Request body**:
```jsonc
{
  "video_id": "sha256_...",   // required; identifies the workspace containing the sidecar
  "spelling": "PlayerName"   // required; the current displayed spelling to validate (from the client UI, not the sidecar). This is the authoritative source for the check and what gets persisted.
}
```

**Response** (200 — check completed):
```jsonc
{
  "candidate_id": "cand-playername",
  "spelling": "PlayerName",
  "normalized_spelling": "playername",
  "state": "found",            // ValidationState
  "checked_at": "2026-05-01T12:34:56+00:00"
}
```

**Response** (200 — check completed but failed):
```jsonc
{
  "candidate_id": "cand-playername",
  "spelling": "PlayerName",
  "normalized_spelling": "playername",
  "state": "failed",
  "checked_at": "2026-05-01T12:34:57+00:00"
}
```
> Note: HTTP 200 is returned even when the RSI check itself fails (state = "failed"). The endpoint only returns 4xx/5xx if the request is invalid or the workspace cannot be resolved.

**Error responses**:

| Status | Error key | Condition |
|--------|-----------|-----------|
| 400 | `validation_error` | `video_id` or `spelling` missing or malformed, workspace not found, candidate not found in sidecar |
| 409 | `conflict` | Another validation for this candidate is already in-flight (future guard) |

**Handler**: `ReviewActionsHandler.post_validate_candidate(candidate_id, payload)` in `src/web/api/routes/review_actions.py`

**Side effect**: Updates `validation_outcomes[normalized_spelling]` in the run's sidecar JSON on disk.

---

## Settings Persistence Contract

### `scytcheck_settings.json` (existing format extended)

**New key** under `advanced_settings`:
```jsonc
{
  "advanced_settings": {
    // ... existing keys ...
    "validation_enabled": true   // bool; default true if absent
  }
}
```

**Read/write**: handled by existing `load_advanced_settings()` / `save_advanced_settings()` in `src/config.py`.

---

## Frontend Service Interface

TypeScript functions to add in the API client layer:

```typescript
// Get current validation state for a live run (called during progress polling — no new HTTP call needed;
// validation_outcomes is already embedded in the progress response)

// Manual recheck for one candidate
async function postValidateCandidate(
  candidateId: string,
  videoId: string
): Promise<{
  candidate_id: string;
  spelling: string;
  normalized_spelling: string;
  state: ValidationState;
  checked_at: string | null;
}>
```
