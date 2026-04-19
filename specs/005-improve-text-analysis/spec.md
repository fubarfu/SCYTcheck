# Feature Specification: Improve Text Analysis

**Feature Branch**: `007-improve-analysis-robustness`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "The text analysis shall be improved. Line breaks in text within a defined region shall be handled to not break the pattern recognition. The fuzzyness for the recognition of context patterns shall be relaxed by user choice. As many player names are rejected because the correct pattern is recognized with character errors. Use frame change gating before OCR to leverage that many adjacent sampled frames are visually identical in selected regions; skip OCR if crop hash/difference is below threshold. Leverage further seed improvements that are possible when sidecar logging is off."

## Clarifications

### Session 2026-04-15

- Q: How should user-controlled matching tolerance be configured? → A: One global numeric tolerance (for example 0.60 to 0.95) set by user.
- Q: Which frame-change gating metric should be used? → A: Normalized mean absolute pixel-difference threshold (0.0-1.0).
- Q: How should gating behavior be exposed/tracked? → A: In-memory counters always; detailed records only when detailed logging is enabled.
- Q: Should frame-change gating be enabled by default? → A: Frame-change gating enabled by default; user can toggle off in Advanced Settings.
- Q: How should multi-line OCR matching be performed? → A: Join all OCR lines in the region into one text block and match only on that full joined text.
- Q: Which precision guardrails should be applied for joined-only matching? → A: Use nearest bounded span (max 6 tokens) plus extracted-name token validation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reliable Name Extraction from Multi-Line Text (Priority: P1)

As an analyst, I want names to be extracted correctly even when text in a selected region wraps across lines, so that expected detections are not lost.

**Why this priority**: Correct extraction is the primary value of the product. Missed names directly reduce trust in output.

**Independent Test**: Can be fully tested by running analysis on clips where target text wraps over line breaks and verifying the expected names are present in exported results.

**Acceptance Scenarios**:

1. **Given** OCR output from a selected region where a context phrase and name are split by line breaks, **When** analysis is run, **Then** the expected name is extracted and included in results.
2. **Given** OCR output containing multiple line breaks and inconsistent spacing, **When** pattern matching is applied, **Then** matching behaves consistently as if spacing were normalized.

---

### User Story 2 - User-Controlled Matching Tolerance (Priority: P1)

As an analyst, I want to relax context-pattern matching tolerance when OCR quality is poor, so that valid names with minor character errors are still accepted.

**Why this priority**: OCR errors are common in real videos, and fixed strictness causes false rejections.

**Independent Test**: Can be fully tested by running the same clip with strict and relaxed tolerance settings and verifying that relaxed mode recovers expected names without changing unrelated workflow steps.

**Acceptance Scenarios**:

1. **Given** OCR text with minor character substitutions in context phrases, **When** the user sets a lower numeric tolerance value, **Then** names that satisfy the configured tolerance are accepted.
2. **Given** the user keeps a higher numeric tolerance value, **When** analysis is run on the same input, **Then** only matches meeting stricter criteria are accepted.

---

### User Story 3 - Faster Analysis on Static Adjacent Frames (Priority: P2)

As an analyst, I want analysis to skip redundant OCR work on visually unchanged sampled frames, so that long runs complete faster.

**Why this priority**: Speed improvements significantly improve usability, especially on long videos.

**Independent Test**: Can be fully tested on a clip with long static periods by verifying that runtime decreases while exported detection results remain equivalent to baseline behavior.

**Acceptance Scenarios**:

1. **Given** adjacent sampled frames in a selected region are visually unchanged, **When** analysis is run with frame-change gating enabled, **Then** OCR is skipped for unchanged samples in that region.
2. **Given** a visible change appears in a selected region, **When** the next sampled frame is processed, **Then** OCR is executed for that frame.
3. **Given** sidecar logging is disabled, **When** analysis is run, **Then** additional non-essential per-frame work is minimized to improve throughput.

### Edge Cases

