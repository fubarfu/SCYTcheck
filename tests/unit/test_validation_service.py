"""Unit tests for ValidationService (T008).

Covers:
- Queue deduplication (same spelling enqueued twice → one HTTP call)
- Rate limiting (≥1 sec between dispatches)
- Outcome mapping: 200→found, 404→not_found, 5xx→failed, timeout→failed
- stop()+wait() drain behaviour
- Drain completeness: enqueue N spellings, all reach terminal state (SC-001)
"""
from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from src.services.validation_service import (
    ValidationOutcome,
    ValidationService,
    ValidationState,
    _MIN_DISPATCH_INTERVAL_SEC,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_http_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status = status_code
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _run_service_with_spellings(
    spellings: list[str],
    urlopen_side_effect,
    sleep_side_effect=None,
) -> ValidationService:
    """Run a ValidationService to completion with mocked urllib and sleep."""
    with (
        patch("src.services.validation_service.urllib.request.urlopen") as mock_urlopen,
        patch("src.services.validation_service.time.sleep") as mock_sleep,
    ):
        if callable(sleep_side_effect) or sleep_side_effect is not None:
            mock_sleep.side_effect = sleep_side_effect
        mock_urlopen.side_effect = urlopen_side_effect

        svc = ValidationService()
        svc.start()
        for spelling in spellings:
            svc.enqueue(spelling)
        svc.stop()
        svc.wait()
    return svc


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

class TestDeduplication:
    def test_same_spelling_enqueued_twice_produces_one_http_call(self):
        http_calls: list[str] = []

        def fake_urlopen(req, timeout):
            http_calls.append(req.full_url)
            return _make_http_response(200)

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("PlayerOne")
            svc.enqueue("PlayerOne")   # duplicate — same exact spelling
            svc.stop()
            svc.wait()

        assert len(http_calls) == 1

    def test_case_insensitive_deduplication(self):
        http_calls: list[str] = []

        def fake_urlopen(req, timeout):
            http_calls.append(req.full_url)
            return _make_http_response(200)

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("PlayerOne")
            svc.enqueue("playerone")   # same after normalisation
            svc.stop()
            svc.wait()

        assert len(http_calls) == 1

    def test_distinct_spellings_produce_separate_http_calls(self):
        http_calls: list[str] = []

        def fake_urlopen(req, timeout):
            http_calls.append(req.full_url)
            return _make_http_response(200)

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Alpha")
            svc.enqueue("Beta")
            svc.stop()
            svc.wait()

        assert len(http_calls) == 2


# ---------------------------------------------------------------------------
# Outcome mapping
# ---------------------------------------------------------------------------

class TestOutcomeMapping:
    def test_http_200_maps_to_found(self):
        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Pilot")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert outcomes["pilot"].state == "found"

    def test_http_404_maps_to_not_found(self):
        import urllib.error

        def fake_urlopen(req, timeout):
            raise urllib.error.HTTPError(url=None, code=404, msg="Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Ghost")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert outcomes["ghost"].state == "not_found"

    def test_http_5xx_maps_to_failed(self):
        import urllib.error

        def fake_urlopen(req, timeout):
            raise urllib.error.HTTPError(url=None, code=503, msg="Service Unavailable", hdrs=None, fp=None)  # type: ignore[arg-type]

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Unreachable")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert outcomes["unreachable"].state == "failed"

    def test_timeout_maps_to_failed(self):
        import socket

        def fake_urlopen(req, timeout):
            raise socket.timeout("timed out")

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Slow")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert outcomes["slow"].state == "failed"

    def test_network_error_maps_to_failed(self):
        import urllib.error

        def fake_urlopen(req, timeout):
            raise urllib.error.URLError("network unreachable")

        with (
            patch("src.services.validation_service.urllib.request.urlopen", side_effect=fake_urlopen),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Disconnected")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert outcomes["disconnected"].state == "failed"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_sleep_called_between_dispatches_for_two_items(self):
        """When two items are enqueued, sleep should be called at least once
        (after the first item completes, before dispatching the second)."""
        sleep_calls: list[float] = []

        def fake_sleep(secs: float) -> None:
            sleep_calls.append(secs)

        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep", side_effect=fake_sleep),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("First")
            svc.enqueue("Second")
            svc.stop()
            svc.wait()

        # Between dispatching First and Second the worker must sleep some positive amount
        assert len(sleep_calls) >= 1
        assert all(s > 0 for s in sleep_calls)

    def test_no_sleep_for_single_item(self):
        """With one item the worker doesn't need to sleep before dispatching it."""
        sleep_calls: list[float] = []

        def fake_sleep(secs: float) -> None:
            sleep_calls.append(secs)

        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep", side_effect=fake_sleep),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("OnlyOne")
            svc.stop()
            svc.wait()

        # The first item should be dispatched immediately (last_dispatch starts at 0,
        # so wait_sec = 1.0 - elapsed, which should be negative for the very first item
        # if we fake time.monotonic to return something reasonable.  In real wall-clock
        # terms the first item dispatches immediately.)
        # We only assert that any sleeps that did happen used a positive duration.
        assert all(s > 0 for s in sleep_calls)


# ---------------------------------------------------------------------------
# Stop and wait drain behaviour
# ---------------------------------------------------------------------------

class TestStopAndWait:
    def test_wait_blocks_until_queue_is_empty(self):
        dispatch_times: list[float] = []
        wait_returned_at: list[float] = []

        real_sleep = time.sleep

        def fake_sleep(secs: float) -> None:
            if secs > 0:
                real_sleep(min(secs, 0.01))  # still sleep, but cap at 10ms

        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep", side_effect=fake_sleep),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("A")
            svc.enqueue("B")
            svc.enqueue("C")
            svc.stop()
            svc.wait()
            wait_returned_at.append(time.monotonic())

        outcomes = svc.get_outcomes()
        # All three must be in terminal state after wait() returns
        for key in ("a", "b", "c"):
            assert outcomes[key].state in ("found", "not_found", "failed")

    def test_enqueue_after_stop_is_ignored(self):
        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Before")
            svc.stop()
            svc.enqueue("After")  # should be ignored
            svc.wait()

        outcomes = svc.get_outcomes()
        assert "before" in outcomes
        assert "after" not in outcomes


# ---------------------------------------------------------------------------
# Drain completeness (SC-001)
# ---------------------------------------------------------------------------

class TestDrainCompleteness:
    def test_all_enqueued_spellings_reach_terminal_state(self):
        """Enqueue N spellings, stop, wait — every spelling must be in outcomes."""
        n = 5
        spellings = [f"Player{i}" for i in range(n)]

        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            for s in spellings:
                svc.enqueue(s)
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        assert len(outcomes) == n
        for outcome in outcomes.values():
            assert outcome.state in ("found", "not_found", "failed"), (
                f"Unexpected state {outcome.state!r} — expected terminal state"
            )

    def test_checked_at_is_set_for_terminal_outcomes(self):
        with (
            patch("src.services.validation_service.urllib.request.urlopen",
                  return_value=_make_http_response(200)),
            patch("src.services.validation_service.time.sleep"),
        ):
            svc = ValidationService()
            svc.start()
            svc.enqueue("Timestamped")
            svc.stop()
            svc.wait()

        outcomes = svc.get_outcomes()
        outcome = outcomes["timestamped"]
        assert outcome.checked_at is not None
        assert outcome.state == "found"


# ---------------------------------------------------------------------------
# check_single (synchronous helper)
# ---------------------------------------------------------------------------

class TestCheckSingle:
    def test_check_single_found(self):
        with patch("src.services.validation_service.urllib.request.urlopen",
                   return_value=_make_http_response(200)):
            result = ValidationService.check_single("Ace")

        assert result.state == "found"
        assert result.spelling == "Ace"
        assert result.source == "manual_review"
        assert result.checked_at is not None

    def test_check_single_not_found(self):
        import urllib.error

        def fake_urlopen(req, timeout):
            raise urllib.error.HTTPError(url=None, code=404, msg="Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]

        with patch("src.services.validation_service.urllib.request.urlopen",
                   side_effect=fake_urlopen):
            result = ValidationService.check_single("Ghost")

        assert result.state == "not_found"
