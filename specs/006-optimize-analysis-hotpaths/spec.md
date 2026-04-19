# Feature Specification: Optimize Analysis Hotpaths

**Feature Branch**: `feature/008-improve-analysis-speed`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "Optimize analysis performance through OpenCV-native gating math, one grayscale conversion per frame, and precompiled normalization regex with strict non-regression parity."

## Clarifications

### Problem Statement

SCYTcheck analysis performance is constrained by repeated per-region math overhead in frame-region gating, repeated grayscale conversion work for the same sampled frame, and repeated regex compilation in normalization paths. The feature must reduce runtime cost on these hotpaths while preserving quality and behavior as guardrails: precision/recall non-regression is validated by automated pytest test only (not a manual blocking gate), no accepted/rejected detection behavior change for identical inputs/settings, no public API/signature breaks, and no backward-incompatible logging/settings changes.

### Scope Clarification

- In scope: optimization of existing behavior for gating math, grayscale reuse, and normalization regex compilation only.
- In scope: objective parity validation against baseline across deterministic and noisy datasets.
- Precision/recall non-regression is validated via automated pytest test only; no manual analysis gate is required outside of automated tests.
- In scope: lightweight per-stage timing output (decode, gating, OCR, post-processing) emitted only when detailed logging is enabled.

### Session 2026-04-16

- Q: Should SC-007 (precision/recall non-regression) be a hard blocking gate or automated-only gate in SC-012? → A: Automated-only gate — blocking only if a new automated pytest regression test fails; no manual analysis required.
- Q: Should gating parity be enforced on binary accept/skip decisions only, or also on intermediate float score equality? → A: Binary decision outcome parity only — intermediate computed diff value is not constrained; accept/skip result must match baseline.
- Q: Should validation datasets be synthetic in-repo fixtures, existing test fixtures, or both? → A: Synthetic in-repo fixtures created as deliverables of this feature.
- Q: What is the fallback mechanism if a parity gate fails post-merge? → A: Git revert of the optimization commits.
- Q: Should SC-001 (≥15% total runtime) and SC-005 (≥20% gating hotpath) thresholds be adjusted based on profiler evidence? → A: Keep as-is — SC-001 ≥15%, SC-005 ≥20%; conservative and hardware-safe.

### Session 2026-04-18

- Q: Where should per-stage timing output be shown? → A: Show per-stage timing only when detailed logging is enabled.
- Q: What maximum runtime overhead is acceptable for per-stage timing instrumentation? → A: Timing instrumentation overhead MUST be <= 2% of total runtime on the representative benchmark suite.

## User Scenarios & Testing

### User Story 1 - Faster Region Gating With Decision Parity (Priority: P1)

As an analyst running long analyses, I want frame-region gating to run faster using optimized native operations so runtime improves without changing which regions are accepted or skipped.

**Why this priority**: Region gating executes at high frequency and is a direct hotpath. Any drift in threshold behavior can silently alter detections, so this optimization has both high performance impact and high correctness risk.

**Independent Test**: Run baseline and candidate on identical deterministic and noisy datasets, produce a gating diff report, and verify 100% gating decision parity plus runtime gain threshold.

**Acceptance Scenarios**:

1. **Given** identical sampled frames, regions, and gating threshold settings, **When** gating runs in baseline and candidate modes, **Then** every frame-region accept/skip decision is identical.
2. **Given** the candidate optimization enabled, **When** processing a representative workload, **Then** median gating compute time per evaluated frame-region is reduced by the defined success threshold.
3. **Given** region crops with shape mismatch conditions, **When** gating evaluates change, **Then** behavior and outcome semantics match baseline exactly.

---

### User Story 2 - Single Grayscale Conversion Per Frame (Priority: P1)

As an analyst processing many selected regions per frame, I want each sampled frame converted to grayscale once and reused across all region gating operations so repeated conversion overhead is removed without changing gating outcomes.

**Why this priority**: Repeated grayscale conversion scales with region count and creates avoidable per-frame cost. This optimization is a large multiplier for multi-region workflows.

**Independent Test**: Instrument conversion counts and validate exactly one grayscale conversion per sampled frame while confirming gating and detection parity against baseline.

**Acceptance Scenarios**:

1. **Given** a sampled frame with multiple selected regions, **When** gating runs for all regions, **Then** grayscale conversion occurs exactly once for that frame and the result is reused.
2. **Given** identical inputs/settings, **When** baseline and candidate runs complete, **Then** accepted/rejected detections and player summary outputs are identical.
3. **Given** empty or invalid frame data, **When** grayscale conversion/reuse paths execute, **Then** fallback/error semantics match baseline behavior.

