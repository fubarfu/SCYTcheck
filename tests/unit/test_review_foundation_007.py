from __future__ import annotations

import json
from pathlib import Path

from src.web.app.frame_asset_store import FrameAssetStore
from src.web.app.result_schema_validator import ResultSchemaValidator
from src.web.app.review_sidecar_store import ReviewSidecarStore


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    content = "\n".join([",".join(row) for row in rows]) + "\n"
    path.write_text(content, encoding="utf-8")


def test_result_schema_validator_accepts_valid_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "valid.csv"
    _write_csv(csv_path, [["PlayerName", "StartTimestamp"], ["Alice", "00:00:03"]])

    validator = ResultSchemaValidator()
    result = validator.validate(csv_path)

    assert result.is_valid is True
    assert result.schema_version == "1.0"
    assert result.missing_columns == ()


def test_result_schema_validator_rejects_missing_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid.csv"
    _write_csv(csv_path, [["PlayerName"], ["Alice"]])

    validator = ResultSchemaValidator()
    result = validator.validate(csv_path)

    assert result.is_valid is False
    assert result.error == "Missing required CSV columns"
    assert result.missing_columns == ("StartTimestamp",)


def test_review_sidecar_store_atomic_write_and_load(tmp_path: Path) -> None:
    csv_path = tmp_path / "result.csv"
    csv_path.write_text("PlayerName,StartTimestamp\n", encoding="utf-8")

    store = ReviewSidecarStore()
    payload = {
        "session_id": "sess_1",
        "source_value": "https://youtube.com/watch?v=abc123",
        "candidates": [{"id": "cand_1"}],
    }

    sidecar_path = store.save(csv_path, payload)

    assert sidecar_path.exists()
    assert sidecar_path.name == "review_state.json"
    assert sidecar_path.parent.name.startswith("vid_")
    loaded = store.load(csv_path)
    assert loaded is not None
    assert loaded["session_id"] == payload["session_id"]
    assert loaded["candidates"] == payload["candidates"]
    assert loaded["result_csv_path"] == str(csv_path)

    # Ensure no leftover temporary files after atomic replace
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []

    on_disk = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert on_disk["session_id"] == "sess_1"


def test_frame_asset_store_uses_workspace_frames_folder_when_provided(tmp_path: Path) -> None:
    csv_path = tmp_path / "result.csv"
    workspace_path = tmp_path / ".scyt_review_workspaces" / "vid_123"
    store = FrameAssetStore(cache_root=tmp_path / "thumb-cache")

    frame_path = store.persisted_frame_path(csv_path, "cand_1", workspace_path=workspace_path)

    assert frame_path == workspace_path / "frames" / "cand_1.png"
