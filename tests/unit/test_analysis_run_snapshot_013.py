from __future__ import annotations

import json
from pathlib import Path

from src.web.api.routes.analysis import AnalysisHandler
from src.web.app.review_sidecar_store import ReviewSidecarStore


def test_next_run_index_prefers_existing_sidecars_and_metadata(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)

    # Existing snapshots indicate run indexes 0 and 1 already exist.
    (workspace / "result_0.review.json").write_text("{}", encoding="utf-8")
    (workspace / "result_1.review.json").write_text("{}", encoding="utf-8")

    # Metadata can be stale; next index should still append after existing snapshots.
    assert AnalysisHandler._next_run_index(workspace, prior_run_count=1) == 2

    # Metadata can also be ahead of sidecars; next index should remain monotonic.
    assert AnalysisHandler._next_run_index(workspace, prior_run_count=5) == 5


def test_persist_run_snapshot_creates_per_run_csv_and_sidecar(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)

    exported_csv = workspace / "result_latest.csv"
    exported_csv.write_text("PlayerName,StartTimestamp\nAlice,00:00:01\n", encoding="utf-8")

    review_state_path = ReviewSidecarStore.workspace_review_state_path(workspace)
    review_state_payload = {
        "source_type": "youtube_url",
        "source_value": "https://youtube.com/watch?v=abc",
        "candidates": [{"candidate_id": "cand_1", "extracted_name": "Alice"}],
        "result_csv_path": str(exported_csv),
    }
    review_state_path.write_text(
        json.dumps(review_state_payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    AnalysisHandler._persist_run_snapshot(exported_csv, workspace, run_index=3)

    run_csv = workspace / "result_3.csv"
    run_sidecar = workspace / "result_3.review.json"

    assert run_csv.exists()
    assert run_sidecar.exists()

    snapshot_payload = json.loads(run_sidecar.read_text(encoding="utf-8"))
    assert snapshot_payload["result_csv_path"] == str(run_csv)
    assert snapshot_payload["candidates"][0]["candidate_id"] == "cand_1"


def test_backfill_latest_snapshot_if_missing_for_legacy_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)

    latest_csv = workspace / "result_latest.csv"
    latest_csv.write_text("PlayerName,StartTimestamp\nAlice,00:00:01\n", encoding="utf-8")

    review_state_path = ReviewSidecarStore.workspace_review_state_path(workspace)
    review_state_payload = {
        "source_type": "youtube_url",
        "source_value": "https://youtube.com/watch?v=abc",
        "candidates": [{"candidate_id": "cand_legacy", "extracted_name": "Alice"}],
        "result_csv_path": str(latest_csv),
    }
    review_state_path.write_text(
        json.dumps(review_state_payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    AnalysisHandler._backfill_latest_snapshot_if_missing(workspace, prior_run_count=2)

    prior_csv = workspace / "result_1.csv"
    prior_sidecar = workspace / "result_1.review.json"

    assert prior_csv.exists()
    assert prior_sidecar.exists()

    payload = json.loads(prior_sidecar.read_text(encoding="utf-8"))
    assert payload["result_csv_path"] == str(prior_csv)
    assert payload["candidates"][0]["candidate_id"] == "cand_legacy"


def test_backfill_does_not_overwrite_existing_snapshot(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)

    latest_csv = workspace / "result_latest.csv"
    latest_csv.write_text("PlayerName,StartTimestamp\nAlice,00:00:01\n", encoding="utf-8")

    review_state_path = ReviewSidecarStore.workspace_review_state_path(workspace)
    review_state_path.write_text(json.dumps({"candidates": []}, ensure_ascii=True, indent=2), encoding="utf-8")

    existing_sidecar = workspace / "result_1.review.json"
    existing_payload = {"candidates": [{"candidate_id": "existing"}], "result_csv_path": "existing.csv"}
    existing_sidecar.write_text(json.dumps(existing_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    AnalysisHandler._backfill_latest_snapshot_if_missing(workspace, prior_run_count=2)

    payload_after = json.loads(existing_sidecar.read_text(encoding="utf-8"))
    assert payload_after["candidates"][0]["candidate_id"] == "existing"


def test_backfill_uses_legacy_nested_review_state_when_top_level_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)

    latest_csv = workspace / "result_latest.csv"
    latest_csv.write_text("PlayerName,StartTimestamp\nAlice,00:00:01\n", encoding="utf-8")

    legacy_dir = workspace / ".scyt_review_workspaces"
    legacy_dir.mkdir(parents=True)
    legacy_review_state = legacy_dir / "review_state.json"
    legacy_review_state.write_text(
        json.dumps(
            {
                "candidates": [{"candidate_id": "cand_legacy_nested", "extracted_name": "Alice"}],
                "result_csv_path": str(latest_csv),
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    AnalysisHandler._backfill_latest_snapshot_if_missing(workspace, prior_run_count=2)

    prior_sidecar = workspace / "result_1.review.json"
    assert prior_sidecar.exists()
    payload = json.loads(prior_sidecar.read_text(encoding="utf-8"))
    assert payload["candidates"][0]["candidate_id"] == "cand_legacy_nested"
