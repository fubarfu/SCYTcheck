# Contract: Per-Stage Timing Output

**Feature**: 006-optimize-analysis-hotpaths  
**Status**: Draft contract for implementation

## Purpose

Define the behavior and shape of per-stage timing output for analysis runs.

## Triggering Rules

1. Timing collection is performed during analysis execution.
2. Timing output emission is conditional:
- Emit only when detailed logging is enabled.
- Do not emit timing output when detailed logging is disabled.

## Timing Stages

Required stage totals (milliseconds):

- `decode_ms`
- `gating_ms`
- `ocr_ms`
- `post_processing_ms`
- `total_ms`

All values are non-negative floating-point numbers.

## Consistency Rules

1. `total_ms >= 0`
2. Each stage value must be `>= 0`
3. `decode_ms + gating_ms + ocr_ms + post_processing_ms <= total_ms + epsilon`
4. Stage names and meanings are stable for downstream consumers once released.

## Backward Compatibility

1. Timing output is additive metadata only.
2. Existing output schemas remain valid when timing is absent (logging disabled).
3. Existing CSV/settings semantics must not be broken.

## Overhead Constraint

Instrumentation overhead gate:

- `(runtime_with_instrumentation - runtime_without_instrumentation) / runtime_without_instrumentation <= 0.02`

Representative benchmark suite is used for this check; failure blocks GO decision (SC-013).

## Validation Requirements

1. Logging-disabled run verifies no timing emission.
2. Logging-enabled run verifies full stage timing presence.
3. Benchmark check verifies overhead <= 2%.
4. Existing parity and compatibility gates remain unchanged.
