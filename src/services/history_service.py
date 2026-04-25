from __future__ import annotations

import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.web.app.history_store import (
    HistoryStore,
    canonicalize_source,
    derive_review_artifacts,
    guess_display_name,
    make_merge_key,
    parse_duration_seconds,
)


class HistoryService:
    """Business logic for video history persistence and reopen workflows."""

    def __init__(self, store: HistoryStore | None = None) -> None:
        self.store = store or HistoryStore()

    def list_videos(self, include_deleted: bool = False, limit: int = 200) -> dict[str, Any]:
        items = self.store.list_entries(include_deleted=include_deleted, limit=limit)
        return {
            "items": [self._to_list_item(item) for item in items],
            "total": len(items),
        }

    def get_video(self, history_id: str) -> dict[str, Any]:
        entry = self.store.get_entry(history_id, include_deleted=True)
        if entry is None:
            raise FileNotFoundError(f"history_id {history_id} not found")
        return deepcopy(entry)

    def delete_video(self, history_id: str) -> dict[str, Any]:
        if not self.store.soft_delete(history_id):
            raise FileNotFoundError(f"history_id {history_id} not found")
        return {"history_id": history_id, "deleted": True}

    def merge_run(
        self,
        *,
        source_type: str,
        source_value: str,
        canonical_source: str | None,
        duration_seconds: int | None,
        result_csv_path: str,
        output_folder: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        canonical = (canonical_source or "").strip() or canonicalize_source(source_type, source_value)
        duration = parse_duration_seconds(duration_seconds)
        merge_key = make_merge_key(canonical, duration)

        entry = self.store.find_by_merge_key(merge_key) if merge_key else None
        merged = entry is not None
        potential_duplicate = merge_key is None

        if entry is None:
            history_id = f"vh_{uuid.uuid4().hex[:12]}"
            entry = {
                "history_id": history_id,
                "canonical_source": canonical,
                "source_type": source_type,
                "duration_seconds": duration,
                "merge_key": merge_key,
                "potential_duplicate": potential_duplicate,
                "display_name": guess_display_name(source_type, source_value),
                "output_folder": output_folder,
                "last_result_csv": result_csv_path,
                "run_count": 0,
                "deleted": False,
                "runs": [],
                "contexts": [],
            }

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        context_id = f"ctx_{uuid.uuid4().hex[:12]}"
        entry["output_folder"] = output_folder
        entry["last_result_csv"] = result_csv_path
        entry["run_count"] = int(entry.get("run_count", 0)) + 1
        entry["deleted"] = False
        entry["potential_duplicate"] = potential_duplicate
        entry["runs"] = list(entry.get("runs", []))
        entry["runs"].append(
            {
                "run_id": run_id,
                "history_id": entry["history_id"],
                "result_csv_path": result_csv_path,
                "sidecar_review_path": str(Path(result_csv_path).with_suffix(".review.json")),
                "settings_snapshot_id": context_id,
            }
        )

        context_payload = {
            "context_id": context_id,
            "history_id": entry["history_id"],
            "scan_region": dict(context.get("scan_region", {})),
            "output_folder": output_folder,
            "context_patterns": list(context.get("context_patterns", [])),
            "analysis_settings": dict(context.get("analysis_settings", {})),
        }
        entry["contexts"] = list(entry.get("contexts", []))
        entry["contexts"].append(context_payload)

        persisted = self.store.upsert_entry(entry)
        return {
            "history_id": persisted["history_id"],
            "merged": merged,
            "potential_duplicate": potential_duplicate,
            "run_id": run_id,
            "run_count": persisted["run_count"],
        }

    def reopen(self, history_id: str) -> dict[str, Any]:
        entry = self.store.get_entry(history_id)
        if entry is None:
            raise FileNotFoundError(f"history_id {history_id} not found")

        contexts = list(entry.get("contexts", []))
        latest_context = contexts[-1] if contexts else {
            "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60},
            "output_folder": str(entry.get("output_folder", "")),
            "context_patterns": [],
            "analysis_settings": {},
        }

        output_folder = Path(str(latest_context.get("output_folder") or entry.get("output_folder", "")))
        derived = derive_review_artifacts(output_folder)

        return {
            "history_id": entry["history_id"],
            "analysis_context": {
                "scan_region": dict(latest_context.get("scan_region", {})),
                "output_folder": str(latest_context.get("output_folder", entry.get("output_folder", ""))),
                "context_patterns": list(latest_context.get("context_patterns", [])),
                "analysis_settings": dict(latest_context.get("analysis_settings", {})),
            },
            "derived_results": derived,
            "review_route": f"/review?history_id={entry['history_id']}",
        }

    @staticmethod
    def _to_list_item(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "history_id": entry.get("history_id"),
            "display_name": entry.get("display_name"),
            "canonical_source": entry.get("canonical_source"),
            "duration_seconds": entry.get("duration_seconds"),
            "potential_duplicate": bool(entry.get("potential_duplicate", False)),
            "run_count": int(entry.get("run_count", 0)),
            "output_folder": entry.get("output_folder"),
            "updated_at": entry.get("updated_at"),
        }