- A selected region yields empty or near-empty text for long periods, then briefly contains valid text.
- Context phrases are split by multiple consecutive line breaks or irregular whitespace.
- Joined text contains multiple valid boundary pairs; extraction must pick the nearest valid bounded span to avoid cross-line false positives.
- Relaxed matching tolerance is set so high that false positives increase; user must be able to return to stricter behavior.
- Frame-change gating is active but subtle visual differences occur (for example antialiasing or compression noise).
- Multiple selected regions change at different times; gating must evaluate each region independently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST normalize OCR text across line breaks and whitespace before context-pattern evaluation.
- **FR-002**: System MUST support context-pattern matching where boundary phrases and candidate names may span multiple OCR lines within the same selected region by joining all OCR lines from the region into one normalized text block.
- **FR-019**: System MUST perform context-pattern matching only on the joined region text block for each sampled frame-region OCR result (no separate per-line matching path).
- **FR-020**: System MUST limit boundary-span extraction in joined text to the nearest valid span containing at most 6 whitespace-delimited tokens between matched boundaries.
- **FR-021**: System MUST validate extracted candidate name tokens before acceptance; invalid tokens MUST be rejected when they are empty after normalization or contain no alphanumeric characters.
- **FR-003**: System MUST allow the user to choose one global numeric matching tolerance value for context-pattern recognition.
- **FR-004**: System MUST apply the user-selected global numeric tolerance consistently to all enabled context patterns during the run.
- **FR-005**: System MUST preserve current strict matching behavior by default using tolerance 0.75 when the user does not change the setting.
- **FR-006**: System MUST evaluate sampled frames per selected region for visual change before running OCR using normalized mean absolute pixel-difference.
- **FR-007**: System MUST skip OCR for a sampled frame-region pair when normalized mean absolute pixel-difference is below the configured threshold.
- **FR-008**: System MUST run OCR for a sampled frame-region pair when normalized mean absolute pixel-difference meets or exceeds the configured threshold.
- **FR-013**: System MUST support a user-configurable normalized pixel-difference threshold in the range 0.0 to 1.0 for gating decisions.
- **FR-014**: System MUST use default gating threshold 0.02 on a normalized mean absolute pixel-difference scale of 0.0 to 1.0 when the user does not change the setting.
- **FR-009**: System MUST keep detection and aggregation outputs functionally equivalent to baseline behavior for unchanged inputs when gating is enabled.
- **FR-010**: System MUST reduce non-essential per-frame processing overhead when detailed sidecar logging is disabled; non-essential work includes per-frame-region detailed-record construction and serialization paths that are only needed for sidecar diagnostics.
- **FR-011**: System MUST preserve complete per-frame-region detailed logging records when detailed logging is enabled, with no missing records relative to processed frame-region evaluations.
- **FR-012**: System MUST track and expose run counters for gating behavior including: total frame-region samples evaluated, count of samples with OCR executed, count of samples with OCR skipped, and MUST display these counters in the analysis completion summary.
- **FR-015**: System MUST maintain identical gating-counter semantics and field names across logging-enabled and logging-disabled runs so downstream reporting remains schema-compatible.
- **FR-016**: System MUST include detailed per-frame-region gating records in detailed sidecar log only when sidecar logging is explicitly enabled by the user.
- **FR-017**: System MUST enable frame-change gating by default for all analysis runs.
- **FR-018**: System MUST allow the user to toggle frame-change gating on or off in Advanced Settings.

### Key Entities *(include if feature involves data)*

- **Analysis Tolerance Setting**: User-selected global numeric tolerance value (range 0.60 to 0.95) used to control acceptance strictness for context-pattern recognition during a run.
- **Frame-Region Change Decision**: Per-sampled-frame, per-region decision record indicating whether OCR is executed or skipped based on normalized mean absolute pixel-difference versus threshold.
- **Joined Region Text**: Canonical OCR text representation for a frame-region, created by joining all OCR lines and normalizing whitespace/newlines before context-pattern matching.
- **Boundary Match Window**: Nearest valid span between matched boundaries in joined region text, constrained to at most 6 whitespace-delimited tokens.
- **Extracted Candidate Token Set**: Normalized tokens extracted from the boundary window; candidate is valid only if at least one token is alphanumeric and non-empty.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a validation set containing multiline text overlays, at least 95% of expected names are extracted successfully.
- **SC-002**: On a validation set containing minor OCR character errors in context phrases, relaxed tolerance mode improves true positive detections by at least 20% compared with strict mode.
- **SC-003**: On videos with long static intervals in selected regions, median analysis runtime is reduced by at least 30% with frame-change gating enabled.
- **SC-004**: For the same input and equivalent tolerance, result differences between gated and non-gated runs remain within 1% for accepted detections, defined as ((max accepted detections - min accepted detections) / baseline accepted detections) * 100 where baseline is the non-gated run.
- **SC-005**: With detailed logging disabled, throughput (sampled frame-region evaluations per minute) improves by at least 15% compared with logging enabled under identical conditions.

## Assumptions

- Existing selected-region workflow and export format remain in scope and are not redesigned by this feature.
- Users can tune matching tolerance and gating behavior through existing advanced settings UX patterns.
- Baseline comparison datasets for multiline overlays, OCR-character-error overlays, and static-frame segments are available for validation.
- Detection quality remains primarily dependent on region quality and OCR confidence settings outside this feature scope.
- Matching tolerance uses a normalized similarity ratio scale from 0.0 to 1.0; default 0.75 preserves current strict behavior.
- Fuzzy matching implementations that return 0 to 100 scores must convert scores to a 0.0 to 1.0 ratio before threshold comparison.
- Frame-change gating uses normalized mean absolute pixel-difference on a 0.0 to 1.0 scale, where 0.0 means identical crops.
- Multi-line extraction uses one full joined region text block as the canonical matching input.
