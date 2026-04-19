# Quickstart: Improve Text Analysis

Feature folder: `specs/005-improve-text-analysis`

## 1. Prerequisites

1. Activate environment and install dependencies.
2. Ensure OCR runtime models are available for local execution.
3. Confirm project tests run cleanly before feature work.

## 2. Implement in this order

1. `src/services/ocr_service.py`
  - Build joined-region-text-only matching flow.
  - Enforce nearest bounded span (`<= 6` tokens) between boundaries.
  - Enforce extracted token validation (non-empty and contains alphanumeric).
2. `src/config.py` and `src/components/main_window.py`
  - Keep global tolerance control (0.60-0.95, default 0.75).
  - Keep gating toggle default enabled.
3. `src/services/analysis_service.py`
  - Preserve normalized MAD gating decisions.
  - Preserve always-on counters and optional detailed sidecar records.
4. `src/main.py` integration wiring
  - Ensure settings propagate consistently into analysis and OCR matching calls.

## 3. Validate behavior

1. Multiline joined-only extraction
  - Run integration tests targeting multiline overlays and verify SC-001.
2. Tolerance recovery
  - Compare strict (0.75) vs relaxed (for example 0.65) behavior and verify SC-002.
3. Gating performance and accuracy
  - Verify SC-003 and SC-004 for static/mixed frame sequences.
4. Logging throughput impact
  - Verify SC-005 with logging enabled vs disabled.

## 4. Suggested command sequence

```powershell
cd src
pytest tests/unit/test_ocr_service.py -q
pytest tests/unit/test_analysis_service.py -q
pytest tests/integration/test_us1_multiline_extraction.py -q
pytest tests/integration/test_performance_sc001.py -q
pytest tests/integration/test_performance_sc002.py -q
pytest tests/integration/test_performance_sc003.py -q
pytest tests/integration/test_performance_sc004.py -q
pytest tests/integration/test_performance_sc005.py -q
ruff check .
```

## 5. Done criteria

1. Functional requirements FR-001 through FR-021 satisfied.
2. Success criteria SC-001 through SC-005 demonstrated by tests.
3. No new constitution gate violations introduced.

