from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.web.app.review_sidecar_store import ReviewSidecarStore


class ReviewHistoryStore:
    """Per-video append-only snapshot persistence with light compaction markers."""

    def __init__(self, sidecar_store: ReviewSidecarStore | None = None, max_uncompressed: int = 100) -> None:
        self._sidecar = sidecar_store or ReviewSidecarStore()
        self._max_uncompressed = max(1, max_uncompressed)

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _entry_sort_key(entry: dict[str, Any]) -> tuple[str, str]:
        return str(entry.get("created_at", "")), str(entry.get("entry_id", ""))

    def _container_path(self, csv_path: Path | str, session_payload: dict[str, Any]) -> Path:
        payload = self._sidecar.ensure_workspace_metadata(csv_path, session_payload)
        container_raw = payload["workspace"]["history_container_path"]
        return Path(str(container_raw))

    def _load_container(self, path: Path, video_id: str) -> dict[str, Any]:
        if not path.exists():
            return {
                "schema_version": "1.0",
                "video_id": video_id,
                "entries": [],
                "compression_index": {},
            }
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        if payload.get("video_id") != video_id:
            payload["video_id"] = video_id
        if not isinstance(payload.get("entries"), list):
            payload["entries"] = []
        if not isinstance(payload.get("compression_index"), dict):
            payload["compression_index"] = {}
        payload.setdefault("schema_version", "1.0")
        return payload

    @staticmethod
    def _write_container(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _build_snapshot(session_payload: dict[str, Any]) -> dict[str, Any]:
        groups = [dict(group) for group in list(session_payload.get("groups", [])) if isinstance(group, dict)]
        group_count = len(groups)
        resolved_count = sum(1 for group in groups if str(group.get("resolution_status", "UNRESOLVED")) == "RESOLVED")
        unresolved_count = max(0, group_count - resolved_count)
        reviewed_names = sorted(
            {
                str(name).strip()
                for name in dict(session_payload.get("accepted_names", {})).values()
                if str(name).strip()
            }
        )
        return {
            "group_count": group_count,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "groups": groups,
            "reviewed_names": reviewed_names,
        }

    def list_entries(self, csv_path: Path | str, session_payload: dict[str, Any]) -> list[dict[str, Any]]:
        payload = self._sidecar.ensure_workspace_metadata(csv_path, session_payload)
        video_id = payload["workspace"]["video_id"]
        container_path = self._container_path(csv_path, payload)
        container = self._load_container(container_path, video_id)
        entries = [entry for entry in container["entries"] if isinstance(entry, dict)]
        entries.sort(key=self._entry_sort_key, reverse=True)
        return entries

    def get_entry(self, csv_path: Path | str, session_payload: dict[str, Any], entry_id: str) -> dict[str, Any] | None:
        for entry in self.list_entries(csv_path, session_payload):
            if str(entry.get("entry_id")) == entry_id:
                return entry
        return None

    def append_snapshot(
        self,
        csv_path: Path | str,
        session_payload: dict[str, Any],
        trigger_type: str,
    ) -> dict[str, Any]:
        payload = self._sidecar.ensure_workspace_metadata(csv_path, session_payload)
        video_id = payload["workspace"]["video_id"]
        container_path = self._container_path(csv_path, payload)
        container = self._load_container(container_path, video_id)

        entry_id = f"h_{uuid4().hex[:12]}"
        snapshot = self._build_snapshot(payload)
        entry = {
            "entry_id": entry_id,
            "created_at": self._utc_now(),
            "trigger_type": trigger_type,
            "compressed": False,
            "summary": {
                "group_count": snapshot["group_count"],
                "resolved_count": snapshot["resolved_count"],
                "unresolved_count": snapshot["unresolved_count"],
            },
            "snapshot": snapshot,
        }
        entries = list(container["entries"])
        entries.append(entry)
        container["entries"] = entries

        self._mark_compaction(container)
        self._write_container(container_path, container)
        return entry

    def _mark_compaction(self, container: dict[str, Any]) -> None:
        entries = [entry for entry in container["entries"] if isinstance(entry, dict)]
        if len(entries) <= self._max_uncompressed:
            return
        compress_until = len(entries) - self._max_uncompressed
        compression_index: dict[str, str] = dict(container.get("compression_index", {}))
        for entry in entries[:compress_until]:
            entry_id = str(entry.get("entry_id", "")).strip()
            if not entry_id:
                continue
            entry["compressed"] = True
            compression_index[entry_id] = "summary_only_marker"
        container["compression_index"] = compression_index

    def restore_snapshot(
        self,
        csv_path: Path | str,
        session_payload: dict[str, Any],
        entry_id: str,
        create_restore_snapshot: bool,
    ) -> tuple[dict[str, Any], str | None]:
        target = self.get_entry(csv_path, session_payload, entry_id)
        if target is None:
            raise FileNotFoundError(f"history entry {entry_id} not found")

        snapshot = dict(target.get("snapshot", {}))
        groups = [dict(group) for group in snapshot.get("groups", []) if isinstance(group, dict)]
        accepted_names: dict[str, str] = {}
        rejected_candidates: dict[str, list[str]] = {}
        collapsed_groups: dict[str, bool] = {}
        resolution_status: dict[str, str] = {}
        restored_candidates: list[dict[str, Any]] = []

        for group in groups:
            group_id = str(group.get("group_id", "")).strip()
            accepted = str(group.get("accepted_name", "")).strip()
            if group_id and accepted:
                accepted_names[group_id] = accepted

            rejected = [
                str(candidate_id).strip()
                for candidate_id in list(group.get("rejected_candidate_ids", []))
                if str(candidate_id).strip()
            ]
            if group_id and rejected:
                rejected_candidates[group_id] = rejected

            if group_id:
                collapsed_groups[group_id] = bool(
                    group.get("remembered_is_collapsed")
                    if group.get("remembered_is_collapsed") is not None
                    else group.get("is_collapsed", False)
                )
                resolution_status[group_id] = str(group.get("resolution_status", "UNRESOLVED"))

            for candidate in list(group.get("candidates", [])):
                if isinstance(candidate, dict):
                    restored_candidates.append(dict(candidate))

        restored = dict(session_payload)
        restored["candidates"] = restored_candidates
        restored["groups"] = groups
        restored["accepted_names"] = accepted_names
        restored["rejected_candidates"] = rejected_candidates
        restored["collapsed_groups"] = collapsed_groups
        restored["resolution_status"] = resolution_status
        restored["reviewed_names"] = list(snapshot.get("reviewed_names", []))

        created_restore_entry_id: str | None = None
        if create_restore_snapshot:
            entry = self.append_snapshot(csv_path, restored, "restore")
            created_restore_entry_id = str(entry.get("entry_id"))

        return restored, created_restore_entry_id
