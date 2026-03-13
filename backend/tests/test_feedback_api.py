"""Contract tests for feedback API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.feedback import FeedbackCreate, VALID_DIMENSIONS


class TestFeedbackCreateValidation:
    def test_valid_feedback(self):
        fb = FeedbackCreate(rating=1)
        assert fb.rating == 1

    def test_valid_with_overrides(self):
        fb = FeedbackCreate(rating=1, dimension_overrides={"clarity_score": 8})
        assert fb.dimension_overrides["clarity_score"] == 8

    def test_invalid_dimension_rejected(self):
        with pytest.raises(ValueError, match="Invalid dimension"):
            FeedbackCreate(rating=1, dimension_overrides={"invalid_dim": 5})

    def test_score_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="Score must be 1-10"):
            FeedbackCreate(rating=1, dimension_overrides={"clarity_score": 11})

    def test_invalid_rating_rejected(self):
        with pytest.raises(Exception):
            FeedbackCreate(rating=2)
