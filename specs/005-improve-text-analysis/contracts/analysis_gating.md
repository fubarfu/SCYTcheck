# Contract: Frame-Change Gating Before OCR

**File**: `src/services/analysis_service.py`  
**Method**: `AnalysisService.analyze(...)`

## Purpose

Skip OCR for unchanged frame-region pairs using normalized mean absolute pixel-difference while preserving auditable counters and optional detailed records.

## Inputs

- `gating_enabled: bool` (default `True`)
- `gating_threshold: float` (0.0-1.0, default 0.02)
- `prev_crop`, `curr_crop` grayscale region crops

## Computation

```python
pixel_diff = mean(abs(prev_crop - curr_crop)) / 255.0
```

## Decision

- If gating disabled: execute OCR.
- If shapes changed: execute OCR.
- Else if `pixel_diff < gating_threshold`: skip OCR.
- Else: execute OCR.

## Required Telemetry

- Always increment `total_frame_region_pairs`.
- Increment exactly one of `ocr_executed_count` or `ocr_skipped_count`.
- Ensure invariant: `executed + skipped == total`.

## Detailed Logging Rule

- Detailed per-frame-region decision records are emitted only when detailed sidecar logging is enabled.

## Expected Outcomes

- Supports SC-003 speedup target.
- Supports SC-004 detection variance constraint through thresholded conservative behavior.

