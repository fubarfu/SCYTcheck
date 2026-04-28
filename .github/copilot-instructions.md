# SCYTcheck Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-28

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
- Python 3.11 (backend), TypeScript/React (Vite) frontend + Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; frontend React stack already in `src/web/frontend`; no new third-party dependency required for planning (009-prepare-spec-branch)
- CSV result files, sidecar review JSON (`<result>.review.json`), persistent app settings in `%APPDATA%/SCYTcheck/scytcheck_settings.json` (with local fallback), new persistent video-history index file under app data (009-prepare-spec-branch)
- Python 3.11 (backend), TypeScript/React (Vite) frontend + Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; existing web stack in `src/web/frontend` (012-from-3c6f0ff)
- CSV outputs + per-result sidecar JSON + per-video append-only history container in selected output location (012-from-3c6f0ff)
- Python 3.11 (backend), TypeScript/React (Vite, frontend) + Backend: `opencv-python`, `paddleocr`, `yt-dlp`, `thefuzz`, `numpy`; Frontend: React, Vite, Material Symbols, TypeScript (013-create-spec-branch)
- CSV outputs + JSON sidecar per video; local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local) (013-create-spec-branch)

- Python 3.11 + opencv-python (video processing), pytesseract (OCR), tkinter (UI) (001-youtube-text-analyzer)
- Python 3.11 (backend), TypeScript/React (Vite) frontend + Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; frontend React stack already in `src/web/frontend`; Google Stitch as UI design authority (010-collapse-player-groups)
- CSV outputs + sidecar JSON (`<result>.review.json`) for group consensus state, local file system persistence, zero new dependencies (010-collapse-player-groups)

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
- 013-create-spec-branch: Added Python 3.11 (backend), TypeScript/React (Vite, frontend) + Backend: `opencv-python`, `paddleocr`, `yt-dlp`, `thefuzz`, `numpy`; Frontend: React, Vite, Material Symbols, TypeScript
- 012-from-3c6f0ff: Added Python 3.11 (backend), TypeScript/React (Vite) frontend + Existing `opencv-python`, `numpy`, `paddleocr`/`paddlepaddle`, `thefuzz`, `yt-dlp`; existing web stack in `src/web/frontend`
- 010-collapse-player-groups: Added Python 3.11 (backend), TypeScript/React (Vite) frontend; Google Stitch UI design authority; sidecar JSON consensus state (`<result>.review.json`); zero new dependencies (Phase 0-1 complete: research, data model, API contracts, UI screens)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
