# Data Model: RSI Player Validation Signal

**Feature**: 014-rsi-player-validation  
**Date**: 2026-05-01

---

## New Entities

### `ValidationState` (Python Literal / TypeScript union)

Represents the current check status of a candidate spelling against the RSI citizen endpoint.

| Value | Meaning |
|-------|---------|
| `unchecked` | Validation is disabled, or this candidate was never submitted for checking |
| `checking` | Request is queued or currently in-flight |
| `found` | HTTP 200 received — profile exists |
| `not_found` | HTTP 404 received — profile does not exist |
| `failed` | Any other HTTP status, timeout (>10 s), or network error |

---

### `ValidationOutcome` (Python dataclass)

One validation result per unique normalized spelling per analysis run.

| Field | Type | Notes |
|-------|------|-------|
| `spelling` | `str` | The exact spelling submitted to the RSI endpoint (pre-normalization display form, post-normalization canonical key) |
| `state` | `ValidationState` | Current outcome |
| `checked_at` | `datetime \| None` | UTC timestamp when the HTTP response was received; `None` if still pending or unchecked |
| `source` | `"analysis_batch" \| "manual_review"` | How the check was triggered |

**Python definition** (`src/services/validation_service.py`):
```python
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

ValidationState = Literal["unchecked", "checking", "found", "not_found", "failed"]

@dataclass
class ValidationOutcome:
    spelling: str
    state: ValidationState = "unchecked"
    checked_at: datetime | None = None
    source: Literal["analysis_batch", "manual_review"] = "analysis_batch"
```

**Deduplication key**: normalized spelling = `spelling.lower().strip()` — same normalization as used in the analysis pipeline (`AnalysisService.normalize_name` trims and lowercases).

---

## Modified Entities

### `AdvancedSettings` (`src/config.py`)

**New field**:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `validation_enabled` | `bool` | `True` | User-controlled toggle; persisted in `scytcheck_settings.json` |

---

### `AnalysisRunState` (`src/web/app/analysis_adapter.py`)

**New fields** (added to `@dataclass`):

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `validation_outcomes` | `dict[str, dict] \| None` | `None` | Current snapshot of serialisable validation outcomes; updated as queue drains |
| `validation_queue_size` | `int` | `0` | Count of spellings still queued or in-flight; 0 when complete or disabled |
| `review_ready` | `bool` | `False` | True after video scan completes (even if validation still pending) |

---

### `Candidate` (TypeScript, `src/web/frontend/src/types/index.ts`)

**New optional field**:

| Field | Type | Notes |
|-------|------|-------|
| `validation_state` | `ValidationState \| undefined` | Current validation status; `undefined` = not loaded / validation disabled |

---

### `AnalysisProgress` (TypeScript, `src/web/frontend/src/types/index.ts`)

**New optional fields**:

| Field | Type | Notes |
|-------|------|-------|
| `validation_queue_size` | `number \| undefined` | Remaining validations in queue + in-flight |
| `validation_outcomes` | `Record<string, { state: ValidationState; spelling: string; checked_at: string \| null }> \| undefined` | Current outcomes keyed by normalized spelling |

---

## Persistence Schema

### `result_<n>.review.json` (sidecar, existing format extended)

New top-level key `validation_outcomes` added:

```jsonc
{
  // ... existing fields ...
  "validation_outcomes": {
    // key: normalized spelling (lowercase + stripped)
    "playername": {
      "spelling": "PlayerName",   // display form
      "state": "found",           // ValidationState
      "checked_at": "2026-05-01T12:34:56+00:00",  // null if pending/unchecked
      "source": "analysis_batch"  // or "manual_review"
    },
    "anothername": {
      "spelling": "AnotherName",
      "state": "checking",
      "checked_at": null,
      "source": "analysis_batch"
    }
  }
}
```

**Write timing**:
1. **Initial write** — after video scan completes; any already-resolved validations included; pending ones show `checking` or `unchecked`
2. **Final write** — when `ValidationService` queue drains completely; all outcomes in terminal states
3. **Manual recheck** — single outcome entry updated immediately after a `POST /api/review/candidates/{id}/validate` call resolves

---

## State Transitions

### Validation lifecycle per spelling (per run)

```
            enqueue()
[unchecked] ──────────► [checking]
                             │
               HTTP 200 ◄────┤────► HTTP 404
                  │          │           │
              [found]        │       [not_found]
                             │
               other / timeout / error
                             │
                          [failed]
```

- `unchecked` → `checking`: spelling enqueued in `ValidationService`
- `checking` → `found` | `not_found` | `failed`: HTTP request resolves
- **No transitions back** — once in a terminal state (`found`, `not_found`, `failed`), the outcome is immutable for that run
- **Manual recheck** in review can restart the cycle: any current state → `checking` → terminal

---

## Recommendation Score Integration

`RecommendationService.score_candidate()` signature extension:

```python
@staticmethod
def score_candidate(
    candidate: dict,
    recommendation_threshold: int = 70,
    validation_state: ValidationState | None = None,  # NEW
) -> dict:
    base = 50.0
    temporal = float(candidate.get("temporal_proximity") or 0.0) * 0.3
    status_bonus = 20.0 if candidate.get("status") == "confirmed" else 0.0
    # NEW: validation signal
    validation_bonus = 0.0
    if validation_state == "found":
        validation_bonus = 20.0
    elif validation_state == "not_found":
        validation_bonus = -10.0
    score = min(100.0, max(0.0, base + temporal + status_bonus + validation_bonus))
    ...
```

**Score ranges with validation**:
| Scenario | Base | Temporal (max) | Status | Validation | Max Score |
|----------|------|----------------|--------|------------|-----------|
| Found, unreviewed | 50 | +30 | 0 | +20 | **100** |
| Found, confirmed | 50 | +30 | +20 | +20 | **100** (capped) |
| Not found, unreviewed | 50 | +30 | 0 | −10 | **70** |
| Checking/failed/unchecked | 50 | +30 | 0 | 0 | **80** |
| Confirmed (no validation) | 50 | +30 | +20 | 0 | **100** |
