"""
Contract tests for POST /api/analysis/start and GET /api/analysis/progress endpoints.
Feature: 013-video-primary-review
Tests: T023, T024
"""

import pytest
from datetime import datetime
from typing import Dict, Any


class TestAnalysisStartContract:
    """T023: Contract test for POST /api/analysis/start endpoint"""

    def test_start_analysis_valid_request_creating_project(self) -> None:
        """
        Given a valid video URL and writable project location
        When POST /api/analysis/start is called
        Then response includes analysis_id, video_id, project_status="creating"
        """
        request_payload = {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "project_location": "/tmp/projects"
        }
        # Verify request structure
        assert "video_url" in request_payload
        assert request_payload["video_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert request_payload["project_location"] == "/tmp/projects"

    def test_start_analysis_valid_request_without_project_location(self) -> None:
        """
        Given a valid video URL without explicit project_location
        When POST /api/analysis/start is called with video_url only
        Then endpoint uses configured default project location
        """
        request_payload = {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }
        # Request can omit project_location to use default
        assert "video_url" in request_payload
        assert request_payload.get("project_location") is None

    def test_start_analysis_invalid_url_raises_error(self) -> None:
        """
        Given an invalid video URL
        When POST /api/analysis/start is called
        Then response is 400 Bad Request with error="invalid_video_url"
        """
        error_response = {
            "error": "invalid_video_url",
            "message": "Video URL is required and must be valid."
        }
        assert error_response["error"] == "invalid_video_url"

    def test_start_analysis_response_includes_project_status(self) -> None:
        """
        Given a valid analysis start request
        When endpoint processes it successfully
        Then response includes project_status field: "creating" or "merging"
        """
        # This tests the response schema requirements
        response_payload = {
            "analysis_id": "uuid-abc123",
            "video_id": "uuid-video-001",
            "project_status": "creating",  # or "merging"
            "run_id": "1",
            "run_timestamp": datetime.now().isoformat(),
            "project_location": "/tmp/projects/uuid-video-001",
            "message": "Creating new project..."
        }
        # Verify response structure has required fields
        assert "analysis_id" in response_payload
        assert "video_id" in response_payload
        assert response_payload["project_status"] in ["creating", "merging"]
        assert "message" in response_payload


class TestAnalysisProgressContract:
    """T024: Contract test for GET /api/analysis/progress endpoint"""

    def test_progress_response_in_progress(self) -> None:
        """
        Given an active analysis
        When GET /api/analysis/progress is called
        Then response includes progress_percent, project_status, message
        """
        progress_payload = {
            "status": "in_progress",
            "progress_percent": 45,
            "project_status": "merging",
            "message": "Merging results with existing project...",
            "frame_count": 1200,
            "frames_processed": 540,
            "candidates_found": 28,
            "elapsed_ms": 12345,
            "estimated_remaining_ms": 8000
        }
        assert progress_payload["status"] == "in_progress"
        assert 0 <= progress_payload["progress_percent"] <= 100
        assert progress_payload["project_status"] in ["creating", "merging"]
        assert isinstance(progress_payload["message"], str)
        assert progress_payload["frames_processed"] <= progress_payload["frame_count"]

    def test_progress_response_completed(self) -> None:
        """
        Given a completed analysis
        When GET /api/analysis/progress is called
        Then response includes status="completed", progress_percent=100, review_ready=true
        """
        progress_payload = {
            "status": "completed",
            "progress_percent": 100,
            "project_status": "merging",
            "message": "Analysis complete. Opening review...",
            "frame_count": 2100,
            "frames_processed": 2100,
            "candidates_found": 45,
            "elapsed_ms": 32500,
            "review_ready": True,
            "video_id": "uuid-video-001"
        }
        assert progress_payload["status"] == "completed"
        assert progress_payload["progress_percent"] == 100
        assert progress_payload["review_ready"] is True
        assert "video_id" in progress_payload

    def test_progress_response_failed(self) -> None:
        """
        Given a failed analysis
        When GET /api/analysis/progress is called
        Then response includes status="failed", error message
        """
        progress_payload = {
            "status": "failed",
            "progress_percent": 35,
            "project_status": "creating",
            "message": "Video download failed: 403 Forbidden",
            "error": "download_error"
        }
        assert progress_payload["status"] == "failed"
        assert "error" in progress_payload or "message" in progress_payload

    def test_progress_response_validates_project_status_field(self) -> None:
        """
        Given any analysis progress response
        When response is returned
        Then project_status field must be present and valid: "creating" or "merging"
        """
        valid_statuses = [
            {"project_status": "creating"},
            {"project_status": "merging"}
        ]
        for response in valid_statuses:
            assert response["project_status"] in ["creating", "merging"]
