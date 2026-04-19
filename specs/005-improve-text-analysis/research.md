# Research Findings: Improve Text Analysis

**Phase**: Phase 0 (Research)  
**Date**: 2026-04-15  
**Status**: Complete

## Decision 1: Joined-Only Multiline Matching Input

**Decision**: Use one full joined, normalized region text block as the canonical matching input and disable separate per-line matching for context-pattern extraction.

**Rationale**:
- Current failure mode is dominated by multiline splits across OCR lines.
- Joined-only behavior removes line-boundary sensitivity and simplifies execution paths.
- A single canonical text representation improves deterministic diagnostics and reduces branch complexity.

**Alternatives considered**:
- Keep per-line matching and add multiline fallback windows: rejected because most lines currently fail, making fallback effectively always-on.
- Geometry-aware line grouping: rejected for higher complexity and uncertain immediate payoff.

## Decision 2: Precision Guardrails for Joined-Only Path

**Decision**: Apply nearest bounded-span extraction (max 6 tokens between matched boundaries) plus extracted-token validation (reject empty/non-alphanumeric).

**Rationale**:
- Joined-only matching can increase accidental cross-line matches in noisy overlays.
- Bounded nearest-span rule prevents long-distance boundary pairing.
- Token validation blocks obvious garbage captures without heavy heuristics.

**Alternatives considered**:
- No additional guardrails: rejected due to expected precision regression.
- Require both boundaries for all patterns: rejected as too strict for valid one-boundary patterns.
- Raise global OCR confidence threshold: rejected as a blunt instrument that can hurt recall.

## Decision 3: Global User Tolerance

**Decision**: Keep one global numeric matching tolerance (0.60-0.95, default 0.75) applied to all enabled patterns.

**Rationale**:
- Simple user model and low UI/config complexity.
- Directly addresses OCR character substitutions in boundary phrases.
- Default preserves current strict behavior.

**Alternatives considered**:
- Per-pattern tolerance: rejected for configuration complexity and lower usability.
- Auto-tuning tolerance per run: rejected for non-determinism and explainability concerns.

## Decision 4: Frame-Change Gating Metric and Defaults

**Decision**: Use normalized mean absolute pixel-difference (0.0-1.0) per frame-region pair; default threshold 0.02; gating enabled by default.

**Rationale**:
- Efficient, vectorized computation with current dependencies (`numpy`, `opencv-python`).
- Supports explicit, auditable skip/execute decisions.
- Aligns with existing success targets for runtime and variance.

**Alternatives considered**:
- Hash-only gating: rejected due to poorer sensitivity to subtle changes.
- Perceptual hash flow: rejected due to additional complexity and tuning burden.

## Decision 5: Gating Telemetry Scope

**Decision**: Always track in-memory counters; emit detailed per-frame-region records only when detailed logging is enabled.

**Rationale**:
- Meets observability requirements without constant I/O overhead.
- Supports summary UX and optional deep diagnostics.

**Alternatives considered**:
- Always write detailed records: rejected for throughput and storage overhead.
- Counters only, no detailed mode: rejected due to reduced diagnosability.

## Dependency and Integration Outcome

- No new third-party dependencies required.
- Primary affected modules: `src/services/ocr_service.py`, `src/services/analysis_service.py`, `src/config.py`, `src/components/main_window.py`, `src/main.py`.

## Open Clarifications Status

All previously identified clarifications are resolved in `spec.md`; no remaining NEEDS CLARIFICATION items for Phase 1.

