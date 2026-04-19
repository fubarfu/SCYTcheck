# Research: Optimize Analysis Hotpaths

**Feature**: 006-optimize-analysis-hotpaths  
**Date**: 2026-04-18  
**Branch**: feature/008-improve-analysis-speed

---

## Decision 1: OpenCV-Native Gating Math

### Decision
Use `cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0` for pixel-diff computation and preserve parity checks on binary decision outcomes.

### Rationale
- Removes repeated float conversion/allocation overhead from NumPy chain operations.
- Keeps gating semantics equivalent for accept/skip at configured thresholds.
- Aligns with clarified requirement: parity is required for decision outcomes, not exact intermediate float values.

### Alternatives considered
- Preallocated NumPy buffers (`out=`): lower gain and higher complexity than direct OpenCV path.
- Additional compute libraries: rejected due to dependency policy and limited incremental benefit.

---

## Decision 2: One Grayscale Conversion Per Sampled Frame

### Decision
Compute grayscale once per sampled frame and reuse for all region crops in that frame.

### Rationale
- Eliminates per-region redundant `cvtColor` calls.
- Preserves per-region independence and threshold behavior.
- Supports existing callers via optional `frame_gray` parameter pattern.

### Alternatives considered
- Frame-level caching object: unnecessary complexity for a single-loop reuse scenario.
- Region-first conversion (existing): retained only as fallback path.

---

## Decision 3: Precompiled Whitespace Regex

### Decision
Use module-level `_RE_WHITESPACE = re.compile(r"\s+")` in normalization functions.

### Rationale
- Eliminates repeated compile/cache lookup overhead in high-frequency normalization paths.
- Maintains exact normalization output equivalence across curated corpus.

### Alternatives considered
- Keep inline `re.sub`: simplest but slower at scale.
- Caching wrapper around normalize functions: low value because input cardinality is high.

---

## Decision 4: Lightweight Per-Stage Timing Output Scope

### Decision
Capture decode, gating, OCR, and post-processing timings in analysis runtime metrics, and emit timing output only when detailed logging is enabled.

### Rationale
- Meets user requirement for run-level time-spend visibility.
- Avoids noisy/default UI output when detailed logging is off.
- Preserves backward compatibility by keeping timing as additive metadata.

### Alternatives considered
- Always-on UI timing output: rejected per clarification.
- Console-only timing: rejected due to weaker discoverability for standard user flow.

---

## Decision 5: Instrumentation Overhead Budget

### Decision
Enforce <=2% total runtime overhead for timing instrumentation on representative benchmark suite.

### Rationale
- Keeps instrumentation aligned with "lightweight" constraint.
- Prevents observability additions from eroding optimization gains.
- Provides objective gate (SC-013) for implementation acceptance.

### Alternatives considered
- No explicit cap: rejected due to ambiguous acceptance.
- 1% cap: rejected as overly strict for Python timing granularity variance.
- 5% cap: rejected as too permissive for a hotpath-focused feature.

---

## Decision 6: Validation Strategy

### Decision
Use dual-path parity tests and synthetic fixtures plus benchmark checks for SC-001/SC-005/SC-013; retain validation report generation for traceability.

### Rationale
- Deterministic CI-compatible validation with no external network/video dependency.
- Explicit proof for parity, performance, and instrumentation overhead constraints.
- Supports go/no-go evidence pack requirements.

### Alternatives considered
- Separate baseline branch execution in CI: operationally brittle and slower.
- Manual-only profiling: rejected due to non-repeatability and weaker gates.
