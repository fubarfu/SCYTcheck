# Data Model: Optimize Analysis Hotpaths

**Feature**: 006-optimize-analysis-hotpaths  
**Date**: 2026-04-18

---

## Overview

This feature is primarily behavioral/performance-focused and does not introduce persistent schema changes. It introduces runtime metrics entities and extends existing runtime models with additive fields to support per-stage timing output under detailed logging.

---

## Entities

### 1. GatingDecision (existing behavior contract)

Represents one frame-region gating outcome.

| Field | Type | Rules |
|---|---|---|
| `pixel_diff` | float | clamped to [0.0, 1.0] |
| `decision_action` | enum(`skip_ocr`, `execute_ocr`) | parity-critical with baseline |
| `reason` | string | compatible with existing semantics |

State transition:
- Input crops available -> compute diff -> emit `skip_ocr` or `execute_ocr`
- Shape mismatch -> force `execute_ocr`

### 2. GatingStats (existing model, extended usage)

Aggregates gating counts across analysis run.

| Field | Type | Validation |
|---|---|---|
| `total_frame_region_pairs` | int | >= 0 |
| `ocr_executed_count` | int | >= 0 |
| `ocr_skipped_count` | int | >= 0 |
| `skip_percentage` | derived float | 0..100 when denominator > 0 |

Invariant:
- `ocr_executed_count + ocr_skipped_count <= total_frame_region_pairs`

### 3. TimingBreakdown (new runtime entity)

Captures per-stage elapsed times for one analysis run.

| Field | Type | Units | Validation |
|---|---|---|---|
| `decode_ms` | float | ms | >= 0 |
| `gating_ms` | float | ms | >= 0 |
| `ocr_ms` | float | ms | >= 0 |
| `post_processing_ms` | float | ms | >= 0 |
| `total_ms` | float | ms | >= 0 |

Derived checks:
- `decode_ms + gating_ms + ocr_ms + post_processing_ms <= total_ms + epsilon`
- When detailed logging disabled, timing entity may be omitted from emitted outputs.

### 4. AnalysisRuntimeMetrics (new runtime aggregate)

Encapsulates performance and instrumentation metrics for validation and reporting.

| Field | Type | Validation |
|---|---|---|
| `timing_breakdown` | TimingBreakdown | optional in output, available internally during run |
| `instrumentation_enabled` | bool | reflects detailed logging state |
| `instrumentation_overhead_pct` | float | >= 0; SC-013 pass requires <= 2.0 |

State transitions:
- Analysis start -> initialize counters/timers
- Frame loop -> accumulate per-stage durations
- Analysis end -> finalize totals and overhead metric

---

## Relationships

- One `VideoAnalysis` run has one `GatingStats` aggregate.
- One `VideoAnalysis` run has zero-or-one emitted `TimingBreakdown` (emitted only when detailed logging enabled).
- One benchmark comparison computes one `instrumentation_overhead_pct` for SC-013 gate.

---

## Backward Compatibility Rules

- No required consumer-facing field removals.
- Timing output is additive and conditional on detailed logging.
- Existing CSV outputs and settings keys remain valid.

---

## Validation Mapping

- FR-002/SC-002: decision parity verified against `GatingDecision.decision_action`.
- FR-004/SC-004: grayscale reuse verified through conversion-count instrumentation.
- FR-025/FR-026: stage timing captured and emitted under logging-enabled mode.
- FR-027/SC-013: instrumentation overhead percentage gate <= 2%.
