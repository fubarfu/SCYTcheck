# Quickstart: Validate Sequential Frame Sampling Optimization

## 1) Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

## 2) Run focused unit tests
```powershell
pytest tests/unit/test_video_service.py -q
```

## 3) Run integration baseline checks
```powershell
pytest tests/integration/test_us1_workflow.py -q
pytest tests/integration/test_performance_sc001.py -q
pytest tests/integration/test_video_service_network_stream.py -q
pytest tests/integration/test_video_service_codec_parity.py -q
pytest tests/integration/test_video_service_fallback.py -q
pytest tests/integration/test_video_service_logging_contract.py -q
pytest tests/integration/test_video_service_memory_stability.py -q
```

## 4) Run full regression suite
```powershell
python -m pytest tests/ -q
```

## 5) Manual verification scenarios
1. Analyze 1-hour game session (H.264/MP4) at `fps=1` and capture iteration runtime.
2. Analyze equivalent duration VP9/WebM source and compare:
   - frame count
   - timestamp sequence
   - OCR/player summary parity
3. Run 2-hour sample and confirm RSS stability checkpoints (0/50/100) within +-10%.

## 6) Debug observability verification
- Enable debug logging and confirm events include:
  - single initialization seek/setup event
  - no per-sample random seek events in sequential path
  - fallback reason (`decode_error` or `performance_probe`) if fallback activates

## 7) Acceptance checklist
- Meets SC-001 through SC-014 in `spec.md`
- No API/signature changes for `iterate_frames_with_timestamps`
- All existing tests pass

## 8) Final Validation Runbook
1. Run focused sequential/fallback unit tests:
  ```powershell
  pytest tests/unit/test_video_service.py -q
  ```
2. Run expanded performance and compatibility checks:
  ```powershell
  pytest tests/integration/test_performance_sc001.py tests/integration/test_us1_workflow.py -q
  ```
3. Run full regression:
  ```powershell
  python -m pytest tests/ -q
  ```
