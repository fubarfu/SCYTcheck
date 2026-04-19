# Contract: OCR Engine Integration Behavior

## Scope

Defines the behavioral contract for replacing the Tesseract-backed OCR implementation with PaddleOCR while preserving SCYTcheck’s existing user workflow and downstream processing expectations.

## Public Interface Contract

- `OCRService` remains the service boundary used by analysis code.
- Callers continue to request OCR against user-selected image regions.
- OCR outputs remain consumable by existing matching, logging, diagnostics, and export code paths.

## Behavioral Guarantees

1. Region-based analysis remains unchanged

- OCR is executed only on the user-selected crop region.
- No new user action is required to enable detection or recognition.

1. Result normalization compatibility

- OCR results are normalized into line-oriented text entries compatible with current downstream matching behavior.
- Confidence threshold semantics remain available at the application level even if engine-native scoring differs internally.

1. Offline packaged execution

- In packaged mode, OCR initialization uses only bundled local runtime/model assets.
- No first-run network downloads or paid service calls are permitted.

1. Error handling

- Missing required OCR assets or initialization failures must produce a clear user-facing error.
- The application must not silently continue with a half-initialized OCR engine.

1. Settings compatibility

- Older settings files from Tesseract-based releases must load safely.
- Obsolete OCR-engine-specific fields may be ignored or migrated, but they must not block analysis startup.

## Non-Functional Contract

- Recognition quality on the maintained validation set must improve versus the current Tesseract baseline according to `spec.md` success criteria.
- End-to-end analysis must remain practical for CPU-only Windows portable usage.
- Release packaging must remain self-contained and runnable after ZIP extraction.

## Compatibility Contract

- Summary CSV and optional detailed log schemas remain unchanged.
- Existing workflow-level tests remain valid with additive OCR-engine migration assertions.