---

### User Story 3 - Precompiled Regex Normalization Without Semantic Drift (Priority: P1)

As an analyst expecting stable text extraction quality, I want normalization to avoid repeated regex compilation so performance improves while normalization output remains equivalent.

**Why this priority**: Normalization runs for many OCR strings. Removing repeated compilation is low-risk only if semantic equivalence is proven for whitespace/newline and formatting edge cases.

**Independent Test**: Compare normalization outputs for a broad corpus (deterministic and noisy) between baseline and candidate; require exact string-output equivalence and unchanged downstream detections.

**Acceptance Scenarios**:

1. **Given** OCR text containing irregular spaces/newlines and mixed formatting, **When** normalization executes in baseline and candidate, **Then** normalized strings are exactly equivalent.
2. **Given** identical OCR inputs/settings, **When** end-to-end analysis completes, **Then** accepted/rejected detections, precision/recall metrics, and player summary outputs are unchanged.
3. **Given** high-volume normalization calls, **When** candidate mode is profiled, **Then** regex compilation overhead in hotpaths is eliminated relative to baseline.

## Edge Cases

- Threshold boundary equality: change value exactly equals configured threshold; binary accept/skip decision outcome must match baseline semantics. Intermediate float diff values at boundary are not required to be identical to baseline.
- Tiny or noisy regions: small crops or high compression noise near threshold; parity must be preserved without oscillation drift.
- Empty crop: selected region produces empty crop array; behavior and logging must match baseline.
- Empty frame: sampled frame data is missing/invalid; handling and downstream effects must match baseline.
- Mixed static/dynamic regions: some regions unchanged while others change in the same frame; per-region decisions must stay independent and baseline-equivalent.
- Irregular whitespace/newlines: normalization must preserve baseline output equivalence for tabs, multiple spaces, CRLF/LF mixes, and line-break-heavy OCR outputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace frame-region gating diff computation with optimized OpenCV-native operations while preserving gating decision parity with baseline; intermediate float diff values are not required to match baseline exactly.
- **FR-002**: System MUST preserve exact gating decision outcomes (accept/skip) for every frame-region evaluation under identical inputs, region coordinates, and settings; parity is defined on the binary accept/skip result, not on intermediate computed values.
- **FR-003**: System MUST preserve shape mismatch handling semantics exactly as baseline, including decision outcome, error/skip behavior, and any emitted logging fields.
- **FR-004**: System MUST convert each sampled frame to grayscale at most once and MUST reuse that grayscale representation for all region gating evaluations within that frame.
- **FR-005**: System MUST NOT recompute grayscale independently per region when reusable per-frame grayscale is available.
- **FR-006**: System MUST maintain equivalent gating behavior when grayscale reuse is active, including threshold comparisons and per-region independence.
- **FR-007**: System MUST remove repeated regex compilation overhead in normalization paths by using precompiled regex definitions with equivalent matching/replacement behavior.
- **FR-008**: System MUST produce normalization outputs that are exactly equivalent to baseline for identical OCR input strings, including whitespace/newline canonicalization behavior.
- **FR-009**: System MUST preserve accepted/rejected detection decisions exactly for identical inputs/settings (detection parity).
- **FR-010**: System MUST validate precision and recall non-regression via an automated pytest regression test; manual precision/recall analysis is advisory only and does not block merge.
- **FR-011**: System MUST preserve player summary outputs exactly (player identity, counts, and ordering semantics) for identical runs.
- **FR-012**: System MUST preserve all public APIs/signatures used by existing callers, with no breaking changes.
- **FR-013**: System MUST preserve backward-compatible logging semantics, including existing field names, meanings, and compatibility of downstream consumers.
- **FR-014**: System MUST preserve backward-compatible settings semantics, including current keys/defaults/interpretation for relevant optimization controls.
- **FR-015**: System MUST include a validation matrix covering baseline vs candidate using synthetic in-repo fixtures; deterministic fixtures (e.g., numpy-generated frames, curated OCR string lists) and noisy/realistic fixtures MUST be created as deliverables of this feature and committed to the repository.
- **FR-016**: Validation matrix execution MUST generate a gating diff report that proves parity (or highlights mismatches with frame-region detail) between baseline and candidate.
- **FR-017**: Validation matrix execution MUST include targeted profiling focused on gating hotpath compute, grayscale conversion counts, and normalization overhead.
- **FR-018**: Test coverage MUST include unit tests for gating parity logic, grayscale reuse behavior, and normalization equivalence.
- **FR-019**: Test coverage MUST include integration tests confirming end-to-end accepted/rejected detection parity and player summary parity.
- **FR-020**: Test coverage MUST include performance tests confirming runtime gain thresholds under representative workloads.
- **FR-021**: System MUST define and document risks and mitigations for numeric drift, grayscale reuse behavior drift, and regex semantic drift.
- **FR-022**: Deliverables MUST include: updated specification document, FR-to-SC traceability matrix, completed requirements checklist, and rollout/fallback plan.
- **FR-023**: Rollout/fallback plan MUST define objective rollback triggers; if any parity/non-regression gate fails in validation or early rollout, the fallback action is to git revert the optimization commits. No feature toggle is required.
- **FR-024**: Final release decision MUST enforce a go/no-go acceptance gate requiring automated test pass evidence across all mandatory criteria; manual precision/recall analysis is advisory and not a required blocking gate.
- **FR-025**: System MUST capture per-stage timing metrics for decode, gating, OCR, and post-processing during analysis runs.
- **FR-026**: Per-stage timing output MUST be emitted only when detailed logging is enabled; when detailed logging is disabled, no per-stage timing output is required.
- **FR-027**: Lightweight timing instrumentation MUST add no more than 2% total runtime overhead on the representative benchmark suite.

