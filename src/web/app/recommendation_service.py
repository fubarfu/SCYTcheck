from __future__ import annotations


class RecommendationService:
    @staticmethod
    def score_candidate(
        candidate: dict,
        recommendation_threshold: int = 70,
        validation_state: str | None = None,
    ) -> dict:
        base = 50.0
        temporal = float(candidate.get("temporal_proximity") or 0.0) * 0.3
        status_bonus = 20.0 if candidate.get("status") == "confirmed" else 0.0
        # Apply validation signal
        _vs = validation_state or candidate.get("validation_state")
        validation_bonus = 20.0 if _vs == "found" else (-10.0 if _vs == "not_found" else 0.0)
        score = min(100.0, max(0.0, base + temporal + status_bonus + validation_bonus))
        recommendation = "review"
        if score >= recommendation_threshold:
            recommendation = "auto_confirm"
        return {
            **candidate,
            "recommendation_score": round(score, 1),
            "recommendation": recommendation,
        }

    @staticmethod
    def score_groups(groups: list[dict], recommendation_threshold: int = 70) -> list[dict]:
        out = []
        for group in groups:
            scored = [
                RecommendationService.score_candidate(c, recommendation_threshold)
                for c in group.get("candidates", [])
            ]
            avg = sum(c["recommendation_score"] for c in scored) / max(1, len(scored))
            out.append(
                {
                    **group,
                    "candidates": scored,
                    "group_recommendation_score": round(avg, 1),
                }
            )
        return out
