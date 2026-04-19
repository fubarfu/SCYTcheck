# PaddleOCR Model Assets (x64)

This folder is intentionally kept minimal in source control.

## Purpose

Place PaddleOCR runtime model directories here for local and release builds.
The packaging workflow expects this tree as input for offline bundling.

## Expected Layout

The migration code discovers model directories by prefix. At minimum, provide:

- `det*` directory for detection model files
- `rec*` directory for recognition model files

Example:

```text
third_party/paddleocr/x64/
  det_en/
    inference.pdmodel
    inference.pdiparams
  rec_en/
    inference.pdmodel
    inference.pdiparams
```

Additional language recognition directories (for example `rec_de`) may be added.

## Notes

- Do not commit large model binaries unless release policy explicitly requires it.
- Use `scripts/download_paddleocr_models.ps1` to stage models automatically.
