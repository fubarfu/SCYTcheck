from __future__ import annotations

import signal
import time

from src.web.app.launcher import AppLauncher
from src.services.logging import configure_logging


def main() -> None:
    configure_logging()
    launcher = AppLauncher()
    launcher.start()

    stop_event = False

    def _shutdown(signum, frame) -> None:  # noqa: ANN001
        nonlocal stop_event
        stop_event = True

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while not stop_event:
            time.sleep(0.5)
    finally:
        launcher.stop()


if __name__ == "__main__":
    main()
