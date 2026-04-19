# Quickstart: Optimize Analysis Hotpaths

**Feature**: 006-optimize-analysis-hotpaths  
**Branch**: feature/008-improve-analysis-speed

---

## Scope

This feature delivers:

1. OpenCV-native gating diff computation.
2. Single grayscale conversion reuse per sampled frame.
3. Precompiled regex normalization.
4. Per-stage timing output (decode, gating, OCR, post-processing) emitted only when detailed logging is enabled.

---

## Enable Timing Output

Timing output is intentionally conditional.

1. Open app advanced settings.
2. Enable detailed sidecar logging.
3. Run analysis normally.
4. Confirm timing summary appears in logging-enabled output path.

When detailed logging is disabled, per-stage timing output should not be emitted.

---

## Validate Core Parity + Performance

```powershell
cd C:\Users\SteSt\source\SCYTcheck
.venv\Scripts\Activate.ps1
pytest tests/unit/test_hotpath_gating_parity.py tests/unit/test_hotpath_normalization_parity.py -q --tb=short -W ignore
pytest tests/integration/test_hotpath_player_summary_parity.py tests/integration/test_precision_recall_regression.py -q --tb=short -W ignore
pytest tests/integration/test_hotpath_performance.py -v -s --tb=short -W ignore
python scripts/validate_hotpaths.py
```

Expected:

- Decision/detection/player-summary parity tests pass.
- SC-001 and SC-005 performance checks pass (or skip only under documented variance condition).
- Validation report generated at `specs/006-optimize-analysis-hotpaths/validation_report.json`.

---

## Validate Timing Instrumentation Rules

1. Logging disabled run:
  - No per-stage timing output emitted.
2. Logging enabled run:
  - Timing output includes decode, gating, OCR, post-processing.
3. Overhead gate:
  - Instrumentation overhead must be <= 2% on representative benchmark suite (SC-013).

---

## Regression Safety

Run broader regression before release:

```powershell
pytest tests/unit/ -q --tb=short -W ignore
pytest tests/integration/ -q --tb=short -W ignore
```

---

## Rollback

Objective rollback trigger matrix:

| Trigger | Condition | Decision | Action |
| --- | --- | --- | --- |
| Parity failure | Any mismatch in SC-002/SC-003/SC-006/SC-008 evidence | NO-GO | `git revert <optimization-commit-sha>` |
| Non-regression test failure | Automated SC-007 pytest gate fails | NO-GO | `git revert <optimization-commit-sha>` |
| Timing overhead failure | SC-013 overhead > 2.0% after defined retry protocol | NO-GO | `git revert <optimization-commit-sha>` |
| Timing overhead inconclusive | Variance remains > 10% after one retry in SC-013 protocol | NO-GO | `git revert <optimization-commit-sha>` |
| Compatibility failure | SC-009 compatibility test suite reports any failure | NO-GO | `git revert <optimization-commit-sha>` |

If parity/non-regression/overhead gates fail in rollout:

```powershell
git revert <optimization-commit-sha>
git push
```

No feature toggle is required by design.
