from __future__ import annotations

import queue
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock, Thread
from typing import Literal

ValidationState = Literal["unchecked", "checking", "found", "not_found", "failed"]

RSI_CITIZEN_URL = "https://robertsspaceindustries.com/en/citizens/{name}"
_REQUEST_TIMEOUT_SEC = 10
_MIN_DISPATCH_INTERVAL_SEC = 1.0

_SENTINEL = object()


@dataclass
class ValidationOutcome:
    spelling: str
    state: ValidationState = "unchecked"
    checked_at: datetime | None = None
    source: Literal["analysis_batch", "manual_review"] = "analysis_batch"


class ValidationService:
    """Rate-limited concurrent RSI citizen validation.

    Designed to be instantiated once per analysis run.  Call ``start()`` before
    enqueueing spellings; call ``stop()`` after scanning is complete; call
    ``wait()`` to block until the queue drains.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[object] = queue.Queue()
        self._lock = Lock()
        self._outcomes: dict[str, ValidationOutcome] = {}
        self._seen: set[str] = set()
        self._thread: Thread | None = None
        self._stopped = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn the background worker thread."""
        self._stopped = False
        self._thread = Thread(target=self._worker, name="validation-worker", daemon=True)
        self._thread.start()

    def enqueue(self, spelling: str) -> None:
        """Enqueue *spelling* for validation if it hasn't been seen this run.

        Deduplication key is ``spelling.lower().strip()``.
        Calling this after ``stop()`` is a no-op.
        """
        if self._stopped:
            return
        key = spelling.lower().strip()
        with self._lock:
            if key in self._seen:
                return
            self._seen.add(key)
            self._outcomes[key] = ValidationOutcome(spelling=spelling, state="checking")
        self._queue.put(spelling)

    def stop(self) -> None:
        """Signal the worker that no more spellings will be enqueued."""
        self._stopped = True
        self._queue.put(_SENTINEL)

    def wait(self) -> None:
        """Block until the worker thread finishes processing all queued items."""
        if self._thread is not None:
            self._thread.join()

    def queue_size(self) -> int:
        """Return the approximate number of pending items (may include sentinel)."""
        return max(0, self._queue.qsize())

    def get_outcomes(self) -> dict[str, ValidationOutcome]:
        """Return a snapshot of all outcomes keyed by normalised spelling."""
        with self._lock:
            return dict(self._outcomes)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        last_dispatch: float = 0.0
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                self._queue.task_done()
                break
            spelling = str(item)
            # Rate-limit: ensure at least 1 sec between dispatches
            now = time.monotonic()
            wait_sec = _MIN_DISPATCH_INTERVAL_SEC - (now - last_dispatch)
            if wait_sec > 0:
                time.sleep(wait_sec)
            last_dispatch = time.monotonic()
            outcome = self._check(spelling)
            key = spelling.lower().strip()
            with self._lock:
                self._outcomes[key] = outcome
            self._queue.task_done()

    def _check(self, spelling: str) -> ValidationOutcome:
        url = RSI_CITIZEN_URL.format(name=urllib.request.quote(spelling, safe=""))
        checked_at = datetime.now(UTC)
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SEC) as resp:
                state: ValidationState = "found" if resp.status == 200 else "failed"
        except urllib.error.HTTPError as exc:
            state = "not_found" if exc.code == 404 else "failed"
        except Exception:
            state = "failed"
        return ValidationOutcome(
            spelling=spelling,
            state=state,
            checked_at=checked_at,
            source="analysis_batch",
        )

    @staticmethod
    def check_single(spelling: str, source: Literal["analysis_batch", "manual_review"] = "manual_review") -> ValidationOutcome:
        """Synchronous single-spelling check (used for manual recheck).  Blocks until done."""
        url = RSI_CITIZEN_URL.format(name=urllib.request.quote(spelling, safe=""))
        checked_at = datetime.now(UTC)
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SEC) as resp:
                state: ValidationState = "found" if resp.status == 200 else "failed"
        except urllib.error.HTTPError as exc:
            state = "not_found" if exc.code == 404 else "failed"
        except Exception:
            state = "failed"
        return ValidationOutcome(
            spelling=spelling,
            state=state,
            checked_at=checked_at,
            source=source,
        )
