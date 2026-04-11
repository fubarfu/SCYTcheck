# SCYTcheck - YouTube Text Analyzer

SCYTcheck analyzes a YouTube video for text in user-selected regions and exports detections to CSV.

## Requirements

- Python 3.11+
- Tesseract OCR installed on Windows

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```bash
python -m src.main
```

## Workflow

1. Enter a YouTube URL
2. Choose an output CSV path
3. Click "Select Regions + Analyze"
4. Draw one or more regions on the video frame (ESC to finish)
5. Wait for progress completion and open the CSV output

## Development

```bash
pytest
ruff check .
black --check .
```
