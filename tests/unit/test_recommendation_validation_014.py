"""Unit tests for validation signal in recommendation_service (T016)."""
from __future__ import annotations

from src.web.app.recommendation_service import RecommendationService


def _base_score(validation_state: str | None = None, status: str = "pending") -> float:
    c = {"candidate_id": "c1", "status": status, "temporal_proximity": 0}
    scored = RecommendationService.score_candidate(c, validation_state=validation_state)
    return scored["recommendation_score"]


class TestValidationSignal:
    def test_found_adds_20_points(self):
        assert _base_score("found") == 70.0   # 50 + 20

    def test_not_found_subtracts_10_points(self):
        assert _base_score("not_found") == 40.0  # 50 - 10

    def test_unchecked_no_change(self):
        assert _base_score("unchecked") == 50.0

    def test_checking_no_change(self):
        assert _base_score("checking") == 50.0

    def test_failed_no_change(self):
        assert _base_score("failed") == 50.0

    def test_none_no_change(self):
        assert _base_score(None) == 50.0

    def test_found_with_confirmed_status_caps_at_100(self):
        c = {"candidate_id": "c1", "status": "confirmed", "temporal_proximity": 100}
        scored = RecommendationService.score_candidate(c, validation_state="found")
        assert scored["recommendation_score"] <= 100.0

    def test_not_found_with_zero_base_floors_at_0(self):
        # temporal=0, status=pending, not_found → 50-10=40 (still above 0; just check no negatives)
        c = {"candidate_id": "c1", "status": "pending", "temporal_proximity": 0}
        scored = RecommendationService.score_candidate(c, validation_state="not_found")
        assert scored["recommendation_score"] >= 0.0

    def test_validation_state_from_candidate_dict(self):
        """If no explicit validation_state arg, fall back to candidate.get('validation_state')."""
        c = {"candidate_id": "c1", "status": "pending", "temporal_proximity": 0, "validation_state": "found"}
        scored = RecommendationService.score_candidate(c)
        assert scored["recommendation_score"] == 70.0