### Non-Goals

- No OCR model changes.
- No tolerance policy changes.
- No sampling strategy redesign.
- No sidecar durability policy change.
- No UI redesign.

### Validation Matrix Requirements

- Baseline and candidate MUST run with identical inputs, settings, and environment controls.
- Dataset categories MUST include deterministic synthetic fixtures (numpy-generated frames, curated OCR string lists) and noisy/realistic synthetic fixtures; both MUST be created and committed as deliverables of this feature.
- Outputs MUST include gating diff report, detection parity report, precision/recall comparison (advisory; not a manual blocking gate), and player summary parity comparison.
- Profiling MUST isolate and report hotpath timing for gating math, grayscale conversion behavior, and normalization overhead.
- Profiling MUST include per-stage timing visibility for decode, gating, OCR, and post-processing when detailed logging is enabled.
- Validation MUST include an instrumentation overhead check demonstrating <= 2% runtime overhead on the representative benchmark suite.

### Risk & Mitigation

- Numeric drift risk in OpenCV-native math: mitigate with boundary-focused binary decision parity tests and exhaustive threshold-edge assertions. Intermediate float value differences are acceptable; only accept/skip outcome must match.
- Grayscale reuse behavior drift risk: mitigate with per-frame conversion count assertions and cross-region parity checks.
- Regex semantic drift risk: mitigate with corpus-based normalization equivalence tests and regression snapshots on newline/whitespace edge cases.
- Timing instrumentation drift risk (scope creep or stage misattribution): mitigate with contract tests that assert stage presence/absence by logging mode and fixed stage-name schema (`decode_ms`, `gating_ms`, `ocr_ms`, `post_processing_ms`, `total_ms`).
- Timing overhead-failure risk (SC-013 breach): mitigate with explicit overhead benchmark protocol (warmups, measured runs, median comparison, variance retry). If overhead remains >2% or inconclusive after retry, release decision is NO-GO and fallback action is git revert of optimization commits.

### FR/SC Traceability Matrix

| Requirement Set | Mapped Success Criteria |
| --- | --- |
| FR-001 to FR-003 (gating equivalence/parity) | SC-002, SC-003 |
| FR-004 to FR-006 (single grayscale reuse) | SC-004, SC-005 |
| FR-007 to FR-008 (normalization equivalence) | SC-006 |
| FR-009 to FR-011 (detection/quality/player parity) | SC-003, SC-007, SC-008 |
| FR-012 to FR-014 (compatibility) | SC-009 |
| FR-015 to FR-020 (validation/test coverage) | SC-010, SC-011 |
| FR-021 to FR-024 (risk, deliverables, go/no-go) | SC-011, SC-012 |
| FR-025 to FR-027 (per-stage timing and overhead) | SC-010, SC-013 |

## Key Entities

