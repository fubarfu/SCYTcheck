# Research: RSI Player Validation Signal

**Feature**: 014-rsi-player-validation  
**Date**: 2026-05-01  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## 1. HTTP Client Approach

**Decision**: Python stdlib `urllib.request`  
**Rationale**: Project has no `requests` or `httpx` in `requirements.txt` (confirmed). The Constitution requires minimal dependencies. `urllib.request` is sufficient for a simple HTTP HEAD or GET request to a known URL pattern with a 10-second timeout. `http.client` is also viable but `urllib.request` has a cleaner interface for this use case.  
**Implementation note**: Use `urllib.request.urlopen(url, timeout=10)` inside a try/except; catch `urllib.error.HTTPError` (to inspect status code), `urllib.error.URLError`, `socket.timeout`, and bare `Exception`. HTTP 200 → found; HTTP 404 → not found; all others → failed.  
**Alternatives considered**:
- `requests` — not installed; adding it for a single feature violates minimal-dependency principle
- `httpx` — same issue, plus async complexity not needed here
- `http.client` — lower level, more verbose, no benefit over `urllib.request` for this task

---

## 2. Concurrent Validation Architecture

**Decision**: Background thread + `queue.Queue` in `ValidationService`  
**Rationale**: The existing `AnalysisAdapter` uses a `threading.Thread` per run (in `start()`). The analysis `work()` function is already running in a background thread. We can spin up a second background thread (the validation queue worker) inside that same `work()` function. The queue worker drains at 1 req/sec using `time.sleep(1)` between dispatches. The main work thread and the queue worker share a `threading.Lock`-protected `dict[str, ValidationOutcome]` for results.  
**Rationale for thread-over-async**: The entire backend is synchronous (no asyncio in use anywhere). Introducing asyncio for one feature would be a significant architectural change. Threading is simple, matches existing patterns, and is safe for I/O-bound HTTP calls.  
**Implementation note**:
```python
class ValidationService:
    def start(self) -> None:
        # Starts worker thread; thread exits when stop() called + queue drained
    def enqueue(self, spelling: str) -> None:
        # Idempotent; deduplicates by normalized spelling; thread-safe
    def stop(self) -> None:
        # Signals no more new items; worker thread drains remaining then exits
    def wait(self, timeout_sec: float | None = None) -> None:
        # Block until worker thread exits (called from work() after scan completes)
    def get_outcomes(self) -> dict[str, ValidationOutcome]:
        # Thread-safe snapshot of current results
    def queue_size(self) -> int:
        # Approximate remaining count (in-queue + in-flight)
```
**Alternatives considered**:
- `concurrent.futures.ThreadPoolExecutor` — overkill; we want 1 concurrent request at a time (rate-limited); pool would require external rate limiting
- `asyncio` + `aiohttp` — architectural mismatch with synchronous backend
- Single-threaded scan-then-validate — violates spec requirement (FR-003a)

---

## 3. Live Update Mechanism (Frontend)

**Decision**: Extend analysis progress endpoint with `validation_outcomes` and `validation_queue_size`; frontend polls the existing `/api/analysis/progress/{run_id}` endpoint  
**Rationale**: The frontend already polls `/api/analysis/progress/{run_id}` during analysis to update the progress bar. Extending the progress response payload with current `validation_outcomes` and `validation_queue_size` requires no new endpoint and no new polling loop. The `AnalysisAdapter.update_progress()` call is already invoked during the work() loop. We extend `AnalysisRunState` with `validation_outcomes: dict | None` and `validation_queue_size: int`.  
**Two-phase review_ready behaviour**:
- After video scan completes (but validation still draining) → `review_ready = True`, `validation_queue_size = N > 0`
- Frontend sees `review_ready = True` → navigates to review page or enables "View Results" button
- Review page continues polling the same progress endpoint to receive live `validation_outcomes` updates
- After all validations complete → `validation_queue_size = 0`, `status = completed`  
**Implementation note**: The `work()` function already calls `self.adapter.update_progress(run_id, percent, 100, label)`. We add `self.adapter.set_validation_state(run_id, outcomes_snapshot, queue_size)` after each batch of validation results come in. The progress handler serialises and returns this alongside existing fields.  
**Alternatives considered**:
- WebSocket push — no WebSocket infrastructure exists; significant new complexity
- Separate `/api/analysis/validation/{run_id}` endpoint — technically clean but adds a second polling loop on the frontend; the existing progress loop is simpler to reuse
- Server-Sent Events — no SSE infrastructure; same complexity as WebSocket

