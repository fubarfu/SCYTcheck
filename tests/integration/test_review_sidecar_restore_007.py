from __future__ import annotations

import json
from pathlib import Path

from src.web.api.routes.review_sessions import ReviewSessionHandler


def test_sidecar_restore_after_reopen(tmp_path: Path) -> None:
    csv_path = tmp_path / "restore.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nAlice,1\n", encoding="utf-8"
    )
    sidecar_path = csv_path.with_suffix(".review.json")
    sidecar_payload = {
        "source_type": "youtube_url",
        "source_value": "https://youtube.com/watch?v=abc",
        "candidates": [{"candidate_id": "c1", "extracted_name": "Alice", "status": "confirmed"}],
    }
    sidecar_path.write_text(json.dumps(sidecar_payload), encoding="utf-8")

    handler = ReviewSessionHandler()
    status, body = handler.post_load({"csv_path": str(csv_path)})
    assert status == 200
    session_id = body["session_id"]

    _, session = handler.get_session(session_id)
    assert session["source_type"] == "youtube_url"
    assert session["candidates"][0]["status"] == "confirmed"
