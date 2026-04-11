# Implementation Plan: YouTube Text Analyzer

**Branch**: `001-youtube-text-analyzer` | **Date**: April 11, 2026 | **Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)
**Input**: Feature specification from `/specs/001-youtube-text-analyzer/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create a portable Windows desktop application that streams YouTube videos for real-time text analysis in user-defined regions. The app captures detected text strings to a CSV file with deterministic naming and provides region-selection UI with video frame navigation via time-based scrollbar. Distribute as bundled ZIP packages (x64/x86) including Python 3.11, OpenCV, Tesseract OCR (English/German), and FFmpeg, code-signed for user trust.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: opencv-python (video processing), pytesseract (OCR), yt-dlp (YouTube streaming), tkinter (UI)  
**Storage**: CSV files (no database)  
**Testing**: pytest with unittest framework  
**Target Platform**: Windows (x64 and x86)
**Project Type**: Desktop application (Tkinter GUI)  
**Performance Goals**: Analyze 10-minute video in under 5 minutes with 80% OCR accuracy  
**Constraints**: Bundled distribution requires no external installs; OCR must support English and German  
**Scale/Scope**: Single-window UI, folder-based output, 19 functional requirements including packaging/deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Assessed Principles:**
1. ✅ **Simple and Modular Architecture**: Existing service-based design in `src/services/` aligns well.
2. ✅ **Readability Over Cleverness**: Current codebase uses type hints and clear naming.
3. ✅ **Testing for Business Logic**: Tests exist in `tests/`; will expand for new packaging code.
4. ✅ **Minimal Dependencies**: Core deps (opencv, pytesseract, yt-dlp) are justified for OCR/video streaming.
5. ✅ **No Secrets in Repository**: Config loads from environment variables (already in place).
6. ✅ **Windows-Friendly Development**: Target platform is Windows; cross-platform compat secondary.
7. ✅ **Incremental Changes and Working State**: Current app runs; packaging will be non-breaking addition.

**Status**: PASS — no violations detected. Bundling and scrollbar features fit within constitution.

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-text-analyzer/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command) - PENDING
├── data-model.md        # Phase 1 output (/speckit.plan command) - EXISTS
├── quickstart.md        # Phase 1 output (/speckit.plan command) - EXISTS
├── spec.md              # Feature specification
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── ocr_service.md
│   └── video_streaming.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py              # Tkinter app entry point
├── config.py            # Environment-based configuration
├── components/          # UI components
│   ├── main_window.py   # Main window layout
│   ├── url_input.py     # URL input field
│   ├── file_selector.py # Output folder selector
│   ├── region_selector.py
│   └── progress_display.py
├── services/            # Business logic services
│   ├── analysis_service.py
│   ├── export_service.py
│   ├── logging.py
│   ├── ocr_service.py
│   └── video_service.py
└── data/                # Data models
    ├── __init__.py
    └── models.py

tests/
├── unit/                # Unit tests
│   ├── test_export_service.py
│   └── test_models.py
└── integration/         # Integration tests (empty)

pyproject.toml          # Project metadata and dependencies
requirements.txt        # Python dependencies
README.md              # Project documentation
```

**Structure Decision**: Single-project layout with service-based architecture. Existing structure (src/services/, src/components/, src/data/) is maintained. New packaging logic will extend export_service.py and main.py. New scrollbar feature extends region_selector.py.

## Phase 0: Research & Unknowns

**Action**: Generate research.md to resolve critical unknowns before Phase 1 design.

### Research Tasks

1. **PyInstaller + Bundled Dependencies**: Best practices for bundling Python 3.11, OpenCV, pytesseract, and FFmpeg into portable Windows executables (x64/x86).
2. **Code Signing on Windows**: Process, tools, and certificate acquisition for signing executables and packages.
3. **YouTube Video Streaming without Full Download**: Verify yt-dlp capability with current implementation and confirm time-based random-access to video frames.
4. **Tesseract Integration in Bundled Executables**: Path configuration and dependency handling when tesseract.exe is bundled.
5. **Tkinter Freezing with PyInstaller**: Known issues and workarounds when bundling Tkinter GUI applications.

### Outcome

research.md will document decisions and alternatives for each research task.

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete

### Data Model

Extract entities and relationships from spec → generate data-model.md:
- **VideoAnalysis**: URL, regions, detected text, timestamp, output path
- **TextString**: content, region, confidence, frequency
- **Region**: coordinates (x, y, width, height)

### Interface Contracts

Define contracts if exposing external interfaces → contracts/:
- **ocr_service.md**: Input (image, region), Output (list of text strings)
- **video_streaming.md**: Input (URL, time), Output (frame as numpy array)
- Region selection UI protocol (mouse events, frame updates)

### Quickstart

Provide minimal example in quickstart.md:
- How to run dev environment
- Example video URL for testing
- How to define regions and run analysis

### Agent Context Update

Run update-agent-context.ps1 to encode new packaging dependencies into agent-specific context file.

## Phase 2: Planning Summary

**Total Requirements**: 19 functional requirements (FR-001 through FR-019)  
**New Features**: Scrollbar-based region selection (FR-018, FR-019), auto-generated CSV filenames (FR-015, FR-016), output folder validation (FR-017)  
**Packaging Requirements**: Portable ZIP (FR-010), Separate x64/x86 (FR-011), Bundled OCR/FFmpeg (FR-012, FR-013), Code signing (FR-014)  
**Constitutional Status**: All principles pass; no violations to justify

**Next Steps**:
1. Complete Phase 0 (research.md)
2. Complete Phase 1 (data-model.md, contracts/, quickstart.md, agent context)
3. Run `/speckit.tasks` to generate task.md with actionable implementation tasks
4. Begin implementation based on prioritized task list
