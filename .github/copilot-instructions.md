# SCYTcheck Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-21

## Active Technologies
- Python 3.11 + opencv-python (video processing), pytesseract (OCR), yt-dlp (YouTube streaming), tkinter (UI) (001-youtube-text-analyzer)
- CSV files (no database) (001-youtube-text-analyzer)
- Python 3.11 + opencv-python, pytesseract, yt-dlp, tkinter (001-youtube-text-analyzer)
- CSV files + local JSON settings file (`scytcheck_settings.json`) (001-youtube-text-analyzer)
- CSV output files + local JSON settings file (`scytcheck_settings.json`) (002-youtube-text-analyzer)
- Python 3.11 + opencv-python, pytesseract, yt-dlp, tkinter, numpy (001-youtube-text-analyzer)
- CSV output files + local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json` fallback to local file) (001-youtube-text-analyzer)
- Python 3.11 + `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter`, `numpy` (001-youtube-text-analyzer)
- CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json` fallback to local file) (001-youtube-text-analyzer)
- Python 3.11 + `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter` (stdlib), `numpy`, `thefuzz` (fuzzy substring matching), `Pillow` (001-youtube-text-analyzer)
- CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local file) (001-youtube-text-analyzer)
- Python 3.11 + `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter` (stdlib), `numpy`, `thefuzz`, `Pillow` (001-youtube-text-analyzer)
- CSV output files plus persisted local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local file) (001-youtube-text-analyzer)
- Python 3.11 + `opencv-python`, `yt-dlp`, `numpy`, `pytesseract`, stdlib logging (002-sequential-frame-sampling)
- N/A (in-memory iteration; CSV artifacts handled by existing export service) (002-sequential-frame-sampling)
- Python 3.11 + `opencv-python`, `yt-dlp`, `numpy`, `thefuzz`, `Pillow`, `paddleocr`, `paddlepaddle` (CPU inference), Tkinter stdlib (005-paddleocr-migration)
- Local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to app/local directory), CSV exports, bundled local OCR model files inside release package (005-paddleocr-migration)
- Python 3.11 + `csv` (stdlib), `pathlib` (stdlib) — no new third-party libraries (006-sidecar-log-streaming)
- CSV file on local filesystem; file is opened with `"a"` (append) mode per entry, or kept open as a streaming context manager throughout the analysis run (006-sidecar-log-streaming)
- Python 3.11 + opencv-python (frame processing, pixel-diff), pytesseract/paddleocr (OCR), numpy (efficient array ops), thefuzz (fuzzy matching), Pillow (image manipulation), tkinter (UI), csv/pathlib (stdlib) (007-improve-analysis-robustness)
- CSV exports + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`) (007-improve-analysis-robustness)
- Python 3.11 + `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `tkinter` (stdlib) (007-improve-analysis-robustness)
- CSV outputs + local JSON settings file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback local) (007-improve-analysis-robustness)
- Python 3.11 + `opencv-python` (cv2), `numpy`, `re` (stdlib), `pytest` (tests) (008-improve-analysis-speed)
- N/A — no persistence changes (008-improve-analysis-speed)
- Python 3.11 + `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, `tkinter` (stdlib) (feature/008-improve-analysis-speed)
- CSV outputs + local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback local) + optional sidecar CSV (feature/008-improve-analysis-speed)
- Python 3.11 (backend), JavaScript/HTML/CSS (frontend) + `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, local HTTP API layer under `src/web/api`, browser UI assets under `src/web/frontend` (feature/007-web-based-player-ui)
- CSV outputs, sidecar JSON session state (`<result>.review.json`), thumbnail/frame image files in sibling folder, existing `scytcheck_settings.json` for settings/theme (feature/007-web-based-player-ui)

- Python 3.11 + opencv-python (video processing), pytesseract (OCR), tkinter (UI) (001-youtube-text-analyzer)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- feature/007-web-based-player-ui: Added Python 3.11 (backend), JavaScript/HTML/CSS (frontend) + `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, local HTTP API layer under `src/web/api`, browser UI assets under `src/web/frontend`
- feature/008-improve-analysis-speed: Added Python 3.11 + `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`, `tkinter` (stdlib)
- 008-improve-analysis-speed: Added Python 3.11 + `opencv-python` (cv2), `numpy`, `re` (stdlib), `pytest` (tests)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