---

## 4. Integration Point in Analysis Pipeline

**Decision**: Pass `on_candidate_discovered: Callable[[str], None] | None = None` to `AnalysisService.analyze()`  
**Rationale**: The `analyze()` method already accepts several optional callbacks (`on_progress`, `on_log_record`). Adding `on_candidate_discovered` follows the same pattern. The callback is invoked after the first occurrence of each unique `normalized_name` is recorded. A `seen_normalized: set[str]` is maintained locally in `analyze()` for deduplication tracking.  
**Deduplication key**: `normalized_name` (output of `AnalysisService.normalize_name(cleaned)`) matches the run-scope deduplication contract in the spec (FR-003).  
**Implementation note**:
```python
seen_normalized: set[str] = set()
# In the per-frame extraction loop, after normalized_name is computed:
if normalized_name not in seen_normalized:
    seen_normalized.add(normalized_name)
    if on_candidate_discovered is not None:
        on_candidate_discovered(normalized_name)
```
**Alternatives considered**:
- Post-scan batch enqueue (loop over `analysis.player_summaries` after `analyze()` returns) — violates FR-003a (concurrent dispatch)
- Hook into `analysis.add_detection_record()` — would require coupling `VideoAnalysis` dataclass to validation concerns, violating modularity
- Separate scan-then-validate pipeline — violates concurrency requirement

---

## 5. Recommendation Signal Weighting

**Decision**: +20 for `found`, −10 for `not_found` applied to `RecommendationService.score_candidate()`  
**Rationale**: Current base score is 50. Temporal proximity adds up to 30. Status bonus adds 20. Max is 100. Adding +20 for `found` moves a base-only candidate from 50 → 70, which equals the default recommendation threshold — effectively making "found" candidates auto-confirm eligible by default. A −10 for `not_found` pushes candidates to 40, clearly below the threshold. This satisfies SC-006 ("found consistently ranked above equivalent not-found") and the spec's "substantially higher" language. Both adjustments are capped via the existing `min(100.0, ...)` and `max(0.0, ...)` guards.  
**Alternatives considered**:
- +30/−20 — too aggressive; would override temporal evidence too strongly
- Separate validation score field with its own threshold — over-engineering; single weighted signal is sufficient
- Boolean flag on group recommendation only — would not satisfy per-candidate icon requirement

---

## 6. Persistence of Validation Outcomes

**Decision**: Store `validation_outcomes` dict in the per-run sidecar JSON (`result_<n>.review.json`)  
**Rationale**: The sidecar is already the persistence layer for per-run candidate state (decisions, corrections). Validation outcomes are run-scoped (FR-013) and naturally belong alongside candidate data in the same sidecar. The existing `ReviewSidecarStore` handles reading/writing sidecars; adding a `update_validation_outcomes()` method is the minimal extension.  
**Structure**:
```json
{
  "validation_outcomes": {
    "<normalized_spelling>": {
      "spelling": "PlayerName",
      "state": "found|not_found|failed|checking|unchecked",
      "checked_at": "2026-05-01T12:34:56Z",
      "source": "analysis_batch|manual_review"
    }
  }
}
```
**Key**: normalized spelling (lowercase + stripped) — same key used for deduplication.  
**Alternatives considered**:
- Separate `validation.json` file per workspace — adds filesystem complexity; sidecar already purpose-built for run-scoped candidate data
- In-memory only (no persistence) — violates FR-013 (must persist for review reopen)

---

## 7. Manual Recheck Endpoint

**Decision**: Synchronous HTTP check dispatched inline in `review_actions.py`; no shared queue  
**Rationale**: Manual recheck is a user-initiated one-off. Using the same `ValidationService` queue would add unnecessary coupling and state management. A simple synchronous `urllib.request.urlopen()` call (10-sec timeout) is appropriate. The endpoint is small, testable, and consistent with the spec requirement that the check "update only the targeted candidate card" (FR-011).  
**Endpoint**: `POST /api/review/candidates/{candidate_id}/validate` with `{ video_id: str }` body  
**Flow**: resolve candidate spelling from sidecar → HTTP check → write updated outcome to sidecar → return result  
**Alternatives considered**:
- Reuse `ValidationService` instance across analysis and manual review — complex lifecycle management; overkill for one-off checks
- `GET` request to profile URL with `HEAD` method — RSI site may not support HEAD; `GET` is more reliable
