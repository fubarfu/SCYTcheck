# Quickstart: YouTube Text Analyzer

**Date**: April 11, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Prerequisites

- Python 3.11+
- Windows OS
- Internet connection
- FFmpeg available (bundled in packaged builds)
- Tesseract OCR with English/German data (bundled in packaged builds)

## Installation

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Ensure Tesseract is installed for development runs.

## Usage

1. Run `python src/main.py`.
2. Enter a YouTube URL.
3. Use the time scrollbar to pick a representative frame and draw region(s).
4. Open Advanced Settings and review context patterns:
	- default `after_text`: `joined`
	- default `after_text`: `connected`
5. Optional: Add additional before/after pattern rules, toggle pattern-only output filtering, and adjust event-gap threshold (default 1.0 sec).
6. Select only an output folder (filename is auto-generated).
7. Start analysis and wait for completion.
8. Open CSV output: one row per normalized player name with event-based occurrence count.

## Development

- Run all tests: `pytest tests/`
- Run unit tests only: `pytest tests/unit/`
- Key business rules to test:
	- context-pattern matching and extraction boundaries
	- normalization and deduplication
	- appearance event merging using the configured gap threshold