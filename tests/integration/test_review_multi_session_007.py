from __future__ import annotations

from src.web.app.session_manager import SessionManager


def test_multi_session_switching_and_state_isolation() -> None:
    manager = SessionManager()
    manager.upsert("s1", "a.csv", {"candidates": [{"candidate_id": "c1", "status": "pending"}]})
    manager.upsert("s2", "b.csv", {"candidates": [{"candidate_id": "c2", "status": "confirmed"}]})

    state1 = manager.switch_session("s1")
    assert state1 is not None
    assert state1.payload["candidates"][0]["candidate_id"] == "c1"

    state2 = manager.switch_session("s2")
    assert state2 is not None
    assert state2.payload["candidates"][0]["candidate_id"] == "c2"
