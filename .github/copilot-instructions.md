# SCYTcheck Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-11

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
- 001-youtube-text-analyzer: Added Python 3.11 + `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter` (stdlib), `numpy`, `thefuzz` (fuzzy substring matching), `Pillow`
- 001-youtube-text-analyzer: Added Python 3.11 + `opencv-python`, `pytesseract`, `yt-dlp`, `tkinter`, `numpy`
- 001-youtube-text-analyzer: Added Python 3.11 + opencv-python, pytesseract, yt-dlp, tkinter, numpy


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
