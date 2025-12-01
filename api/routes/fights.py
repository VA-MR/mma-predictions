"""Fight routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database
from api.auth import get_db
from api.schemas import FightResponse, FightWithStatsResponse
from api.converters import fight_to_response

router = APIRouter(prefix="/fights", tags=["Fights"])


@router.get("/{fight_id}", response_model=FightResponse)
async def get_fight(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get fight details by ID."""
    with db.get_session() as session:
        fight = db.get_fight_by_id(session, fight_id)
        
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        return fight_to_response(fight)


@router.get("/{fight_id}/stats", response_model=FightWithStatsResponse)
async def get_fight_stats(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get fight details with prediction and scorecard statistics."""
    with db.get_session() as session:
        fight = db.get_fight_by_id(session, fight_id)
        
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        # Get stats
        prediction_stats = db.get_fight_prediction_stats(session, fight_id)
        scorecard_stats = db.get_fight_scorecard_stats(session, fight_id)
        
        fight_response = fight_to_response(fight)
        
        return FightWithStatsResponse(
            **fight_response.model_dump(),
            prediction_stats=prediction_stats,
            scorecard_stats=scorecard_stats,
        )

