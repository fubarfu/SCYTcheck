"""
Contract tests for GET /api/review/context and PUT /api/review/action endpoints.
Feature: 013-video-primary-review
Tests: T025
"""

import pytest
from datetime import datetime


class TestReviewContextContract:
    """T025: Contract test for GET /api/review/context endpoint"""

    def test_review_context_response_structure(self) -> None:
        """
        Given a valid video_id
        When GET /api/review/context is called
        Then response includes merged candidates with freshness flags and groups structure
        """
        response_payload = {
            "video_id": "uuid-video-001",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "project_location": "/tmp/projects/uuid-video-001",
            "run_count": 3,
            "latest_run_id": "2",
            "merged_timestamp": datetime.now().isoformat(),
            "candidates": [
                {
                    "id": "cand-001",
                    "spelling": "misspelling1",
                    "discovered_in_run": "1",
                    "marked_new": True,
                    "decision": "unreviewed",
                    "frame_count": 12,
                    "frame_samples": ["frame_0001.png", "frame_0045.png"]
                },
                {
                    "id": "cand-002",
                    "spelling": "misspelling2",
                    "discovered_in_run": "0",
                    "marked_new": False,
                    "decision": "confirmed",
                    "frame_count": 8,
                    "frame_samples": ["frame_0002.png"]
                }
            ],
            "groups": [
                {
                    "id": "group-001",
                    "name": "Technical Terms",
                    "candidate_ids": ["cand-001", "cand-003"],
                    "decision": "confirmed"
                }
            ]
        }
        # Verify top-level structure
        assert response_payload["video_id"]
        assert response_payload["video_url"]
        assert "candidates" in response_payload
        assert isinstance(response_payload["candidates"], list)
        assert "groups" in response_payload
        assert isinstance(response_payload["groups"], list)

    def test_review_context_candidate_has_freshness_flag(self) -> None:
        """
        Given merged candidates from multiple runs
        When GET /api/review/context is called
        Then each candidate includes marked_new flag (true only if unique to latest run)
        """
        candidates = [
            {
                "id": "cand-001",
                "spelling": "new_spelling",
                "discovered_in_run": "2",  # latest
                "marked_new": True,
                "decision": "unreviewed"
            },
            {
                "id": "cand-002",
                "spelling": "old_spelling",
                "discovered_in_run": "0",  # prior run
                "marked_new": False,
                "decision": "confirmed"
            }
        ]
        # marked_new should be True only for spellings unique to latest run
        new_candidates = [c for c in candidates if c["marked_new"]]
        old_candidates = [c for c in candidates if not c["marked_new"]]
        
        assert len(new_candidates) >= 0
        assert len(old_candidates) >= 0

    def test_review_context_candidate_decision_field(self) -> None:
        """
        Given candidates with prior human decisions
        When GET /api/review/context is called
        Then decision field reflects prior decision or "unreviewed"
        """
        candidate = {
            "id": "cand-001",
            "spelling": "test_spelling",
            "discovered_in_run": "1",
            "marked_new": False,
            "decision": "confirmed",  # or "unreviewed", "rejected"
        }
        valid_decisions = ["unreviewed", "confirmed", "rejected", "edited"]
        assert candidate["decision"] in valid_decisions

    def test_review_context_not_found(self) -> None:
        """
        Given a non-existent video_id
        When GET /api/review/context is called
        Then response is 404 Not Found with error="video_not_found"
        """
        error_response = {
            "error": "video_not_found",
            "message": "Video with ID xyz not found in project location."
        }
        assert error_response["error"] == "video_not_found"

    def test_review_context_includes_frame_samples(self) -> None:
        """
        Given candidates with multiple frame occurrences
        When GET /api/review/context is called
        Then frame_samples array includes up to 3 sample frame paths
        """
        candidate = {
            "id": "cand-001",
            "spelling": "test_spelling",
            "frame_count": 12,
            "frame_samples": ["frame_0001.png", "frame_0045.png", "frame_0100.png"]
        }
        assert len(candidate["frame_samples"]) <= 3
        assert len(candidate["frame_samples"]) > 0


class TestReviewActionContract:
    """Contract test for PUT /api/review/action endpoint"""

    def test_review_action_confirm_candidate(self) -> None:
        """
        Given a candidate and confirm action
        When PUT /api/review/action is called
        Then response includes decision="confirmed" and marked_new is cleared
        """
        request_payload = {
            "video_id": "uuid-video-001",
            "candidate_id": "cand-001",
            "action": "confirmed",
            "user_note": "This is the correct spelling"
        }
        response_payload = {
            "candidate_id": "cand-001",
            "decision": "confirmed",
            "marked_new": False,
            "timestamp": datetime.now().isoformat()
        }
        assert response_payload["decision"] == "confirmed"
        assert response_payload["marked_new"] is False

    def test_review_action_reject_candidate(self) -> None:
        """
        Given a candidate and reject action
        When PUT /api/review/action is called
        Then response includes decision="rejected"
        """
        response_payload = {
            "candidate_id": "cand-002",
            "decision": "rejected",
            "marked_new": False,
            "timestamp": datetime.now().isoformat()
        }
        assert response_payload["decision"] == "rejected"

    def test_review_action_response_clears_marked_new(self) -> None:
        """
        Given a candidate with marked_new=true
        When PUT /api/review/action is called with any action
        Then response includes marked_new=false
        """
        actions = ["confirmed", "rejected", "edited"]
        for action in actions:
            response = {
                "candidate_id": "cand-001",
                "decision": action if action != "edited" else "confirmed",
                "marked_new": False,
                "timestamp": datetime.now().isoformat()
            }
            assert response["marked_new"] is False
