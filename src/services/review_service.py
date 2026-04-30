from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.web.app.review_grouping import recompute_groups
from src.web.app.review_sidecar_store import ReviewSidecarStore


class ReviewService:
    """Merge review context across runs and persist user actions."""

    def __init__(self, sidecar_store: ReviewSidecarStore | None = None) -> None:
        self.sidecar_store = sidecar_store or ReviewSidecarStore()

    def merge_review_context(self, project_location: str, video_id: str) -> dict[str, Any]:
        workspace_root = Path(project_location) / video_id
        if not workspace_root.exists():
            raise FileNotFoundError(f"video_id {video_id} not found")

        run_sidecars = sorted(workspace_root.glob("result_*.review.json"), key=lambda p: p.name)
        if not run_sidecars:
            review_state_path = workspace_root / "review_state.json"
            if review_state_path.exists():
                run_sidecars = [review_state_path]

        runs: list[dict[str, Any]] = []
        for sidecar_path in run_sidecars:
            try:
                payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict):
                runs.append(payload)

        prior_state_path = workspace_root / ".scyt_review_workspaces" / "review_state.json"
        prior_state = self._load_prior_state(prior_state_path)
        prior_decisions = self._extract_prior_decisions(prior_state)
        thresholds = self._extract_thresholds(prior_state)

        merged_candidates = self._merge_candidates(runs, prior_decisions)
        merged_candidates = self.mark_new_candidates(merged_candidates, runs, prior_decisions)

        grouped_payload = recompute_groups(
            {
                "candidates": [
                    {
                        "candidate_id": str(candidate.get("id") or ""),
                        "extracted_name": str(candidate.get("spelling") or ""),
                        "status": str(candidate.get("decision") or "unreviewed"),
                        "marked_new": bool(candidate.get("marked_new")),
                        "start_timestamp": str(candidate.get("start_timestamp") or "0"),
                    }
                    for candidate in merged_candidates
                    if str(candidate.get("id") or "").strip()
                ],
                "thresholds": thresholds,
            }
        )
        grouped_candidates = list(grouped_payload.get("candidates", []))
        groups_payload = list(grouped_payload.get("groups", []))

        candidate_status_by_id = {
            str(candidate.get("candidate_id") or ""): str(candidate.get("status") or "unreviewed")
            for candidate in grouped_candidates
            if str(candidate.get("candidate_id") or "").strip()
        }

        groups = [
            {
                "id": str(group.get("group_id") or ""),
                "name": str(group.get("accepted_name") or group.get("display_name") or group.get("group_id") or ""),
                "candidate_ids": [
                    str(candidate.get("candidate_id") or "")
                    for candidate in list(group.get("candidates") or [])
                    if str(candidate.get("candidate_id") or "").strip()
                ],
                "decision": self._derive_group_decision(
                    [
                        candidate_status_by_id.get(str(candidate.get("candidate_id") or ""), "unreviewed")
                        for candidate in list(group.get("candidates") or [])
                        if str(candidate.get("candidate_id") or "").strip()
                    ]
                ),
            }
            for group in groups_payload
            if str(group.get("group_id") or "").strip()
        ]

        return {
            "video_id": video_id,
            "video_url": self._resolve_video_url(runs, video_id),
            "project_location": str(workspace_root),
            "run_count": len(runs),
            "latest_run_id": str(len(runs) - 1) if runs else "0",
            "candidates": merged_candidates,
            "groups": groups,
            "thresholds": dict(grouped_payload.get("thresholds") or thresholds),
        }

    @staticmethod
    def _derive_group_decision(statuses: list[str]) -> str:
        normalized = [str(status).strip().lower() for status in statuses if str(status).strip()]
        if not normalized:
            return "unreviewed"
        if all(status in {"rejected"} for status in normalized):
            return "rejected"
        if all(status in {"confirmed", "edited"} for status in normalized):
            return "confirmed"
        return "unreviewed"

    def mark_new_candidates(
        self,
        merged_candidates: list[dict[str, Any]],
        runs: list[dict[str, Any]],
        prior_decisions: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if not runs:
            return merged_candidates

        prior_decisions = prior_decisions or {}

        prior_spellings: set[str] = set()
        latest = runs[-1]
        latest_spellings: set[str] = set()

        for run in runs[:-1]:
            for candidate in list(run.get("candidates") or []):
                spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
                if spelling:
                    prior_spellings.add(spelling)

        for candidate in list(latest.get("candidates") or []):
            spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
            if spelling:
                latest_spellings.add(spelling)

        for candidate in merged_candidates:
            candidate_id = str(candidate.get("id") or "").strip()
            spelling = str(candidate.get("spelling") or "").strip()
            if not spelling:
                candidate["marked_new"] = False
                continue
            is_new = spelling in latest_spellings and spelling not in prior_spellings
            prior = prior_decisions.get(candidate_id)
            if isinstance(prior, dict) and prior.get("marked_new") is False:
                candidate["marked_new"] = False
            else:
                candidate["marked_new"] = is_new

        return merged_candidates

    def apply_candidate_action(
        self,
        project_location: str,
        video_id: str,
        candidate_id: str,
        action: str,
        user_note: str | None = None,
    ) -> dict[str, Any]:
        if action not in {"confirmed", "rejected", "edited", "clear_new", "unreviewed"}:
            raise ValueError("Action must be one of: confirmed, rejected, edited, clear_new, unreviewed")

        workspace_root = Path(project_location) / video_id / ".scyt_review_workspaces"
        workspace_root.mkdir(parents=True, exist_ok=True)
        review_state_path = workspace_root / "review_state.json"

        payload = self._load_prior_state(review_state_path)
        decisions = payload.get("candidate_decisions")
        if not isinstance(decisions, dict):
            decisions = {}

        context = self.merge_review_context(project_location, video_id)
        candidates = list(context.get("candidates") or [])
        groups = list(context.get("groups") or [])
        candidate_by_id = {
            str(candidate.get("id") or ""): candidate
            for candidate in candidates
            if str(candidate.get("id") or "").strip()
        }
        group_by_candidate_id: dict[str, dict[str, Any]] = {}
        for group in groups:
            group_candidate_ids = [
                str(group_candidate_id or "")
                for group_candidate_id in list(group.get("candidate_ids") or [])
                if str(group_candidate_id or "").strip()
            ]
            for group_candidate_id in group_candidate_ids:
                group_by_candidate_id[group_candidate_id] = group

        previous = decisions.get(candidate_id)
        if not isinstance(previous, dict):
            previous = {}

        candidate = candidate_by_id.get(candidate_id)
        group = group_by_candidate_id.get(candidate_id)

        if action == "confirmed" and candidate is not None and group is not None:
            selected_spelling = str(candidate.get("spelling") or "").strip().lower()
            for group_candidate_id in list(group.get("candidate_ids") or []):
                member_id = str(group_candidate_id or "").strip()
                if not member_id:
                    continue
                member_previous = decisions.get(member_id)
                if not isinstance(member_previous, dict):
                    member_previous = {}
                member = candidate_by_id.get(member_id, {})
                member_spelling = str(member.get("spelling") or "").strip().lower()
                member_decision = "confirmed" if member_spelling == selected_spelling else "rejected"
                decisions[member_id] = {
                    "decision": member_decision,
                    "marked_new": False,
                    "user_note": (user_note or "").strip()
                    if member_id == candidate_id and (user_note or "").strip()
                    else member_previous.get("user_note", ""),
                }
        elif action == "rejected" and candidate is not None and group is not None:
            selected_spelling = str(candidate.get("spelling") or "").strip().lower()
            for group_candidate_id in list(group.get("candidate_ids") or []):
                member_id = str(group_candidate_id or "").strip()
                if not member_id:
                    continue
                member = candidate_by_id.get(member_id, {})
                member_spelling = str(member.get("spelling") or "").strip().lower()
                if member_spelling != selected_spelling:
                    continue
                member_previous = decisions.get(member_id)
                if not isinstance(member_previous, dict):
                    member_previous = {}
                decisions[member_id] = {
                    "decision": "rejected",
                    "marked_new": False,
                    "user_note": (user_note or "").strip()
                    if member_id == candidate_id and (user_note or "").strip()
                    else member_previous.get("user_note", ""),
                }
        else:
            decision = previous.get("decision") if action == "clear_new" else action
            if action == "clear_new" and not decision:
                decision = "unreviewed"

            decisions[candidate_id] = {
                "decision": decision,
                "marked_new": False,
                "user_note": (user_note or "").strip() or previous.get("user_note", ""),
            }
        payload["candidate_decisions"] = decisions

        review_state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

        return {
            "candidate_id": candidate_id,
            "decision": decisions[candidate_id]["decision"],
            "marked_new": False,
        }

    def update_grouping_settings(
        self,
        project_location: str,
        video_id: str,
        thresholds: dict[str, Any],
        *,
        reset_decisions: bool,
    ) -> dict[str, Any]:
        workspace_root = Path(project_location) / video_id / ".scyt_review_workspaces"
        workspace_root.mkdir(parents=True, exist_ok=True)
        review_state_path = workspace_root / "review_state.json"

        payload = self._load_prior_state(review_state_path)
        payload["thresholds"] = self._extract_thresholds({"thresholds": thresholds})
        if reset_decisions:
            payload["candidate_decisions"] = {}

        review_state_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return self.merge_review_context(project_location, video_id)

    @staticmethod
    def _load_prior_state(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _extract_prior_decisions(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        decisions = payload.get("candidate_decisions")
        if not isinstance(decisions, dict):
            return {}
        normalized: dict[str, dict[str, Any]] = {}
        for candidate_id, item in decisions.items():
            if isinstance(item, dict):
                normalized[str(candidate_id)] = item
        return normalized

    @staticmethod
    def _extract_thresholds(payload: dict[str, Any]) -> dict[str, Any]:
        raw = payload.get("thresholds") if isinstance(payload, dict) else {}
        thresholds = raw if isinstance(raw, dict) else {}

        similarity_threshold = int(thresholds.get("similarity_threshold", 80))
        recommendation_threshold = int(thresholds.get("recommendation_threshold", 70))
        spelling_influence = int(thresholds.get("spelling_influence", 50))
        temporal_influence = int(thresholds.get("temporal_influence", 50))
        temporal_window_seconds = float(thresholds.get("temporal_window_seconds", 2.0))

        similarity_threshold = max(50, min(100, similarity_threshold))
        recommendation_threshold = max(0, min(100, recommendation_threshold))
        spelling_influence = max(0, min(100, spelling_influence))
        temporal_influence = max(0, min(100, temporal_influence))
        if temporal_window_seconds <= 0:
            temporal_window_seconds = 2.0

        return {
            "similarity_threshold": similarity_threshold,
            "recommendation_threshold": recommendation_threshold,
            "spelling_influence": spelling_influence,
            "temporal_influence": temporal_influence,
            "temporal_window_seconds": temporal_window_seconds,
        }

    @staticmethod
    def _merge_candidates(runs: list[dict[str, Any]], prior_decisions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        first_seen: dict[str, str] = {}

        for run_idx, run_payload in enumerate(runs):
            run_id = str(run_idx)
            for candidate in list(run_payload.get("candidates") or []):
                spelling = str(candidate.get("extracted_name") or candidate.get("spelling") or "").strip()
                if not spelling:
                    continue

                candidate_id = str(candidate.get("candidate_id") or f"cand-{spelling.lower()}")
                if spelling not in merged:
                    first_seen[spelling] = run_id
                    merged[spelling] = {
                        "id": candidate_id,
                        "spelling": spelling,
                        "discovered_in_run": run_id,
                        "marked_new": False,
                        "decision": "unreviewed",
                        "frame_count": 0,
                        "frame_samples": [],
                        "start_timestamp": str(candidate.get("start_timestamp") or ""),
                    }

                prior = prior_decisions.get(candidate_id)
                if isinstance(prior, dict):
                    decision = str(prior.get("decision") or "unreviewed")
                    merged[spelling]["decision"] = decision
                    if prior.get("marked_new") is False:
                        merged[spelling]["marked_new"] = False

        for spelling, run_id in first_seen.items():
            merged[spelling]["discovered_in_run"] = run_id

        return list(merged.values())

    @staticmethod
    def _resolve_video_url(runs: list[dict[str, Any]], fallback: str) -> str:
        for run in reversed(runs):
            source_value = str(run.get("source_value") or "").strip()
            if source_value:
                return source_value
        return fallback
