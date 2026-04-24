from __future__ import annotations

from src.web.app.recommendation_service import RecommendationService


def test_candidate_recommendation_respects_threshold() -> None:
    candidate = {"candidate_id": "c1", "status": "confirmed", "temporal_proximity": 90}
    scored = RecommendationService.score_candidate(candidate, recommendation_threshold=70)
    assert scored["recommendation_score"] >= 70
    assert scored["recommendation"] == "auto_confirm"


def test_group_recommendation_scores_all_candidates() -> None:
    groups = [
        {
            "group_id": "g1",
            "candidates": [
                {"candidate_id": "c1", "temporal_proximity": 50},
                {"candidate_id": "c2", "temporal_proximity": 80},
            ],
        }
    ]
    scored = RecommendationService.score_groups(groups, recommendation_threshold=90)
    assert len(scored[0]["candidates"]) == 2
    assert "group_recommendation_score" in scored[0]
