from __future__ import annotations

import os
import sys
from pathlib import Path


def _prepend_env_path(path: Path) -> None:
    try:
        resolved = str(path.resolve())
    except Exception:
        return
    existing = os.environ.get("PATH", "")
    entries = existing.split(os.pathsep) if existing else []
    if resolved in entries:
        return
    os.environ["PATH"] = os.pathsep.join([resolved, *entries]) if entries else resolved


_dll_handles: list[object] = []


def _register_dll_dir(path: Path) -> None:
    add_dll_directory = getattr(os, "add_dll_directory", None)
    if add_dll_directory is None:
        return
    try:
        _dll_handles.append(add_dll_directory(str(path.resolve())))
    except Exception:
        # Best effort only; import-time fallback still uses PATH when possible.
        return


def _apply_runtime_paths() -> None:
    executable_root = Path(sys.executable).resolve().parent
    bundle_root = Path(getattr(sys, "_MEIPASS", executable_root / "_internal"))
    internal_root = executable_root / "_internal"

    dll_dirs: list[Path] = [
        # paddle/base contains co-located DLLs (common.dll, mkldnn.dll, etc.)
        # Python 3.8+ does NOT auto-search a PYD's own directory for DLL deps,
        # so this must be registered explicitly via add_dll_directory.
        bundle_root / "paddle" / "base",
        bundle_root / "paddle" / "libs",
        bundle_root / "paddleocr",
        bundle_root,
        internal_root / "paddle" / "base",
        internal_root / "paddle" / "libs",
        internal_root,
    ]

    # Include all wheel-style native dependency folders such as numpy.libs,
    # scipy.libs, Shapely.libs, etc., which may be required by PaddleOCR
    # transitive imports on clean machines.
    for root in (bundle_root, internal_root):
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and child.name.lower().endswith(".libs"):
                dll_dirs.append(child)

    for dll_candidate in dll_dirs:
        if dll_candidate.exists():
            _prepend_env_path(dll_candidate)
            _register_dll_dir(dll_candidate)


try:
    _apply_runtime_paths()
except Exception:
    # Runtime hook must never prevent process startup.
    pass