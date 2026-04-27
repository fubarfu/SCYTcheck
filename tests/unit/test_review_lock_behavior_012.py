from __future__ import annotations

from src.web.app.review_lock_service import ReviewLockService


def test_single_writer_lock_enforces_readonly_for_non_owner() -> None:
    lock = ReviewLockService()
    owner = lock.acquire("vid_1", "sess_owner")
    viewer = lock.acquire("vid_1", "sess_viewer")

    assert owner["readonly"] is False
    assert viewer["readonly"] is True
    assert viewer["owner_session_id"] == "sess_owner"


def test_lock_service_returns_workspace_locked_error() -> None:
    lock = ReviewLockService()
    lock.acquire("vid_2", "sess_owner")

    can_write, err = lock.ensure_writable("vid_2", "sess_other")

    assert can_write is False
    assert err is not None
    assert err["error"] == "workspace_locked"
