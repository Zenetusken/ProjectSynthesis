"""Onboarding analytics event model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OnboardingEvent(Base):
    __tablename__ = "onboarding_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    # Event types: wizard_started, wizard_step_1..4, wizard_skipped, wizard_completed,
    #   walkthrough_started, walkthrough_step_N, walkthrough_completed,
    #   first_forge, milestone_achieved, tip_dismissed, checklist_item_N
    metadata_ = Column("metadata", Text, nullable=True)  # JSON string for step timing, context
    created_at = Column(DateTime, default=_utcnow, nullable=False)
