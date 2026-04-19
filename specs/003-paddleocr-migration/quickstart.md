# Quickstart: Validate PaddleOCR Migration

## 1) Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 2) Install or update local dependencies for source validation

```powershell
pip install -r requirements.txt
```

## 3) Run focused OCR and configuration tests

```powershell
pytest tests/unit/test_ocr_service.py tests/unit/test_config.py -q
```

## 4) Run workflow and bundle regression checks

```powershell
pytest tests/integration/test_us1_workflow.py tests/integration/test_release_bundle_fr010_fr013.py -q
```

## 5) Run reference OCR quality comparison

1. Execute the maintained reference validation set against the current baseline build.
2. Execute the same validation set against the PaddleOCR migration build.
3. Compare:
   - correctly recognized player names
   - missed detections
   - false positives
   - output-schema compatibility

## 6) Validate portable package behavior

```powershell
powershell -ExecutionPolicy Bypass -File scripts/release/build.ps1 -Architecture x64
```

Manual packaged verification:

1. Extract the produced ZIP to a clean test directory.
2. Disconnect network access or otherwise ensure no model download path is available.
3. Launch `SCYTcheck.exe`.
4. Run analysis on a known sample recording.
5. Confirm OCR works with bundled assets only.

## 7) Run full regression suite

```powershell
python -m pytest tests/ -q
ruff check src tests --select=E,F,W
```

## 8) Acceptance checklist

- OCR quality improves against the maintained baseline set.
- Existing workflow remains unchanged for users.
- Summary CSV and detailed log outputs remain compatible.
- Portable ZIP works offline after extraction with bundled PaddleOCR assets.
