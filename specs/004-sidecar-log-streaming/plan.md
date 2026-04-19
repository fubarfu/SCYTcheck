# Implementation Plan: Continuous Sidecar Log Writing

**Branch**: `006-sidecar-log-streaming` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-sidecar-log-streaming/spec.md`

## Summary

Currently the sidecar log is written in a single batch call after analysis completes, discarding all log data if the run is interrupted. This feature changes the write strategy so that each `LogRecord` is flushed to the CSV file immediately upon generation during the frame-processing loop. A callback-based `SidecarLogWriter` utility wraps the open file handle and CSV writer; `AnalysisService.analyze()` accepts an optional `on_log_record` callback and delegates streaming writes to the caller. `main.py` passes the callback when sidecar log is enabled, and the batch write at analysis end is removed for the normal path (only kept for the retry-export path where records are already in memory).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `csv` (stdlib), `pathlib` (stdlib) — no new third-party libraries  
**Storage**: CSV file on local filesystem; file is opened with `"a"` (append) mode per entry, or kept open as a streaming context manager throughout the analysis run  
**Testing**: pytest  
**Target Platform**: Windows desktop (Windows 10+)  
**Project Type**: Desktop application (Tkinter)  
**Performance Goals**: Per-entry write overhead must not be perceptible between consecutive frame analyses; `flush()` after each write is acceptable given typical frame intervals  
**Constraints**: No new dependencies; no changes to the existing sidecar log CSV schema; no UI changes  
**Scale/Scope**: Single analysis run, up to thousands of log records per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Simple and Modular Architecture | ✅ PASS | A single new streaming writer class; no architectural restructuring |
| II. Readability Over Cleverness | ✅ PASS | Callback-based streaming is explicit and easy to follow |
| III. Testing for Business Logic | ✅ PASS | New writer and callback wiring are unit-testable in isolation |
| IV. Minimal Dependencies | ✅ PASS | Uses only stdlib `csv` and `pathlib`, no new libraries |
| V. No Secrets in Repository | ✅ PASS | No credentials or secrets involved |
| VI. Windows-Friendly Development | ✅ PASS | Uses `pathlib` and standard `newline=""` CSV handling |
| VII. Incremental Changes and Working State | ✅ PASS | The existing batch write path (`retry_export`) remains; incremental change |

**Result: All gates PASS. Proceed to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/004-sidecar-log-streaming/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── services/
│   ├── logging.py       # MODIFIED: add SidecarLogWriter class
│   └── analysis_service.py  # MODIFIED: add on_log_record callback param
└── main.py              # MODIFIED: wire SidecarLogWriter callback

tests/
├── unit/
│   └── test_export_service.py   # VERIFY: no regressions
│   └── test_analysis_service.py # EXTENDED: test on_log_record callback
└── integration/
    └── test_log_schema_fr049.py # VERIFY: no regressions
```

**Structure Decision**: Single project; changes are confined to three existing files. No new source files are added.
