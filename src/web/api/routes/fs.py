from __future__ import annotations

import queue
import threading
import tkinter
import tkinter.filedialog
from http import HTTPStatus


class _DialogWorker:
    """Owns a single Tk instance on a dedicated daemon thread.

    Keeps the Tk event loop warm so folder-picker dialogs open instantly
    without spawning a new process for every request.
    """

    def __init__(self) -> None:
        self._q: queue.Queue = queue.Queue()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="tk-dialog-worker")
        self._thread.start()
        self._ready.wait(timeout=5)

    def _run(self) -> None:
        self._root = tkinter.Tk()
        self._root.withdraw()
        self._ready.set()
        self._poll()
        self._root.mainloop()

    def _poll(self) -> None:
        try:
            while True:
                func, result_holder, done = self._q.get_nowait()
                result_holder[0] = func(self._root)
                done.set()
        except queue.Empty:
            pass
        self._root.after(50, self._poll)

    def ask_directory(self, title: str = "", initial_dir: str = "") -> str:
        result: list[str | None] = [None]
        done = threading.Event()

        def _ask(root: tkinter.Tk) -> str:
            root.attributes("-topmost", True)
            chosen = tkinter.filedialog.askdirectory(
                parent=root,
                title=title,
                initialdir=initial_dir or None,
            )
            root.attributes("-topmost", False)
            return chosen or ""

        self._q.put((_ask, result, done))
        done.wait(timeout=120)
        return result[0] or ""

    def ask_save_file(self, title: str = "", initial_dir: str = "", default_name: str = "") -> str:
        result: list[str | None] = [None]
        done = threading.Event()

        def _ask(root: tkinter.Tk) -> str:
            root.attributes("-topmost", True)
            chosen = tkinter.filedialog.asksaveasfilename(
                parent=root,
                title=title,
                initialdir=initial_dir or None,
                initialfile=default_name or None,
                defaultextension=".csv",
                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
            )
            root.attributes("-topmost", False)
            return chosen or ""

        self._q.put((_ask, result, done))
        done.wait(timeout=120)
        return result[0] or ""


# Pre-warm the worker at import time so the first click is instant.
_worker = _DialogWorker()


def _get_worker() -> _DialogWorker:
    return _worker


class FsHandler:
    """Filesystem helper routes (e.g. native folder picker)."""

    def get_pick_folder(self, initial_dir: str = "") -> tuple[int, dict]:
        """Open a native OS folder-chooser dialog and return the chosen path."""
        try:
            path = _get_worker().ask_directory(
                title="Choose output folder",
                initial_dir=initial_dir,
            )
        except Exception:
            path = ""
        if not path:
            return HTTPStatus.NO_CONTENT, {"path": ""}
        return HTTPStatus.OK, {"path": path}

    def get_pick_save_file(self, initial_dir: str = "", default_name: str = "") -> tuple[int, dict]:
        """Open a native save-file chooser dialog and return the chosen file path."""
        try:
            path = _get_worker().ask_save_file(
                title="Export names to CSV",
                initial_dir=initial_dir,
                default_name=default_name,
            )
        except Exception:
            path = ""
        if not path:
            return HTTPStatus.NO_CONTENT, {"path": ""}
        return HTTPStatus.OK, {"path": path}
