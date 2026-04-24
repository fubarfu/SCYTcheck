from __future__ import annotations


class GroupMutationService:
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