- **Baseline Run**: Reference execution using current implementation for comparison.
- **Candidate Run**: Execution with the three optimizations enabled for parity/performance validation.
- **Frame-Region Evaluation**: One gating decision for one selected region at one sampled frame.
- **Gating Threshold Configuration**: Existing threshold setting that defines accept/skip boundary semantics.
- **Per-Frame Grayscale Artifact**: Reusable grayscale representation derived once from a sampled frame.
- **Normalization Input/Output Pair**: Raw OCR string and its normalized result used for equivalence comparison.
- **Detection Outcome Record**: Accepted/rejected result and associated metadata for one evaluated candidate.
- **Player Summary Artifact**: Aggregated player-level output produced after analysis.
- **Validation Matrix Execution**: Structured baseline-vs-candidate run set over synthetic deterministic and noisy in-repo fixture sets with parity and profiling outputs.
- **Synthetic Fixture Set**: In-repo numpy-generated frame arrays and curated OCR string lists created as deliverables of this feature for deterministic and noisy validation scenarios.
- **Go/No-Go Evidence Pack**: Collected reports proving or disproving mandatory parity/non-regression gates.
- **Per-Stage Timing Summary**: Decode, gating, OCR, and post-processing timing totals produced when detailed logging is enabled.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Runtime Gain)**: Candidate median total analysis runtime MUST improve by at least 15% versus baseline on the representative benchmark suite (mock video/OCR, 4 regions × 100 sampled frames, 5 warm runs, median time); pass if improvement >= 15%, fail otherwise.
- **SC-002 (Gating Decision Parity)**: Frame-region accept/skip gating decisions MUST match baseline at 100.00% parity over deterministic and noisy validation sets; pass only if decision mismatches = 0. Intermediate float diff values are not required to match baseline.
- **SC-003 (Detection Parity)**: Accepted/rejected detection outcomes MUST match baseline exactly at 100.00% parity for identical inputs/settings; pass only if mismatches = 0.
- **SC-004 (One-Grayscale Constraint)**: Grayscale conversion count MUST be <= sampled-frame count and MUST equal sampled-frame count when gating is active; pass if no per-region recomputation is observed.
- **SC-005 (Gating Hotpath Efficiency)**: Median per frame-region gating compute time MUST improve by at least 20% versus baseline; pass if improvement >= 20%.
- **SC-006 (Normalization Equivalence)**: Normalized output strings MUST be exactly equal to baseline for 100.00% of validation corpus entries; pass only if mismatches = 0.
- **SC-007 (Precision/Recall Non-Regression)**: Precision and recall MUST be validated by an automated pytest regression test; blocking only if that automated test fails. Manual analysis of precision/recall is not a required blocking gate. Report is produced and retained as advisory evidence.
- **SC-008 (Player Summary Parity)**: Player summary outputs MUST be identical to baseline for all validation runs (identity/count/order semantics); pass only if mismatches = 0.
- **SC-009 (Compatibility)**: Existing public APIs/signatures, logging semantics, and settings semantics MUST remain backward-compatible as proven by compatibility test suite; pass only if compatibility tests report zero failures.
- **SC-010 (Validation Matrix Completeness)**: Validation matrix MUST execute baseline and candidate across synthetic deterministic and noisy in-repo fixture sets (created as feature deliverables) and produce gating diff plus profiling reports; pass only if all required reports are generated and complete.
- **SC-011 (Test Suite Gate)**: All required unit, integration, and performance tests for the three optimization points MUST pass in CI/local validation; pass only if zero failing required tests.
- **SC-012 (Final Go/No-Go Gate)**: Release is GO only if SC-001, SC-002, SC-003, SC-006, SC-008, SC-009, SC-010, SC-011, and SC-013 all pass simultaneously; SC-007 is binding only if its automated pytest regression test fails (manual precision/recall analysis is not a blocking gate); otherwise decision is NO-GO with fallback activation.
- **SC-013 (Timing Instrumentation Overhead)**: Per-stage timing instrumentation MUST add no more than 2% total runtime overhead on the representative benchmark suite; pass if overhead <= 2%, fail otherwise. Benchmark protocol: use the SC-001 representative suite, run 5 warmup iterations and 10 measured iterations per mode, compare median runtime with instrumentation enabled vs disabled, compute `overhead_pct = ((enabled_median - disabled_median) / disabled_median) * 100`, and mark result inconclusive (NO-GO) if variance exceeds 10% after one retry.

## Assumptions

- Existing baseline behavior is the authoritative reference for parity checks.
- Input videos/datasets used in validation are synthetic in-repo fixtures (numpy-generated frames and curated OCR string lists) created and committed as deliverables of this feature, ensuring full reproducibility and CI stability without external video files or network access.
- Runtime benchmarks are executed under controlled conditions to reduce environmental variance.
- Required reports (gating diff, parity comparisons, profiling summaries) are retained as evidence for release gating.
- Rollout will begin with controlled validation scope before broader use; if any no-go condition is triggered, fallback is git revert of the optimization commits (no feature toggle needed given the absence of API, schema, or settings changes).