# Research: Continuous Sidecar Log Writing

**Feature**: 004-sidecar-log-streaming  
**Date**: 2026-04-14  
**Status**: Complete — all NEEDS CLARIFICATION items resolved

---

## Research Question 1: Streaming vs. Batch CSV Write Strategy

**Context**: Currently `write_sidecar_log()` opens the file in `"w"` mode and writes all records in a single pass at the end of analysis. The new requirement is that each record is durable immediately upon generation.

### Options Evaluated

| Option | Mechanism | Durability | Complexity |
|--------|-----------|------------|------------|
| A. Keep file open for entire run | Open with `"w"` at start, call `csv_writer.writerow()` + `flush()` per entry, close at end | ✅ Every entry is durable after `flush()` | Low — standard `csv.writer` usage |
| B. Append mode per entry | Open with `"a"`, write one row, close — for every single entry | ✅ Durable but expensive | Medium — file open/close per entry; OS overhead on Windows |
| C. Write on completion (current) | Batch write after `analyze()` returns | ❌ All data lost on interruption | Low |

**Decision**: **Option A — keep the file open for the entire analysis run, flush after each row.**

**Rationale**:
- One `open()` call + per-row `flush()` is the minimal overhead path; frame intervals are typically hundreds of milliseconds, so flush latency is invisible.
- Keeps the CSV writer state (quoting, dialect) consistent across the whole file rather than re-initialising per entry.
- Aligns with standard Python idioms for streaming CSV writes.
- File closure on unexpected process exit still preserves all flushed rows on Windows (OS-level buffers are flushed when the process exits, and `flush()` ensures OS buffer is not holding the record).

**Alternatives considered**:
- Option B rejected: unnecessary syscall overhead; also means the CSV dialect and writer must be re-created for each append, risking inconsistency.
- Option C (status quo) rejected: violates FR-001 through FR-003.

---

## Research Question 2: Where Should the File Handle Live?

**Context**: `AnalysisService` is a pure processing service with no file I/O responsibility. Adding file writing directly to the service would violate SRP and make unit testing harder.

### Options Evaluated

| Option | Description | SRP | Testability |
|--------|-------------|-----|-------------|
| A. Callback injection | Caller passes `on_log_record: Callable[[LogRecord], None] | None` to `analyze()` | ✅ Service stays pure | ✅ Easy to mock |
| B. File path injection | Caller passes `sidecar_log_path: Path | None` to `analyze()`, service owns I/O | ❌ Mixes concerns | ❌ Requires file system in tests |
| C. Post-analysis batch (current) | File written by caller after `analyze()` returns | ❌ Violates requirement | – |

**Decision**: **Option A — callback injection (`on_log_record` parameter).**

**Rationale**:
- Keeps `AnalysisService` free of any file I/O.
- `main.py` constructs the `SidecarLogWriter` and passes its `.write_record` method as the callback.
- The existing `analysis.log_records` list can still be populated in parallel (for the retry-export path which needs all records in memory).
- Unit tests for `AnalysisService` can verify the callback is invoked N times without touching the filesystem.

---

## Research Question 3: SidecarLogWriter Design

**Context**: The file handle must be opened before the analysis loop, written to per entry, and reliably closed even on failure.

**Decision**: A lightweight class (`SidecarLogWriter`) implementing the context manager protocol (`__enter__` / `__exit__`).

- `__enter__`: opens file, creates `csv.writer`, writes header row, flushes.
- `write_record(record: LogRecord)`: writes one row, flushes; catches and silently logs `OSError` to satisfy FR-004 (non-fatal write failures).
- `__exit__`: closes file handle.

```python
# Sketch (not normative — see data-model.md)
with SidecarLogWriter(output_folder, summary_filename) as writer:
    analysis = analysis_service.analyze(
        ...,
        on_log_record=writer.write_record if logging_enabled else None,
    )
```

**Rationale**: Context manager guarantees file closure on both normal exit and exception exit, satisfying the durability requirement across all interruption scenarios described in the spec.

---

## Research Question 4: Retry Export Path

**Context**: `main.py` has a `retry_export()` function that re-exports using `analysis.log_records` already in memory. This path must still work after the feature change.

**Decision**: The retry export path continues to call `write_sidecar_log()` (the existing batch function). Since `analysis.log_records` is still populated during analysis, this path is unaffected. In the normal analysis path, the batch `write_sidecar_log()` call at the end of `run_analysis_worker()` is removed (replaced by streaming writes), but the retry path keeps the batch call.

---

## Research Question 5: Error Handling on Disk Full / Locked File

**Context**: FR-004 requires write failures to be non-fatal.

**Decision**: `SidecarLogWriter.write_record()` wraps each `csv_writer.writerow()` + `flush()` in a `try/except OSError`. On failure, the exception is swallowed (or logged at WARNING level to the app logger), and analysis continues. The file handle is not closed on write failure — subsequent writes are still attempted in case the transient condition resolves (e.g., temporary lock lifted).

---

## Resolved Items Summary

| Was NEEDS CLARIFICATION | Resolution |
|-------------------------|------------|
| Best write strategy for streaming CSV | Option A: keep file open, flush per entry |
| File handle ownership | Callback injection; `SidecarLogWriter` lives in `main.py` scope |
| Error handling | Non-fatal: catch `OSError`, log warning, continue analysis |
| Retry export path impact | None — batch write path retained for `retry_export()` |
