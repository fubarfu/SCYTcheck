# Quickstart: YouTube Text Analyzer

**Date**: April 11, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Prerequisites

- Python 3.11+
- Windows OS
- Internet connection

## Installation

1. Clone the repository
2. Install dependencies: `pip install opencv-python pytesseract yt-dlp`
3. Install Tesseract OCR: Download from https://github.com/UB-Mannheim/tesseract/wiki

## Usage

1. Run `python src/main.py`
2. Enter YouTube URL
3. Select regions on the video frame
4. Click Analyze
5. Choose output CSV file location
6. View results in the CSV

## Development

- Run tests: `pytest tests/`
- Add new features in modular components