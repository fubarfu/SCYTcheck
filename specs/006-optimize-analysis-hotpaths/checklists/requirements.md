# Requirements Coverage Checklist: 006 Optimize Analysis Hotpaths

Purpose: Map every functional requirement (FR-001..FR-024) to implementation and automated validation artifacts.

## Functional Requirement Coverage

- [x] FR-001 Gating diff uses optimized OpenCV-native operations with parity-preserving behavior.
- [x] FR-002 Binary gating decision parity preserved for identical inputs.
- [x] FR-003 Shape-mismatch handling semantics preserved.
- [x] FR-004 One grayscale conversion per sampled frame with reuse across regions.
- [x] FR-005 No redundant per-region grayscale recomputation when reusable grayscale exists.
- [x] FR-006 Gating threshold/per-region behavior preserved with grayscale reuse.
- [x] FR-007 Regex compilation overhead removed via precompiled whitespace patterns.
- [x] FR-008 Normalization outputs remain equivalent to baseline.
- [x] FR-009 Accepted/rejected detection decisions preserved for identical inputs/settings.
- [x] FR-010 Precision/recall non-regression validated by automated pytest gate.
- [x] FR-011 Player summary identity/count/order semantics preserved.
- [x] FR-012 Public API/signature compatibility preserved for existing callers.
- [x] FR-013 Logging semantics and downstream-compatible field meanings preserved.
- [x] FR-014 Settings compatibility preserved (keys/default semantics retained at persistence boundary).
- [x] FR-015 Validation matrix implemented using committed synthetic fixtures.
- [x] FR-016 Validation matrix emits gating parity/decision report in JSON output.
- [x] FR-017 Validation matrix includes hotpath profiling medians and conversion-count checks.
- [x] FR-018 Unit coverage includes gating parity, grayscale reuse, and normalization equivalence.
- [x] FR-019 Integration coverage includes detection parity and player summary parity checks.
- [x] FR-020 Performance coverage includes hotpath and runtime threshold gates.
- [x] FR-021 Numeric/grayscale/regex drift risks documented and mitigated in feature artifacts.
- [x] FR-022 Deliverables produced: updated spec artifacts, checklist, validation script/report, fallback plan references.
- [x] FR-023 Rollback trigger/fallback documented as git revert on failed parity/non-regression gates.
- [x] FR-024 Final go/no-go driven by automated test evidence for mandatory criteria.
- [x] FR-025 Per-stage timing metrics captured for decode/gating/OCR/post-processing.
- [x] FR-026 Per-stage timing output emitted only when detailed logging is enabled.
- [x] FR-027 Timing instrumentation overhead constrained to <=2% with explicit benchmark protocol.

## Primary Evidence Links

- Gating parity + grayscale reuse tests: tests/unit/test_hotpath_gating_parity.py
- Normalization parity tests: tests/unit/test_hotpath_normalization_parity.py
- Performance gates: tests/integration/test_hotpath_performance.py
- Precision/recall gate: tests/integration/test_precision_recall_regression.py
- Player summary parity gate: tests/integration/test_hotpath_player_summary_parity.py
- Validation matrix script: scripts/validate_hotpaths.py
- Validation report artifact: specs/006-optimize-analysis-hotpaths/validation_report.json

## Sign-off

Verified 2026-04-18 by automated tests, validation matrix execution, and timing-overhead protocol definition.
