# Contract: Portable Bundle OCR Asset Layout

## Scope

Defines the release-bundle expectations for shipping PaddleOCR in the Windows portable ZIP.

## Required Bundle Contents

- Application executable and Python runtime produced by PyInstaller
- FFmpeg bundle required by existing video workflows
- PaddleOCR Python runtime dependencies required by the packaged executable
- Local PaddleOCR detection and recognition model directories required for offline inference
- Any auxiliary OCR support files needed for first-run analysis

## Behavioral Guarantees

1. Offline readiness

- Extracting the ZIP is sufficient for OCR analysis to work on a supported Windows machine.
- No network connectivity is required to fetch models or initialize OCR runtime assets.

1. Deterministic lookup

- The packaged application resolves bundled OCR assets from known local paths relative to the executable or packaged resource root.
- Asset lookup must not depend on a developer machine’s global Python environment.

1. Failure signaling

- If required bundled OCR assets are missing or unreadable, startup or first OCR use must fail with a clear message.
- The app must not silently fall back to remote downloads.

## Validation Contract

- Release-bundle checks must verify that the build script stages OCR assets into the bundle.
- A clean-machine validation path must confirm first-run OCR works from the extracted ZIP with no additional installation.
