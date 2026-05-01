# Quickstart: RSI Player Validation Signal

**Feature**: 014-rsi-player-validation  
**Branch**: `014-add-rsi-player-validation`

---

## What This Feature Adds

- **During analysis**: each unique candidate spelling is validated against `https://robertsspaceindustries.com/en/citizens/<PlayerName>` concurrently with video scanning (rate-limited to 1 req/sec; 10-sec timeout per request)
- **In review**: each candidate card shows a validation state icon (found / not found / checking / failed / unchecked); reviewers can trigger a one-off recheck
- **In analysis settings**: a toggle to disable external validation entirely
- **Recommendation scoring**: found +20 pts, not-found −10 pts

---

## Running Locally

```powershell
# Standard dev server start (no change needed):
.\run_app.ps1
```

Validation runs automatically when the app is started and a new analysis is launched with "Validate players" enabled (default: on).

---

## Key Files Added / Modified

| Path | Change |
|------|--------|
| `src/services/validation_service.py` | **NEW** — `ValidationService`, `ValidationOutcome`, `ValidationState` |
| `src/config.py` | **MODIFY** — `AdvancedSettings.validation_enabled: bool = True` |
| `src/services/analysis_service.py` | **MODIFY** — `analyze()` adds `on_candidate_discovered` callback |
| `src/web/app/analysis_adapter.py` | **MODIFY** — `AnalysisRunState` extended with `validation_outcomes`, `validation_queue_size`, `review_ready` |
| `src/web/app/recommendation_service.py` | **MODIFY** — `score_candidate()` accepts optional `validation_state` |
| `src/web/api/routes/analysis.py` | **MODIFY** — wire `ValidationService` into `work()` |
| `src/web/api/routes/review_actions.py` | **MODIFY** — add `POST /api/review/candidates/{id}/validate` |
| `src/web/api/router.py` | **MODIFY** — register new recheck route |
| `src/web/frontend/src/types/index.ts` | **MODIFY** — `ValidationState` type, extend `Candidate`, `AnalysisProgress` |
| `src/web/frontend/src/components/CandidateRow.tsx` | **MODIFY** — validation icon + recheck action |
| `src/web/frontend/src/components/AnalysisSettingsPanel.tsx` | **MODIFY** — validation toggle |
| `src/web/frontend/src/pages/AnalysisPage.tsx` | **MODIFY** — `review_ready` handling, validation progress |
| `src/web/frontend/src/pages/ReviewPage.tsx` | **MODIFY** — live validation outcome polling |

---

## Running Tests

```powershell
cd src
pytest tests/unit/test_validation_service.py -v
pytest tests/unit/test_recommendation_service.py -v
pytest tests/integration/test_validation_api.py -v
```

All three test files are new/modified as part of this feature.

---

## Disabling Validation

In the Analysis page → Settings panel → toggle "Validate player names" off.

When disabled:
- Zero external HTTP requests are made during analysis
- All candidate cards show `unchecked` state (neutral icon or no icon)
- Recommendation scores are unaffected by validation signal (treated as 0)

---

## Validation Icon Reference

| State | Icon (Material Symbols) | Meaning |
|-------|------------------------|---------|
| `found` | `check_circle` (green) | Profile confirmed on RSI |
| `not_found` | `person_off` (amber) | No profile found |
| `checking` | `progress_activity` (grey, animated) | Request in-flight or queued |
| `failed` | `error_outline` (red) | Timeout, network error, or unexpected status |
| `unchecked` | (none / neutral) | Disabled or not yet run |

> **Note**: Icon visuals and exact placement are governed by the Google Stitch design for feature 014. Consult and update the Stitch project before implementing frontend changes.

---

## Architecture: Concurrent Validation Flow

```
Analysis work() thread
│
├─ Creates ValidationService(enabled=True, rate=1.0, timeout=10.0)
├─ Calls vs.start()                         ← starts queue worker thread
│
├─ Calls analysis_service.analyze(
│      on_candidate_discovered=vs.enqueue   ← new spellings enqueued as discovered
│  )
│   └─ Queue worker thread: drains at 1 req/sec, writes outcomes to shared dict
│
├─ [Scan complete] ──────────────────────────────────────────────────┐
│   - Writes initial sidecar (with current validation outcomes)      │
│   - Sets adapter.review_ready = True                               │
│   - Calls vs.stop()   ← no new enqueues; queue drains remaining    │
│                                                                    │
├─ Waits for vs.wait()  ← blocks until queue worker thread exits    │
│                                                                    │
├─ Writes final sidecar (all outcomes in terminal states)           │
└─ Marks run as 100% complete                                       │
                                                                    ↓
Frontend (Review page)                               Continues polling
    ↓ sees review_ready=True                         /api/analysis/progress/{run_id}
    ↓ navigates to review                            ← validation_outcomes in response
    ↓ shows "checking" icons for pending
    ↓ updates icons live as queue drains
```
