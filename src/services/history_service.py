from __future__ import annotations

import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.config import load_advanced_settings
from src.services.project_service import ProjectService
from src.web.app.review_sidecar_store import ReviewSidecarStore
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

    def __init__(
        self,
        store: HistoryStore | None = None,
        project_service: ProjectService | None = None,
        settings_loader: Any | None = None,
    ) -> None:
        self.store = store or HistoryStore()
        self.project_service = project_service or ProjectService()
        self.settings_loader = settings_loader or load_advanced_settings
        self.sidecar_store = ReviewSidecarStore()

    def list_videos(self, include_deleted: bool = False, limit: int = 200) -> dict[str, Any]:
        project_location = ""
        try:
            settings = self.settings_loader()
            project_location = str(getattr(settings, "project_location", "") or "").strip()
        except Exception:
            project_location = ""

        if project_location:
            projects = self.project_service.discover_projects(project_location)
            if projects:
                items = [self._project_to_list_item(project) for project in projects]
                bounded = items[: max(1, min(limit, 5000))]
                return {
                    "items": bounded,
                    "total": len(items),
                }

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
            workspace_meta = self.sidecar_store.ensure_workspace_metadata(
                result_csv_path,
                {"source_type": source_type, "source_value": source_value},
            )
            entry = {
                "history_id": history_id,
                "canonical_source": canonical,
                "source_type": source_type,
                "source_value": source_value,
                "duration_seconds": duration,
                "merge_key": merge_key,
                "potential_duplicate": potential_duplicate,
                "display_name": guess_display_name(source_type, source_value),
                "output_folder": output_folder,
                "workspace_path": workspace_meta["workspace"]["workspace_path"],
                "last_result_csv": result_csv_path,
                "run_count": 0,
                "deleted": False,
                "runs": [],
                "contexts": [],
            }

        workspace_meta = self.sidecar_store.ensure_workspace_metadata(
            result_csv_path,
            {
                "source_type": source_type,
                "source_value": source_value,
                "workspace": {"video_id": Path(str(entry.get("workspace_path", ""))).name},
            },
        )
        workspace_path = str(workspace_meta["workspace"]["workspace_path"])
        review_state_path = str(self.sidecar_store.workspace_review_state_path(workspace_path))

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        context_id = f"ctx_{uuid.uuid4().hex[:12]}"
        entry["output_folder"] = output_folder
        entry["workspace_path"] = workspace_path
        entry["source_type"] = source_type
        entry["source_value"] = source_value
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
                "sidecar_review_path": review_state_path,
                "settings_snapshot_id": context_id,
            }
        )

        context_payload = {
            "context_id": context_id,
            "history_id": entry["history_id"],
            "source_type": source_type,
            "source_value": source_value,
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

        sidecar_payload = None
        last_result_csv = str(entry.get("last_result_csv") or "").strip()
        if last_result_csv:
            sidecar_payload = self.sidecar_store.load(last_result_csv)
        if isinstance(sidecar_payload, dict):
            latest_context = {
                **latest_context,
                "source_type": sidecar_payload.get("source_type", latest_context.get("source_type")),
                "source_value": sidecar_payload.get("source_value", latest_context.get("source_value")),
                "scan_region": dict(sidecar_payload.get("scan_region", latest_context.get("scan_region", {}))),
                "output_folder": str(sidecar_payload.get("output_folder", latest_context.get("output_folder", ""))),
                "context_patterns": list(sidecar_payload.get("context_patterns", latest_context.get("context_patterns", []))),
                "analysis_settings": dict(sidecar_payload.get("analysis_settings", latest_context.get("analysis_settings", {}))),
            }

        output_folder = Path(str(latest_context.get("output_folder") or entry.get("output_folder", "")))
        derived = derive_review_artifacts(output_folder, preferred_csv_path=str(entry.get("last_result_csv") or ""))

        source_type = str(latest_context.get("source_type") or entry.get("source_type") or "youtube_url")
        source_value = str(latest_context.get("source_value") or entry.get("source_value") or "").strip()
        if not source_value:
            canonical_source = str(entry.get("canonical_source") or "").strip()
            if source_type == "youtube_url" and canonical_source.startswith("youtube:"):
                source_value = f"https://youtube.com/watch?v={canonical_source.split(':', 1)[1]}"
            elif source_type == "local_file":
                source_value = canonical_source

        return {
            "history_id": entry["history_id"],
            "analysis_context": {
                "source_type": source_type,
                "source_value": source_value,
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

    @staticmethod
    def _project_to_list_item(project: dict[str, Any]) -> dict[str, Any]:
        video_url = str(project.get("video_url") or "")
        created = str(project.get("created_date") or "")
        run_count = int(project.get("run_count") or 0)
        return {
            "history_id": str(project.get("project_id") or ""),
            "display_name": video_url or str(project.get("project_id") or ""),
            "canonical_source": video_url,
            "duration_seconds": None,
            "potential_duplicate": False,
            "run_count": run_count,
            "output_folder": str(project.get("project_location") or ""),
            "updated_at": str(project.get("last_analyzed") or created),
        }
