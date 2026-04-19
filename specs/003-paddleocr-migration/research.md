# Research: PaddleOCR Migration

## Decision 1: Use PaddleOCR Python Integration With Local Bundled Model Paths

- Decision: Integrate PaddleOCR through its Python API inside `OCRService`, and initialize it with explicit local model directories bundled inside the app package rather than allowing runtime model downloads.
- Rationale: PaddleOCR supports Python integration and local model-path configuration, which matches the product requirement for a fully offline portable ZIP and avoids first-run download failures.
- Alternatives considered:
  - Allow PaddleOCR to download models automatically: rejected because it violates the clarified offline portable-package requirement.
  - Use PaddleOCR CLI as a subprocess: rejected because it adds orchestration complexity and weakens service-level integration and testing.

## Decision 2: Preserve Current Language Coverage Parity

- Decision: Preserve the current English and German OCR support baseline in the PaddleOCR migration.
- Rationale: The existing product explicitly bundles English and German OCR data. Reducing language coverage would be a regression; expanding beyond current scope increases package size and validation burden without user justification.
- Alternatives considered:
  - English only: rejected because it regresses current functionality.
  - Broader multilingual package: rejected because it increases bundle size and complexity beyond current product scope.

## Decision 3: Keep Region-Based Analysis And Downstream Matching Intact

- Decision: Continue using user-selected image regions as the OCR input boundary and normalize PaddleOCR results into the same line-oriented text tokens consumed by existing matching, logging, and export paths.
- Rationale: The feature goal is an OCR engine replacement, not a workflow redesign. Preserving the existing downstream interfaces minimizes regression risk and keeps implementation incremental.
- Alternatives considered:
  - Redesign the app around full-frame OCR and auto-layout detection: rejected because it changes product behavior beyond the feature scope.
  - Replace downstream pattern and export logic along with OCR: rejected because the current problem is recognition quality, not the surrounding pipeline contract.

## Decision 4: Disable Unneeded PaddleOCR Pipeline Features By Default

- Decision: Use the general OCR pipeline but disable optional orientation/unwarping features unless validation shows they are required for gameplay HUD text.
- Rationale: SCYTcheck processes small, user-selected HUD regions rather than arbitrary scanned documents. Disabling unneeded pipeline modules reduces runtime cost and packaging surface while preserving the detection+recognition gains that motivate the migration.
- Alternatives considered:
  - Enable the full document-oriented pipeline by default: rejected because it adds runtime and bundle overhead not justified by the use case.
  - Use recognition-only mode without detection: rejected because localized text detection inside the selected region is part of the expected quality gain on noisy gameplay frames.

## Decision 5: Treat Tesseract-Specific Settings As Migration Inputs, Not Long-Term UX Commitments

- Decision: Safely read older settings files, ignore or migrate Tesseract-only knobs where possible, and present a simplified PaddleOCR-relevant configuration surface rather than preserving every legacy tuning field.
- Rationale: The spec requires safe upgrades but not perpetual exposure of obsolete engine-specific controls. Carrying dead settings forward would add confusion and maintenance burden.
- Alternatives considered:
  - Preserve all legacy OCR tuning fields in the UI: rejected because most fields are engine-specific and would become misleading.
  - Drop old settings files entirely: rejected because it would create avoidable upgrade friction.

## Decision 6: Extend Portable Packaging To Include Paddle Runtime And Models

- Decision: Update the build process and PyInstaller spec so the release bundle contains the PaddleOCR Python runtime dependencies, the selected local model directories, and any required auxiliary assets alongside the executable.
- Rationale: The clarified packaging requirement is explicit: the ZIP must work fully offline after extraction. Packaging must therefore be deterministic and asset-complete.
- Alternatives considered:
  - Keep build packaging unchanged and rely on site-packages behavior: rejected because hidden imports and model assets are unlikely to be bundled reliably.
  - Ask users to install Paddle runtime separately: rejected because it breaks the portable-product promise.

## Decision 7: Validate Quality Against A Maintained Baseline Set Before Release

- Decision: Add a repeatable evaluation path that compares PaddleOCR results against the current Tesseract baseline on maintained reference recordings or frame crops, using missed detections and false positives as the primary outcome measures.
- Rationale: The feature is justified by improved recognition quality. Without baseline comparison, the team cannot tell whether the migration actually improved the stated use case.
- Alternatives considered:
  - Rely on subjective spot checks only: rejected because they are not repeatable release gates.
  - Replace the full test suite with OCR-only checks: rejected because workflow and packaging regressions must still be caught.

## Validation Evidence And Constraints (2026-04-14)

- Current codebase facts:
  - OCR is currently implemented through `pytesseract.image_to_data` on thresholded region crops.
  - Portable packaging currently bundles FFmpeg and Tesseract payload trees through `scripts/release/build.ps1`.
  - PyInstaller currently declares `pytesseract` hidden imports and no OCR model data assets.
- External integration facts from PaddleOCR documentation:
  - PaddleOCR supports Python API integration through `PaddleOCR(...)`.
  - PaddleOCR supports explicit local model directories, which fits the offline packaging requirement.
  - Basic OCR inference can be installed via PyPI inference packages without training dependencies.
