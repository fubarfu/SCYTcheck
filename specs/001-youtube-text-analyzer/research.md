# Research Findings: YouTube Text Analyzer

**Date**: April 11, 2026  
**Feature**: `specs/001-youtube-text-analyzer/spec.md`

## Decision: On-Demand YouTube Frame Retrieval

**Chosen**: Use `yt-dlp` to resolve stream URLs and `ffmpeg`-backed OpenCV decode/seek for frame extraction without full media download.

**Rationale**: Matches FR-003 and FR-018 while keeping runtime dependencies aligned with current codebase.

**Alternatives considered**:
- Full video download before analysis: slower startup, violates on-demand intent.
- YouTube Data API media retrieval: not suitable for direct frame analysis flow.

## Decision: Video Quality Selection Behavior

**Chosen**: Expose user-selectable video quality with default to best available quality; no automatic downgrade.

**Rationale**: Satisfies FR-046 and preserves user control over OCR tradeoffs.

**Alternatives considered**:
- Automatic fallback: conflicts with explicit no-auto-downgrade clarification.
- Fixed best-only: reduces flexibility for constrained networks.

## Decision: URL Validation and Error Classification

**Chosen**: Two-stage validation (format then accessibility preflight) with distinct user-facing outcomes for malformed URL, private/unreachable media, and transient retrieval failures.

**Rationale**: Aligns FR-002 and FR-045 and improves actionable feedback.

**Alternatives considered**:
- Single runtime validation only: late failure and ambiguous messages.

## Decision: OCR and Context-Pattern Extraction

**Chosen**: Case-insensitive substring matching with optional `before_text` / `after_text` pattern boundaries; resolve collisions deterministically per FR-041.

**Rationale**: Deterministic extraction is testable and robust against OCR casing variance.

**Alternatives considered**:
- Regex-first pattern system: adds complexity for the target UX.

## Decision: Recall-First Candidate Preservation

**Chosen**: Preserve every non-empty context-matched candidate through candidate collection (FR-034), then apply normalization and event aggregation.

**Rationale**: Prioritizes not missing valid player names in low-quality video scenarios.

**Alternatives considered**:
- Early aggressive filtering: increases false negatives.

## Decision: Deduplication and Event Merging

**Chosen**: Deduplicate by normalized name across full video and compute occurrence counts from merged events with configurable gap (default `1.0s`).

**Rationale**: Matches FR-028 to FR-031 and avoids frame-count inflation.

**Alternatives considered**:
- Frame-level counts: noisy and less meaningful for user output.

## Decision: Region Selector UX and Instruction Placement

**Chosen**: Region selector opens in foreground; instructional text is legible and displayed in a dedicated area below video, never overlaying video content.

**Rationale**: Implements FR-036, FR-037, and FR-051 together without conflicting rendering constraints.

**Alternatives considered**:
- Overlay instructions on video: can obstruct region placement and reduce readability.

## Decision: Optional Analysis Audit Logging

**Chosen**: Advanced Settings toggle (default off) writes sidecar CSV log when enabled, named `<output_base>_log.csv` in the output folder.

**Rationale**: Satisfies FR-047 to FR-050 while preserving default lean workflow.

**Alternatives considered**:
- Always-on logging: unnecessary noise and I/O overhead.
- JSON or free-form text logs: less convenient for quick spreadsheet-style inspection.

## Decision: Log CSV Schema and Timestamp Format

**Chosen**: Fixed ordered headers:
`TimestampSec, RawString, Accepted, RejectionReason, ExtractedName, RegionId, MatchedPattern`
with `TimestampSec` formatted as `HH:MM:SS.mmm`.

**Rationale**: Deterministic schema simplifies tests and troubleshooting.

**Alternatives considered**:
- Flexible headers: harder validation and parsing.
- Numeric seconds format: acceptable but not selected.

## Decision: Packaging and Distribution

**Chosen**: Portable ZIP bundles for x64/x86 with bundled FFmpeg and Tesseract language data, signed executables/packages.

**Rationale**: Directly supports FR-010 to FR-014 and Windows-friendly usage.

**Alternatives considered**:
- Installer-only distribution: not requested.
- Unbundled runtime dependencies: violates portability requirements.

## Summary

All technical clarifications are resolved with concrete implementation choices. No open `NEEDS CLARIFICATION` items remain.