"""Event routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database
from api.auth import get_db
from api.schemas import EventResponse, EventDetailResponse
from api.converters import fight_to_response, event_to_response, get_main_event_info

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=List[EventResponse])
async def list_events(
    upcoming_only: bool = True,
    db: Database = Depends(get_db),
):
    """List all events.
    
    Args:
        upcoming_only: If True, only return upcoming events.
    """
    with db.get_session() as session:
        if upcoming_only:
            events = db.get_upcoming_events(session)
        else:
            events = db.get_all_events(session)
        
        return [event_to_response(event) for event in events]


@router.get("/{slug}", response_model=EventDetailResponse)
async def get_event(
    slug: str,
    db: Database = Depends(get_db),
):
    """Get event details by slug, including all fights."""
    with db.get_session() as session:
        event = db.get_event_by_slug(session, slug)
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with slug '{slug}' not found",
            )
        
        # Convert fights
        fights = [fight_to_response(fight) for fight in event.fights]
        
        return EventDetailResponse(
            id=event.id,
            name=event.name,
            organization=event.organization,
            event_date=event.event_date,
            time_msk=event.time_msk,
            location=event.location,
            is_upcoming=event.is_upcoming,
            slug=event.slug,
            url=event.url,
            fight_count=len(fights),
            fights=fights,
        )

