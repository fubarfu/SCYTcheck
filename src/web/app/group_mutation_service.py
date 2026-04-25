from __future__ import annotations

from typing import Any

from src.web.app.review_sidecar_store import ReviewSidecarStore


def _candidate_name(candidate: dict[str, Any]) -> str:
  corrected = str(candidate.get("corrected_text", "")).strip()
  if corrected:
    return corrected
  return str(candidate.get("extracted_name", "")).strip()


def _set_candidate_status(candidates: list[dict[str, Any]], candidate_id: str, status: str) -> list[dict[str, Any]]:
  updated: list[dict[str, Any]] = []
  for candidate in candidates:
    item = dict(candidate)
    if str(item.get("candidate_id", "")).strip() == candidate_id:
      item["status"] = status
    updated.append(item)
  return updated


def _find_group(groups: list[dict[str, Any]], group_id: str) -> dict[str, Any] | None:
  return next((group for group in groups if str(group.get("group_id", "")) == group_id), None)


def _find_group_for_candidate(groups: list[dict[str, Any]], candidate_id: str) -> str | None:
  for group in groups:
    for candidate in list(group.get("candidates", [])):
      if str(candidate.get("candidate_id", "")).strip() == candidate_id:
        return str(group.get("group_id", "")).strip()
  return None


def _find_candidate(group: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
  for candidate in list(group.get("candidates", [])):
    if str(candidate.get("candidate_id", "")).strip() == candidate_id:
      return candidate
  return None


def _duplicate_conflict(
  accepted_names: dict[str, str],
  candidate_name: str,
  *,
  excluded_group_id: str,
) -> str | None:
  normalized_target = candidate_name.strip().lower()
  if not normalized_target:
    return None
  for group_id, accepted_name in accepted_names.items():
    if group_id == excluded_group_id:
      continue
    if str(accepted_name).strip().lower() == normalized_target:
      return group_id
  return None


def _validation_payload(
  *,
  is_valid: bool,
  candidate_name: str,
  conflict_group_id: str | None = None,
) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "is_valid": is_valid,
    "candidate_name": candidate_name,
  }
  if not is_valid:
    payload["message"] = f"Accepted name already used by group {conflict_group_id}"
    payload["conflict_group_id"] = conflict_group_id
    payload["hint"] = "Choose a different candidate in this group"
  return payload


