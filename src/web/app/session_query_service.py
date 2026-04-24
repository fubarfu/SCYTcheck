from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryFilters:
    search_text: str = ""
    status: str = "all"


class SessionQueryService:
    """Applies search and status filters to review candidates."""

    @staticmethod
    def filter_candidates(candidates: list[dict], filters: QueryFilters) -> list[dict]:
        search = filters.search_text.strip().lower()
        status = filters.status.strip().lower()

        filtered: list[dict] = []
        for candidate in candidates:
            name = str(
                candidate.get("corrected_text")
                or candidate.get("extracted_name")
                or ""
            ).lower()
            candidate_status = str(candidate.get("status", "pending")).lower()

            if search and search not in name:
                continue
            if status not in {"", "all"} and candidate_status != status:
                continue

            filtered.append(candidate)

        return filtered
