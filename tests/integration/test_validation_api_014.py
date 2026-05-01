"""Integration test for candidate RSI validation API (T024)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.web.api.routes.review_actions import ReviewActionsHandler
from src.web.api.routes.review_sessions import ReviewSessionHandler
from src.web.app.session_manager import SessionManager


def _setup_session(tmp_path: Path) -> tuple[str, SessionManager]:
    csv_path = tmp_path / "result_latest.csv"
    csv_path.write_text(
        "#schema_version=1.0\nPlayerName,StartTimestamp\nRocketJockey,5.0\n",
        encoding="utf-8",
    )
    manager = SessionManager()
    handler = ReviewSessionHandler(session_manager=manager)
    _, body = handler.post_load({"csv_path": str(csv_path)})
    session_id = body["session_id"]

    state = manager.get(session_id)
    assert state is not None
    payload = dict(state.payload or {})
    candidate = {
        "candidate_id": "c_rocketjockey",
        "extracted_name": "RocketJockey",
        "status": "pending",
        "normalized_name": "rocketjockey",
    }
    payload["candidates"] = [candidate]
    payload["candidates_original"] = [candidate]
    payload["validation_outcomes"] = {}
    manager.upsert(session_id, state.csv_path, payload)
    return session_id, manager


def _make_http_response(status_code: int):
    from unittest.mock import MagicMock
    resp = MagicMock()
    resp.status = status_code
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestValidateCandidateEndpoint:
    def test_post_validate_candidate_found(self, tmp_path: Path) -> None:
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            status, body = actions.post_validate_candidate(
                session_id, "c_rocketjockey", {"spelling": "RocketJockey"}
            )

        assert status == 200
        assert body["state"] == "found"
        assert body["candidate_id"] == "c_rocketjockey"
        assert body["spelling"] == "RocketJockey"
        assert body["source"] == "manual_review"
        assert body["checked_at"] is not None

    def test_post_validate_candidate_not_found(self, tmp_path: Path) -> None:
        import urllib.error
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        def fake_urlopen(req, timeout):
            raise urllib.error.HTTPError(url=None, code=404, msg="Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]

        with patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen):
            status, body = actions.post_validate_candidate(
                session_id, "c_rocketjockey", {"spelling": "RocketJockey"}
            )

        assert status == 200
        assert body["state"] == "not_found"

    def test_post_validate_persists_outcome_to_sidecar(self, tmp_path: Path) -> None:
        import json
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            actions.post_validate_candidate(
                session_id, "c_rocketjockey", {"spelling": "RocketJockey"}
            )

        state = manager.get(session_id)
        assert state is not None
        outcomes = state.payload.get("validation_outcomes", {})
        assert "rocketjockey" in outcomes
        assert outcomes["rocketjockey"]["state"] == "found"

    def test_post_validate_candidate_missing_spelling_uses_candidate_fallback(self, tmp_path: Path) -> None:
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        status, body = actions.post_validate_candidate(
            session_id, "c_rocketjockey", {}
        )
        assert status == 200
        assert body["candidate_id"] == "c_rocketjockey"
        assert body["spelling"] == "RocketJockey"

    def test_post_validate_candidate_unknown_session_returns_404(self, tmp_path: Path) -> None:
        _, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        status, body = actions.post_validate_candidate(
            "nonexistent_session", "c_rocketjockey", {"spelling": "RocketJockey"}
        )
        assert status == 404

    def test_post_validate_candidate_overwrites_previous_outcome(self, tmp_path: Path) -> None:
        """Second recheck for same candidate should overwrite previous result."""
        import urllib.error
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        # First check: found
        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            actions.post_validate_candidate(
                session_id, "c_rocketjockey", {"spelling": "RocketJockey"}
            )

        # Second check: not found
        def fake_404(req, timeout):
            raise urllib.error.HTTPError(url=None, code=404, msg="Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]

        with patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_404):
            status, body = actions.post_validate_candidate(
                session_id, "c_rocketjockey", {"spelling": "RocketJockey"}
            )

        assert body["state"] == "not_found"
        state = manager.get(session_id)
        assert state is not None
        assert state.payload["validation_outcomes"]["rocketjockey"]["state"] == "not_found"

    def test_post_validate_prefers_corrected_text_for_edited_candidate(self, tmp_path: Path) -> None:
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        state = manager.get(session_id)
        assert state is not None
        payload = dict(state.payload or {})
        payload["candidates"] = [
            {
                "candidate_id": "c_rocketjockey",
                "extracted_name": "RocketJockey",
                "corrected_text": "RocketJockeyFixed",
                "status": "pending",
            }
        ]
        manager.upsert(session_id, state.csv_path, payload)

        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            status, body = actions.post_validate_candidate(
                session_id,
                "c_rocketjockey",
                {"spelling": "RocketJockey"},
            )

        assert status == 200
        assert body["spelling"] == "RocketJockeyFixed"

    def test_post_validate_does_not_treat_null_corrected_text_as_literal_none(self, tmp_path: Path) -> None:
        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        state = manager.get(session_id)
        assert state is not None
        payload = dict(state.payload or {})
        payload["candidates"] = [
            {
                "candidate_id": "c_rocketjockey",
                "extracted_name": "RocketJockey",
                "corrected_text": None,
                "status": "pending",
            }
        ]
        manager.upsert(session_id, state.csv_path, payload)

        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            status, body = actions.post_validate_candidate(
                session_id,
                "c_rocketjockey",
                {"spelling": "RocketJockey"},
            )

        assert status == 200
        assert body["spelling"] == "RocketJockey"
        outcomes = manager.get(session_id).payload.get("validation_outcomes", {})
        assert "rocketjockey" in outcomes
        assert "none" not in outcomes

    def test_post_validate_preserves_persisted_candidate_decisions(self, tmp_path: Path) -> None:
        from src.web.app.review_sidecar_store import ReviewSidecarStore

        session_id, manager = _setup_session(tmp_path)
        actions = ReviewActionsHandler(session_manager=manager)

        state = manager.get(session_id)
        assert state is not None
        persisted_payload = {
            "source_type": "local_file",
            "source_value": str(state.csv_path),
            "candidates": list(state.payload.get("candidates", [])),
            "candidate_decisions": {
                "c_rocketjockey": {
                    "decision": "unreviewed",
                    "marked_new": False,
                    "corrected_text": "RocketJockeyFixed",
                }
            },
            "validation_outcomes": {},
        }
        store = ReviewSidecarStore()
        store.save(state.csv_path, persisted_payload)

        with patch(
            "src.services.validation_service.urllib.request.urlopen",
            return_value=_make_http_response(200),
        ):
            status, _ = actions.post_validate_candidate(
                session_id,
                "c_rocketjockey",
                {"spelling": "RocketJockey"},
            )

        assert status == 200
        reloaded = store.load(state.csv_path)
        assert reloaded is not None
        assert reloaded.get("candidate_decisions", {}).get("c_rocketjockey", {}).get("corrected_text") == "RocketJockeyFixed"
