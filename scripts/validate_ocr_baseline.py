from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _load_names(path: Path) -> set[str]:
    names: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            value = (row.get("PlayerName") or "").strip()
            if value:
                names.add(value)
    return names


def compare(
    baseline_csv: Path,
    candidate_csv: Path,
    expected_csv: Path | None,
) -> dict[str, int | float]:
    baseline_names = _load_names(baseline_csv)
    candidate_names = _load_names(candidate_csv)
    expected_names = _load_names(expected_csv) if expected_csv else set()

    baseline_missed = len(expected_names - baseline_names) if expected_names else 0
    candidate_missed = len(expected_names - candidate_names) if expected_names else 0

    baseline_false_pos = len(baseline_names - expected_names) if expected_names else 0
    candidate_false_pos = len(candidate_names - expected_names) if expected_names else 0

    baseline_total_error = baseline_missed + baseline_false_pos
    candidate_total_error = candidate_missed + candidate_false_pos

    reduction_percent = 0.0
    if baseline_total_error > 0:
        reduction_percent = (
            (baseline_total_error - candidate_total_error) / baseline_total_error
        ) * 100.0

    return {
        "baseline_missed": baseline_missed,
        "candidate_missed": candidate_missed,
        "baseline_false_positives": baseline_false_pos,
        "candidate_false_positives": candidate_false_pos,
        "baseline_total_error": baseline_total_error,
        "candidate_total_error": candidate_total_error,
        "error_reduction_percent": round(reduction_percent, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare OCR baseline and candidate CSV outputs"
    )
    parser.add_argument(
        "--baseline", required=True, type=Path, help="Path to baseline summary CSV"
    )
    parser.add_argument(
        "--candidate", required=True, type=Path, help="Path to candidate summary CSV"
    )
    parser.add_argument(
        "--expected",
        required=False,
        type=Path,
        help="Optional path to expected names CSV (PlayerName column)",
    )
    args = parser.parse_args()

    results = compare(args.baseline, args.candidate, args.expected)
    for key, value in results.items():
        print(f"{key},{value}")


if __name__ == "__main__":
    main()
