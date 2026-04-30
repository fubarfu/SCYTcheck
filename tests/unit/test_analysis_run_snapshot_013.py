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
