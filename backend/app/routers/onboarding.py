"""Onboarding analytics router: fire-and-forget event tracking."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user
from app.models.onboarding_event import OnboardingEvent
from app.schemas.auth import AuthenticatedUser

router = APIRouter(tags=["onboarding"])


class OnboardingEventRequest(BaseModel):
    """Request body for POST /api/onboarding/events."""

    event_type: str = Field(..., max_length=64)
    metadata: dict | None = Field(default=None)


@router.post("/api/onboarding/events", status_code=201)
async def track_event(
    body: OnboardingEventRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Fire-and-forget event tracking for onboarding funnel analytics."""
    event = OnboardingEvent(
        user_id=current_user.id,
        event_type=body.event_type,
        metadata_=json.dumps(body.metadata) if body.metadata else None,
    )
    session.add(event)
    # Commit handled by get_session context manager
    return {"tracked": True}
