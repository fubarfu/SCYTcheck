from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from src.config import history_index_path
from src.web.app.review_sidecar_store import ReviewSidecarStore


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def parse_duration_seconds(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def canonicalize_source(source_type: str, source_value: str) -> str:
    raw = source_value.strip()
    if not raw:
        return ""

    if source_type == "youtube_url":
        parsed = urlparse(raw)
        query = parse_qs(parsed.query)
        video_id = (query.get("v") or [""])[0].strip()
        if not video_id and parsed.netloc.lower() in {"youtu.be", "www.youtu.be"}:
            video_id = parsed.path.strip("/")
        if not video_id:
            video_id = raw
        return f"youtube:{video_id.lower()}"

    normalized = str(Path(raw).expanduser().resolve(strict=False)).replace("\\", "/")
    return normalized.lower() if os.name == "nt" else normalized


def make_merge_key(canonical_source: str, duration_seconds: int | None) -> str | None:
    if not canonical_source or duration_seconds is None:
        return None
    return f"{canonical_source}|{duration_seconds}"


@dataclass
class HistoryStore:
    index_path: Path | None = None

    def __post_init__(self) -> None:
        self._path = self.index_path or history_index_path()

    @property
    def path(self) -> Path:
        return self._path

    def load_index(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"entries": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {"entries": []}
        if not isinstance(payload, dict):
            return {"entries": []}
        entries = payload.get("entries")
        if not isinstance(entries, list):
            return {"entries": []}
        return {"entries": [entry for entry in entries if isinstance(entry, dict)]}

    def save_index(self, payload: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        tmp.replace(self._path)

    def list_entries(self, include_deleted: bool = False, limit: int = 200) -> list[dict[str, Any]]:
        items = self.load_index().get("entries", [])
        filtered = [
            entry
            for entry in items
            if include_deleted or not bool(entry.get("deleted", False))
        ]
        filtered.sort(key=lambda item: str(item.get("updated_at", "")), reverse=True)
        return filtered[: max(1, min(limit, 5000))]

    def get_entry(self, history_id: str, include_deleted: bool = False) -> dict[str, Any] | None:
        for entry in self.load_index().get("entries", []):
            if str(entry.get("history_id")) != history_id:
                continue
            if not include_deleted and bool(entry.get("deleted", False)):
                return None
            return entry
        return None

    def upsert_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        payload = self.load_index()
        entries = payload.get("entries", [])
        history_id = str(entry.get("history_id", ""))
        now = _now_iso()
        if not entry.get("created_at"):
            entry["created_at"] = now
        entry["updated_at"] = now

        for index, existing in enumerate(entries):
            if str(existing.get("history_id")) == history_id:
                entries[index] = entry
                payload["entries"] = entries
                self.save_index(payload)
                return entry

        entries.append(entry)
        payload["entries"] = entries
        self.save_index(payload)
        return entry

    def soft_delete(self, history_id: str) -> bool:
        payload = self.load_index()
        changed = False
        for entry in payload.get("entries", []):
            if str(entry.get("history_id")) != history_id:
                continue
            if bool(entry.get("deleted", False)):
                return True
            entry["deleted"] = True
            entry["updated_at"] = _now_iso()
            changed = True
            break
        if changed:
            self.save_index(payload)
        return changed

    def find_by_merge_key(self, merge_key: str) -> dict[str, Any] | None:
        if not merge_key:
            return None
        for entry in self.load_index().get("entries", []):
            if bool(entry.get("deleted", False)):
                continue
            if str(entry.get("merge_key", "")) == merge_key:
                return entry
        return None


def guess_display_name(source_type: str, source_value: str) -> str:
    if source_type == "youtube_url":
        parsed = urlparse(source_value)
        query = parse_qs(parsed.query)
        video_id = (query.get("v") or [""])[0].strip()
        return video_id or source_value.strip()
    return Path(source_value).name or source_value.strip()


def derive_review_artifacts(
    output_folder: Path,
    preferred_csv_path: str | None = None,
) -> dict[str, Any]:
    if not output_folder.exists() or not output_folder.is_dir():
        return {
            "resolution_status": "missing_folder",
            "resolved_csv_paths": [],
            "resolved_sidecar_paths": [],
            "primary_csv_path": None,
            "resolution_messages": ["Output folder does not exist or is not accessible"],
        }

    csv_candidates: list[Path] = []
    seen_csv_paths: set[str] = set()

    def _add_csv_candidate(path: Path) -> None:
        resolved = str(path.resolve(strict=False))
        if resolved in seen_csv_paths:
            return
        if not path.exists() or not path.is_file() or path.suffix.lower() != ".csv":
            return
        seen_csv_paths.add(resolved)
        csv_candidates.append(path)

    for csv_path in output_folder.glob("*.csv"):
        _add_csv_candidate(csv_path)

    workspace_parent = output_folder / ".scyt_review_workspaces"
    if workspace_parent.exists() and workspace_parent.is_dir():
        for csv_path in workspace_parent.glob("*/*.csv"):
            _add_csv_candidate(csv_path)

    if preferred_csv_path:
        _add_csv_candidate(Path(preferred_csv_path))

    csv_paths = sorted(csv_candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    if not csv_paths:
        return {
            "resolution_status": "missing_results",
            "resolved_csv_paths": [],
            "resolved_sidecar_paths": [],
            "primary_csv_path": None,
            "resolution_messages": ["No CSV files found in output folder"],
        }

    if preferred_csv_path:
        preferred = Path(preferred_csv_path)
        for index, csv_path in enumerate(csv_paths):
            if csv_path.resolve(strict=False) == preferred.resolve(strict=False):
                csv_paths.insert(0, csv_paths.pop(index))
                break

    sidecar_store = ReviewSidecarStore()
    sidecars: list[str] = []
    for csv_path in csv_paths:
        workspace_sidecar = sidecar_store.review_state_path_for_csv(csv_path)
        if workspace_sidecar is not None and workspace_sidecar.exists():
            sidecars.append(str(workspace_sidecar))
            continue
        legacy_sidecar = csv_path.with_suffix(".review.json")
        if legacy_sidecar.exists():
            sidecars.append(str(legacy_sidecar))

    status = "ready"
    messages: list[str] = []
    if not sidecars:
        status = "partial"
        messages.append("Review sidecar JSON not found; continuing with CSV artifacts")

    return {
        "resolution_status": status,
        "resolved_csv_paths": [str(path) for path in csv_paths],
        "resolved_sidecar_paths": sidecars,
        "primary_csv_path": str(csv_paths[0]),
        "resolution_messages": messages,
    }
