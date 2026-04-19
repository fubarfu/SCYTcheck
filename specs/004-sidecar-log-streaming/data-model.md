# Data Model: Continuous Sidecar Log Writing

**Feature**: 004-sidecar-log-streaming  
**Date**: 2026-04-14

---

## Existing Entities (unchanged)

### LogRecord

Defined in `src/data/models.py`. No changes to this dataclass.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp_sec` | `str` | Formatted HH:MM:SS.mmm timestamp of the frame |
| `raw_string` | `str` | Raw string returned by OCR |
| `tested_string_raw` | `str` | String submitted for matching, before normalization |
| `tested_string_normalized` | `str` | Normalized form used for pattern matching |
| `accepted` | `bool` | Whether the string passed filtering |
| `rejection_reason` | `str` | Reason for rejection (empty if accepted) |
| `extracted_name` | `str` | Name extracted by pattern, empty if rejected |
| `region_id` | `str` | Colon-separated `x:y:w:h` identifier of the capture region |
| `matched_pattern` | `str` | Pattern ID that matched, empty if none |
| `normalized_name` | `str` | Normalized form of extracted name |
| `occurrence_count` | `int` | How many times this name appeared in the run |
| `start_timestamp` | `str` | Formatted first-seen timestamp |
| `end_timestamp` | `str` | Formatted last-seen timestamp |
| `representative_region` | `str` | Region where the name appeared most frequently |

### VideoAnalysis

Defined in `src/data/models.py`. No changes. Continues to accumulate `log_records: list[LogRecord]` during analysis (for the retry-export path).

---

## New Entity: SidecarLogWriter

**Module**: `src/services/logging.py`  
**Purpose**: Holds an open CSV file handle for the duration of an analysis run and writes one row per `LogRecord` immediately upon receipt.

| Attribute | Type | Description |
|-----------|------|-------------|
| `_folder` | `Path` | Resolved output directory |
| `_path` | `Path` | Full path to the sidecar log CSV file |
| `_handle` | `IO[str] \| None` | Open file handle; `None` when writer is not active |
| `_writer` | `csv.writer \| None` | CSV writer bound to `_handle`; `None` when not active |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(output_folder: str, summary_filename: str)` | Stores folder and derives filename; does not open file yet |
| `__enter__` | `() -> SidecarLogWriter` | Opens file, writes header, flushes; returns `self` |
| `__exit__` | `(exc_type, exc_val, exc_tb) -> None` | Closes file handle unconditionally (normal exit and exception exit) |
| `write_record` | `(record: LogRecord) -> None` | Writes one CSV row and flushes; swallows `OSError` silently |

### State Transitions

```
(created) --enter--> (active: header written, file open)
    (active) --write_record()--> (active: N rows written)
    (active) --exit--> (closed)
    (active, OSError in write)--> (active: error logged, continue)
```

---

## Modified Signatures

### AnalysisService.analyze()

Added optional parameter (no breaking change):

```python
def analyze(
    self,
    url: str,
    regions: list[tuple[int, int, int, int]],
    start_time: float,
    end_time: float,
    fps: int,
    on_progress: Callable[[int], None] | None = None,
    context_patterns: list[ContextPattern] | None = None,
    filter_non_matching: bool = False,
    event_gap_threshold_sec: float = 1.0,
    video_quality: str = "best",
    logging_enabled: bool = False,
    on_log_record: Callable[[LogRecord], None] | None = None,  # NEW
) -> VideoAnalysis:
```

Each call to `analysis.add_log_record(record)` gains a paired call:
```python
if on_log_record is not None:
    on_log_record(record)
```

### main.py — run_analysis_worker()

Wraps analysis in `SidecarLogWriter` context when `logging_enabled`:

```python
# Conceptual sketch
writer_ctx = (
    SidecarLogWriter(output_folder, filename)
    if advanced.logging_enabled
    else contextlib.nullcontext()
)
with writer_ctx as writer:
    analysis = analysis_service.analyze(
        ...,
        on_log_record=writer.write_record if advanced.logging_enabled else None,
    )
# Batch write_sidecar_log() call after analyze() is REMOVED from normal path
```

---

## CSV Schema (unchanged)

The on-disk sidecar log CSV continues to use `LOG_HEADERS` from `src/services/logging.py`:

```
TimestampSec, RawString, TestedStringRaw, TestedStringNormalized, Accepted,
RejectionReason, ExtractedName, RegionId, MatchedPattern, NormalizedName,
OccurrenceCount, StartTimestamp, EndTimestamp, RepresentativeRegion
```

No schema changes. Byte-level content of a completed run is identical to the current implementation.

---

## Validation Rules

- `SidecarLogWriter` MUST write the header row in `__enter__` before any `write_record()` call.
- `write_record()` MUST flush after each row.
- `write_record()` MUST NOT raise; `OSError` is caught and logged at WARNING.
- `__exit__` MUST close the file handle even when `exc_type` is not `None`.
- When `logging_enabled` is `False`, `on_log_record` MUST be `None`; `SidecarLogWriter` is never instantiated.
