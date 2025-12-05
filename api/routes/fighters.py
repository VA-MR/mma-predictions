"""Fighter routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_

from database import Database
from api.auth import get_db
from api.schemas import FighterResponse, FightResponse
from api.converters import fighter_to_response, fight_to_response
from database.models import Fight

router = APIRouter(prefix="/fighters", tags=["Fighters"])


@router.get("/{fighter_id}", response_model=FighterResponse)
async def get_fighter(
    fighter_id: int,
    db: Database = Depends(get_db),
):
    """Get fighter details by ID."""
    with db.get_session() as session:
        fighter = db.get_fighter_by_id(session, fighter_id)
        
        if not fighter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fighter with ID {fighter_id} not found",
            )
        
        return fighter_to_response(fighter)


@router.get("/{fighter_id}/fights", response_model=List[FightResponse])
async def get_fighter_fights(
    fighter_id: int,
    limit: int = 10,
    db: Database = Depends(get_db),
):
    """Get recent fights for a fighter."""
    with db.get_session() as session:
        fighter = db.get_fighter_by_id(session, fighter_id)
        
        if not fighter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fighter with ID {fighter_id} not found",
            )
        
        # Get fights where this fighter participated
        from database.models import Event
        
        stmt = (
            select(Fight)
            .join(Event)
            .where(
                or_(
                    Fight.fighter1_id == fighter_id,
                    Fight.fighter2_id == fighter_id
                )
            )
            .order_by(Event.event_date.desc().nulls_last())
            .limit(limit)
        )
        
        fights = list(session.execute(stmt).scalars().all())
        
        return [fight_to_response(fight) for fight in fights]
