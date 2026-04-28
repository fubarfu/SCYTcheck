from __future__ import annotations

from pathlib import Path

from src.web.app.history_store import derive_review_artifacts
from src.web.app.review_sidecar_store import ReviewSidecarStore


def test_reopen_resolution_ready_when_csv_and_sidecar_present(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    ReviewSidecarStore().save(
        csv_path,
        {
            "source_value": "https://youtube.com/watch?v=abc123",
            "candidates": [],
            "action_history": [],
        },
    )

    resolved = derive_review_artifacts(output)
    assert resolved["resolution_status"] == "ready"
    assert resolved["primary_csv_path"] == str(csv_path)


def test_reopen_resolution_still_supports_legacy_csv_adjacent_sidecar(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    csv_path.with_suffix(".review.json").write_text("{}", encoding="utf-8")

    resolved = derive_review_artifacts(output)
    assert resolved["resolution_status"] == "ready"
    assert resolved["primary_csv_path"] == str(csv_path)


def test_reopen_resolution_partial_when_sidecar_missing(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    csv_path = output / "result.csv"
    csv_path.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")

    resolved = derive_review_artifacts(output)
    assert resolved["resolution_status"] == "partial"
    assert resolved["resolved_csv_paths"] == [str(csv_path)]


def test_reopen_resolution_missing_results(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    resolved = derive_review_artifacts(output)
    assert resolved["resolution_status"] == "missing_results"


def test_reopen_resolution_missing_folder(tmp_path: Path) -> None:
    resolved = derive_review_artifacts(tmp_path / "does-not-exist")
    assert resolved["resolution_status"] == "missing_folder"


def test_reopen_resolution_prefers_requested_csv_when_present(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    first = output / "result_a.csv"
    second = output / "result_b.csv"
    first.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nA,1\n", encoding="utf-8")
    second.write_text("#schema_version=1.0\nPlayerName,StartTimestamp\nB,2\n", encoding="utf-8")

    resolved = derive_review_artifacts(output, preferred_csv_path=str(first))
    assert resolved["primary_csv_path"] == str(first)
    assert resolved["resolved_csv_paths"][0] == str(first)
