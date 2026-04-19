# Quickstart: Continuous Sidecar Log Writing

**Feature**: 004-sidecar-log-streaming  
**Date**: 2026-04-14

---

## Overview

This feature changes when sidecar log entries are written: from a single batch write after analysis completes, to an incremental write for each entry as it is produced during the frame loop. If analysis is interrupted at any point, the log file on disk contains all entries generated up to that moment.

---

## What Changes

### Before (current)

1. Analysis runs to completion (or is cancelled).
2. `write_sidecar_log(output_folder, filename, analysis.log_records)` is called after `analyze()` returns.
3. If analysis is interrupted before step 2, the sidecar log file is **never created**.

### After (this feature)

1. Before analysis starts, `SidecarLogWriter` opens the log file and writes the CSV header.
2. During analysis, each `LogRecord` is written and flushed to disk immediately via the `on_log_record` callback.
3. After analysis ends (normally or interrupted), the file is closed.
4. The log file reflects **every entry generated up to the point of interruption**.

---

## Key Files

| File | Change |
|------|--------|
| `src/services/logging.py` | Add `SidecarLogWriter` class |
| `src/services/analysis_service.py` | Add `on_log_record` callback param to `analyze()` |
| `src/main.py` | Use `SidecarLogWriter` context; pass callback; remove post-analyze batch write |

---

## Using SidecarLogWriter

```python
from src.services.logging import SidecarLogWriter

# When logging is enabled, wrap the analysis call in the context manager
with SidecarLogWriter(output_folder, filename) as writer:
    analysis = analysis_service.analyze(
        url=url,
        regions=regions,
        start_time=start_time,
        end_time=end_time,
        fps=fps,
        logging_enabled=True,
        on_log_record=writer.write_record,
    )
# File is closed here — even if analyze() raised an exception

# When logging is disabled: pass on_log_record=None (default), no file is created
analysis = analysis_service.analyze(
    url=url,
    regions=regions,
    start_time=start_time,
    end_time=end_time,
    fps=fps,
    logging_enabled=False,
    # on_log_record defaults to None
)
```

---

## Retry Export

The `retry_export()` path in `main.py` is unchanged. It calls the existing `write_sidecar_log()` batch function using `analysis.log_records` (which are still accumulated in memory during analysis), and produces an identical output file.

---

## Error Handling

Write failures (e.g., disk full, file locked) are non-fatal:

- `SidecarLogWriter.write_record()` catches `OSError`.
- Analysis continues; subsequent entries are still attempted.
- The app logger records a `WARNING` for each failed write.
- The file handle is kept open — it is not closed on a write failure.

---

## Testing Guidance

### Unit: AnalysisService callback wiring

```python
# Verify on_log_record is called once per LogRecord added
records = []
analysis = analysis_service.analyze(
    ...,
    logging_enabled=True,
    on_log_record=records.append,
)
assert len(records) == len(analysis.log_records)
```

### Unit: SidecarLogWriter

```python
import csv, io
from src.services.logging import SidecarLogWriter

# Use a tmp_path fixture; verify header + N rows written
with SidecarLogWriter(str(tmp_path), "test_output.csv") as writer:
    writer.write_record(some_log_record)

lines = (tmp_path / "test_output_log.csv").read_text().splitlines()
assert lines[0].startswith("TimestampSec")  # header present
assert len(lines) == 2  # header + 1 data row
```

### Integration: Interruption durability

Start analysis in a thread; cancel after N frames; verify log file has N rows (excluding header).

---

## Acceptance Criteria Reference

| Requirement | Verified By |
|-------------|-------------|
| FR-001 Entry written immediately | `on_log_record` called inside frame loop, before loop continues |
| FR-002 File updated incrementally | Each `write_record()` call flushes to disk |
| FR-003 Entries survive interruption | Thread cancel test: file contains pre-interruption entries |
| FR-004 Non-fatal write failure | OSError caught; analysis continues |
| FR-005 Format unchanged | Header and row structure identical to current `write_sidecar_log()` |
| FR-006 No file when log inactive | `on_log_record=None`; `SidecarLogWriter` never entered |
| FR-007 No perceptible delay | Single flush per row; no blocking I/O beyond OS buffer flush |
