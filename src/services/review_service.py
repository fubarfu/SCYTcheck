from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.services.project_service import ProjectService
from src.web.app.review_grouping import recompute_groups
from src.web.app.review_sidecar_store import ReviewSidecarStore


class ReviewService:
    """Merge review context across runs and persist user actions."""

    def __init__(self, sidecar_store: ReviewSidecarStore | None = None) -> None:
        self.sidecar_store = sidecar_store or ReviewSidecarStore()

    def merge_review_context(self, project_location: str, video_id: str) -> dict[str, Any]:
        workspace_root = ProjectService.resolve_workspace_root(project_location, video_id)
        if workspace_root is None:
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

        sidecar_run_count = len(runs)
        metadata_run_count = self._read_workspace_metadata_run_count(workspace_root)
        effective_run_count = sidecar_run_count
        if metadata_run_count is not None:
            effective_run_count = max(effective_run_count, metadata_run_count)

        prior_state_path = workspace_root / "review_state.json"
        if not prior_state_path.exists():
            legacy_prior_state_path = workspace_root / ".scyt_review_workspaces" / "review_state.json"
            if legacy_prior_state_path.exists():
                prior_state_path = legacy_prior_state_path
        prior_state = self._load_prior_state(prior_state_path)
        prior_decisions = self._extract_prior_decisions(prior_state)
        thresholds = self._extract_thresholds(prior_state)
        validation_outcomes = self._extract_validation_outcomes(runs, prior_state)

        merged_candidates = self._merge_candidates(runs, prior_decisions)
        merged_candidates = self.mark_new_candidates(merged_candidates, runs, prior_decisions)
        for candidate in merged_candidates:
            key = str(candidate.get("corrected_text") or candidate.get("spelling") or "").strip().lower()
            if not key:
                continue
            outcome = validation_outcomes.get(key)
            if not isinstance(outcome, dict):
                continue
            state = str(outcome.get("state") or "").strip().lower()
            if state in {"found", "not_found", "checking", "failed"}:
                candidate["validation_state"] = state

        grouped_payload = recompute_groups(
            {
                "candidates": [
                    {
                        "candidate_id": str(candidate.get("id") or ""),
                        # Group naming should stay anchored to OCR spelling; corrected_text is a card-level override.
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
        merged_candidate_by_id = {
            str(candidate.get("id") or ""): candidate
            for candidate in merged_candidates
            if str(candidate.get("id") or "").strip()
        }

        def _resolve_group_name(group_payload: dict[str, Any]) -> str:
            group_candidates = list(group_payload.get("candidates") or [])
            for group_candidate in group_candidates:
                candidate_id = str(group_candidate.get("candidate_id") or "").strip()
                if not candidate_id:
                    continue
                if candidate_status_by_id.get(candidate_id, "unreviewed") != "confirmed":
                    continue
                candidate = merged_candidate_by_id.get(candidate_id, {})
                corrected = str(candidate.get("corrected_text") or "").strip()
                if corrected:
                    return corrected
                spelling = str(candidate.get("spelling") or "").strip()
                if spelling:
                    return spelling

            return str(
                group_payload.get("accepted_name")
                or group_payload.get("display_name")
                or group_payload.get("group_id")
                or ""
            )

        groups = [
            {
                "id": str(group.get("group_id") or ""),
                "name": _resolve_group_name(group),
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
            "run_count": effective_run_count,
            "latest_run_id": str(max(effective_run_count - 1, 0)),
            "candidates": merged_candidates,
            "groups": groups,
            "thresholds": dict(grouped_payload.get("thresholds") or thresholds),
            "validation_outcomes": validation_outcomes,
        }

    @staticmethod
    def _extract_validation_outcomes(
        runs: list[dict[str, Any]],
        prior_state: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for run in runs:
            raw = run.get("validation_outcomes")
            if not isinstance(raw, dict):
                continue
            for name, outcome in raw.items():
                key = str(name or "").strip().lower()
                if not key or not isinstance(outcome, dict):
                    continue
                merged[key] = dict(outcome)

        fallback = prior_state.get("validation_outcomes") if isinstance(prior_state, dict) else None
        if isinstance(fallback, dict):
            # Prefer persisted review_state outcomes (includes manual retries)
            # over older run sidecar snapshots when keys overlap.
            for name, outcome in fallback.items():
                key = str(name or "").strip().lower()
                if not key or not isinstance(outcome, dict):
                    continue
                merged[key] = dict(outcome)

        return merged

    @staticmethod
    def _read_workspace_metadata_run_count(workspace_root: Path) -> int | None:
        metadata_path = workspace_root / "metadata.json"
        if not metadata_path.exists():
            return None
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        try:
            value = int(payload.get("run_count"))
        except (TypeError, ValueError):
            return None
        return max(0, value)

    @staticmethod
    def _derive_group_decision(statuses: list[str]) -> str:
        normalized = [str(status).strip().lower() for status in statuses if str(status).strip()]
        if not normalized:
            return "unreviewed"
        if all(status in {"rejected"} for status in normalized):
            return "rejected"
        # A group is confirmed if all candidates have been explicitly reviewed
        # (confirmed/edited or rejected) and at least one is confirmed/edited.
        # This is the normal state after a user selects a name from a group:
        # the chosen spelling is "confirmed" and alternates are "rejected".
        reviewed_statuses = {"confirmed", "edited", "rejected"}
        if all(status in reviewed_statuses for status in normalized):
            if any(status in {"confirmed", "edited"} for status in normalized):
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

        workspace_root = ProjectService.resolve_workspace_root(project_location, video_id)
        if workspace_root is None:
            workspace_root = Path(project_location) / video_id
        workspace_root.mkdir(parents=True, exist_ok=True)
        review_state_path = workspace_root / "review_state.json"
        legacy_review_state_path = workspace_root / ".scyt_review_workspaces" / "review_state.json"

        payload = self._load_prior_state(review_state_path)
        if not payload and legacy_review_state_path.exists():
            payload = self._load_prior_state(legacy_review_state_path)
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

        previous_decision_raw = str(previous.get("decision") or "").strip().lower()
        if previous_decision_raw == "edited":
            previous_decision_raw = "unreviewed"
        if previous_decision_raw not in {"unreviewed", "confirmed", "rejected"}:
            previous_decision_raw = "unreviewed"

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
                member_corrected_text = str(member_previous.get("corrected_text") or "").strip()
                decisions[member_id] = {
                    "decision": member_decision,
                    "marked_new": False,
                    "user_note": (user_note or "").strip()
                    if member_id == candidate_id and (user_note or "").strip()
                    else member_previous.get("user_note", ""),
                    "corrected_text": member_corrected_text,
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
                member_corrected_text = str(member_previous.get("corrected_text") or "").strip()
                decisions[member_id] = {
                    "decision": "rejected",
                    "marked_new": False,
                    "user_note": (user_note or "").strip()
                    if member_id == candidate_id and (user_note or "").strip()
                    else member_previous.get("user_note", ""),
                    "corrected_text": member_corrected_text,
                }
        else:
            if action == "clear_new":
                decision = previous_decision_raw
            elif action == "edited":
                # Editing candidate text should not change review status.
                decision = previous_decision_raw
            else:
                decision = action

            if not decision:
                decision = "unreviewed"

            corrected_text = str(previous.get("corrected_text") or "").strip()
            if action == "edited":
                corrected_text = (user_note or "").strip() or corrected_text

            decisions[candidate_id] = {
                "decision": decision,
                "marked_new": False,
                "user_note": (user_note or "").strip() or previous.get("user_note", ""),
                "corrected_text": corrected_text,
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
        workspace_root = ProjectService.resolve_workspace_root(project_location, video_id)
        if workspace_root is None:
            workspace_root = Path(project_location) / video_id
        workspace_root.mkdir(parents=True, exist_ok=True)
        review_state_path = workspace_root / "review_state.json"
        legacy_review_state_path = workspace_root / ".scyt_review_workspaces" / "review_state.json"

        payload = self._load_prior_state(review_state_path)
        if not payload and legacy_review_state_path.exists():
            payload = self._load_prior_state(legacy_review_state_path)
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
                decision_raw = str(item.get("decision") or "").strip().lower()
                if decision_raw == "edited":
                    decision_raw = "unreviewed"
                if decision_raw not in {"unreviewed", "confirmed", "rejected"}:
                    decision_raw = "unreviewed"

                corrected_text = str(item.get("corrected_text") or "").strip()
                # Backward compatibility for legacy payloads that stored edits in user_note.
                if not corrected_text and str(item.get("decision") or "").strip().lower() == "edited":
                    corrected_text = str(item.get("user_note") or "").strip()

                normalized[str(candidate_id)] = {
                    **item,
                    "decision": decision_raw,
                    "corrected_text": corrected_text,
                }
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
                        "corrected_text": None,
                        "discovered_in_run": run_id,
                        "marked_new": False,
                        "decision": "unreviewed",
                        "frame_count": 0,
                        "frame_samples": [],
                        "start_timestamp": str(candidate.get("start_timestamp") or ""),
                    }

                prior = prior_decisions.get(candidate_id)
                if isinstance(prior, dict):
                    decision = str(prior.get("decision") or "unreviewed").strip().lower()
                    if decision not in {"unreviewed", "confirmed", "rejected"}:
                        decision = "unreviewed"
                    merged[spelling]["decision"] = decision
                    edited_text = str(prior.get("corrected_text") or "").strip()
                    merged[spelling]["corrected_text"] = edited_text or None
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