class GroupMutationService:
  @staticmethod
  def apply_action(
    session_payload: dict[str, Any],
    action_type: str,
    target_ids: list[str],
    action_payload: dict[str, Any],
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    """Apply review-group specific actions; return handled=False for legacy fallbacks."""
    payload = ReviewSidecarStore.ensure_group_state_maps(session_payload)
    groups = list(payload.get("groups", []))
    if not groups:
      return payload, None, False

    primary_target = str(target_ids[0]).strip() if target_ids else ""
    group_id = str(action_payload.get("group_id", "")).strip()
    if not group_id and primary_target and action_type in {"confirm", "reject", "unreject"}:
      group_id = _find_group_for_candidate(groups, primary_target) or ""

    if action_type == "confirm":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.confirm_candidate(payload, group_id, primary_target)
    if action_type == "reject":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.reject_candidate(payload, group_id, primary_target)
    if action_type == "unreject":
      if not group_id or not primary_target:
        return payload, None, False
      return GroupMutationService.unreject_candidate(payload, group_id, primary_target)
    if action_type == "deselect":
      if not group_id:
        return payload, None, False
      return GroupMutationService.deselect_group(payload, group_id)
    if action_type == "toggle_collapse":
      if not group_id:
        return payload, None, False
      requested = action_payload.get("is_collapsed")
      if requested is None:
        current = bool(payload.get("collapsed_groups", {}).get(group_id, False))
        requested = not current
      return GroupMutationService.toggle_group_collapsed(payload, group_id, bool(requested))

    return payload, None, False

  @staticmethod
  def confirm_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False

    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    accepted_name = _candidate_name(candidate)
    conflict_group = _duplicate_conflict(
      dict(payload.get("accepted_names", {})),
      accepted_name,
      excluded_group_id=group_id,
    )
    if conflict_group:
      return payload, _validation_payload(
        is_valid=False,
        candidate_name=accepted_name,
        conflict_group_id=conflict_group,
      ), True

    updated = store.set_group_accepted_name(payload, group_id, accepted_name)
    updated = store.set_candidate_rejected(updated, group_id, candidate_id, False)
    updated = store.set_group_resolution_status(updated, group_id, "RESOLVED")
    updated["candidates"] = _set_candidate_status(list(updated.get("candidates", [])), candidate_id, "confirmed")
    return updated, _validation_payload(is_valid=True, candidate_name=accepted_name), True

  @staticmethod
  def reject_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False

    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    candidate_name = _candidate_name(candidate)
    accepted_names = dict(payload.get("accepted_names", {}))
    updated = store.set_candidate_rejected(payload, group_id, candidate_id, True)
    if accepted_names.get(group_id, "").strip() == candidate_name:
      updated = store.set_group_accepted_name(updated, group_id, None)
      updated = store.set_group_resolution_status(updated, group_id, "UNRESOLVED")
    updated["candidates"] = _set_candidate_status(list(updated.get("candidates", [])), candidate_id, "rejected")
    return updated, None, True

  @staticmethod
  def unreject_candidate(
    session_payload: dict[str, Any],
    group_id: str,
    candidate_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    group = _find_group(list(payload.get("groups", [])), group_id)
    if group is None:
      return payload, None, False
    candidate = _find_candidate(group, candidate_id)
    if candidate is None:
      return payload, None, False

    updated = store.set_candidate_rejected(payload, group_id, candidate_id, False)
    updated["candidates"] = _set_candidate_status(list(updated.get("candidates", [])), candidate_id, "pending")
    return updated, None, True

  @staticmethod
  def deselect_group(
    session_payload: dict[str, Any],
    group_id: str,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    if _find_group(list(payload.get("groups", [])), group_id) is None:
      return payload, None, False

    updated = store.set_group_accepted_name(payload, group_id, None)
    updated = store.set_group_resolution_status(updated, group_id, "UNRESOLVED")
    updated = store.set_group_collapsed(updated, group_id, False)
    return updated, None, True

  @staticmethod
  def toggle_group_collapsed(
    session_payload: dict[str, Any],
    group_id: str,
    is_collapsed: bool,
  ) -> tuple[dict[str, Any], dict[str, Any] | None, bool]:
    store = ReviewSidecarStore()
    payload = store.ensure_group_state_maps(session_payload)
    if _find_group(list(payload.get("groups", [])), group_id) is None:
      return payload, None, False
    updated = store.set_group_collapsed(payload, group_id, is_collapsed)
    return updated, None, True

  @staticmethod
  def move_candidate(groups: list[dict], candidate_id: str, to_group_id: str) -> list[dict]:
    moving = None
    for group in groups:
      for candidate in list(group.get("candidates", [])):
        if candidate.get("candidate_id") == candidate_id:
          moving = candidate
          group["candidates"].remove(candidate)
          break
    if moving is None:
      return groups
    for group in groups:
      if group.get("group_id") == to_group_id:
        group.setdefault("candidates", []).append(moving)
        break
    return groups

  @staticmethod
  def merge_groups(groups: list[dict], group_a_id: str, group_b_id: str) -> list[dict]:
    a = next((g for g in groups if g.get("group_id") == group_a_id), None)
    b = next((g for g in groups if g.get("group_id") == group_b_id), None)
    if a is None or b is None:
      return groups
    a.setdefault("candidates", []).extend(b.get("candidates", []))
    return [g for g in groups if g.get("group_id") != group_b_id]

  @staticmethod
  def reorder_group(groups: list[dict], group_id: str, to_index: int) -> list[dict]:
    idx = next((i for i, g in enumerate(groups) if g.get("group_id") == group_id), None)
    if idx is None:
      return groups
    group = groups.pop(idx)
    bounded = max(0, min(to_index, len(groups)))
    groups.insert(bounded, group)
    return groups
