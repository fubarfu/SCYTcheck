from __future__ import annotations

from pathlib import Path

from src.web.api.routes.review_sessions import ReviewSessionHandler


def test_malformed_csv_is_rejected_by_schema_gate(tmp_path: Path) -> None:
    bad_csv = tmp_path / "malformed.csv"
    bad_csv.write_text("foo,bar\n1,2\n", encoding="utf-8")

    handler = ReviewSessionHandler()
    status, body = handler.post_load({"csv_path": str(bad_csv)})
    assert status == 422
    assert body["error"] == "invalid_schema"
