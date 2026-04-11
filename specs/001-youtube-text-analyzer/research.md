# Research Findings: YouTube Text Analyzer

**Date**: April 12, 2026  
**Feature**: `specs/001-youtube-text-analyzer/spec.md`

## Decision: On-Demand YouTube Frame Retrieval

**Chosen**: Use `yt-dlp` to resolve stream URLs and `ffmpeg`-backed OpenCV decode/seek for frame extraction without full media download.

**Rationale**: Matches FR-003 and FR-018 while keeping runtime dependencies aligned with current codebase.

**Alternatives considered**:
- Full video download before analysis: slower startup, violates on-demand intent.
- YouTube Data API media retrieval: not suitable for direct frame analysis flow.

## Decision: Video Quality Selection Behavior

**Chosen**: Expose user-selectable video quality with default to best available quality. If a selected quality is unavailable, fall through to the next lower available quality and show a non-blocking warning indicating requested and actual quality.

**Rationale**: Satisfies FR-046 while preserving user control and improving run robustness against per-video format availability differences.

**Alternatives considered**:
- No fallback: causes avoidable run failures when a selected quality is absent.
- Fixed best-only: reduces flexibility for constrained networks.

## Decision: URL Validation and Error Classification

**Chosen**: Two-stage validation (format then accessibility preflight) with distinct user-facing outcomes for malformed URL, private/unreachable media, and transient retrieval failures.

**Rationale**: Aligns FR-002 and FR-045 and improves actionable feedback.

**Alternatives considered**:
- Single runtime validation only: late failure and ambiguous messages.

## Decision: OCR and Context-Pattern Extraction

**Chosen**: Case-insensitive fuzzy **substring search** over normalized OCR text with configurable similarity threshold (default `0.75`), combined with optional `before_text` / `after_text` extraction boundaries and deterministic collision resolution per FR-041. The algorithm scans the full normalized OCR region text (all line breaks removed, whitespace collapsed) for the best matching occurrence of the pattern anywhere within it.

**Rationale**: Reduces false negatives from OCR noise and spacing/line-break artifacts while preserving deterministic extraction behavior.

**Alternatives considered**:
- Whole-block fuzzy comparison: causes systematic misses when context pattern is a short marker inside a longer OCR string.
- Strict substring-only matching: too brittle for noisy OCR text.
- Regex-first pattern system: adds complexity for target users.

## Decision: Single-Token Name Extraction

**Chosen**: After a boundary match, keep one token only for `ExtractedName`: after-only patterns keep the last token before the marker; before-only and both-boundary patterns keep the first token in the extracted span.

**Rationale**: Implements clarified domain constraint that player names do not contain blanks while preserving deterministic extraction semantics.

**Alternatives considered**:
- Preserve full extracted span: captures extra context words and increases false positives.
- Reject whitespace-containing extractions: drops potentially recoverable names and reduces recall.

## Decision: Output Display Name vs Deduplication Key

**Chosen**: Deduplicate by normalized key, but export `PlayerName` as the first accepted on-screen extracted form observed at the earliest timestamp for that normalized group.

**Rationale**: Keeps grouping robust to OCR variation while preserving user-visible output in on-screen form.

**Alternatives considered**:
- Export normalized lowercase names: easier grouping but loses user-expected presentation.
- Most-frequent form selection: more volatile under noisy OCR and harder to reason about.

## Decision: OCR Normalization and Boundary-Clipped Matches

**Chosen**: Normalize OCR text for matching by removing line breaks and collapsing repeated whitespace runs. If context text is clipped by region boundaries, accept match when either boundary overlap has at least two contiguous characters or fuzzy similarity meets threshold.

**Rationale**: Aligns with recall-first requirement and supports realistic region-cropping/OCR fragmentation behavior.

**Alternatives considered**:
- Require full context text visibility: increases missed detections.
- Single-character boundary overlap acceptance: too permissive.

## Decision: Recall-First Candidate Preservation

**Chosen**: Preserve every non-empty context-matched candidate through candidate collection (FR-034), then apply normalization-key grouping and event aggregation.

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
`TimestampSec, RawString, TestedStringRaw, TestedStringNormalized, Accepted, RejectionReason, ExtractedName, RegionId, MatchedPattern, NormalizedName, OccurrenceCount, StartTimestamp, EndTimestamp, RepresentativeRegion`
with `TimestampSec`, `StartTimestamp`, and `EndTimestamp` formatted as `HH:MM:SS.mmm`.

**Rationale**: Deterministic schema simplifies tests and troubleshooting while tested-string diagnostics improve false-negative debugging for context-pattern matching.

**Alternatives considered**:
- Logging only one tested-string representation: insufficient visibility into normalization effects.
- Flexible headers: harder validation and parsing.

## Decision: Packaging and Distribution

**Chosen**: Portable ZIP bundles for x64/x86 with bundled FFmpeg and Tesseract language data; release packaging does not require signing certificates. Optional signing is a post-build enhancement when a certificate is available.

**Rationale**: Meets FR-010 to FR-014 and supports unsigned portable releases by default.

**Alternatives considered**:
- Mandatory code-signing in release path: rejected due to certificate acquisition burden.
- Installer-only distribution: not requested.
- Unbundled runtime dependencies: violates portability requirements.

## Summary

All technical clarifications are resolved with concrete implementation choices. Summary output remains intentionally minimal (`PlayerName`, `StartTimestamp`) while detailed diagnostics and aggregation metadata are captured in optional sidecar logs.
