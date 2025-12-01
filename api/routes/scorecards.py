"""Scorecard routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database, User
from api.auth import get_db, get_current_user, require_auth
from api.schemas import ScorecardCreate, ScorecardResponse, ScorecardStatsResponse
from api.converters import scorecard_to_response

router = APIRouter(prefix="/scorecards", tags=["Scorecards"])


@router.post("", response_model=ScorecardResponse, status_code=status.HTTP_201_CREATED)
async def create_scorecard(
    scorecard_data: ScorecardCreate,
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Create a new scorecard for a fight.
    
    Scorecards are immutable - once submitted, they cannot be changed.
    Only authenticated users can create scorecards.
    """
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, scorecard_data.fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {scorecard_data.fight_id} not found",
            )
        
        # Validate round scores match fight rounds
        expected_rounds = fight.rounds or 3
        if len(scorecard_data.round_scores) != expected_rounds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected {expected_rounds} round scores, got {len(scorecard_data.round_scores)}",
            )
        
        # Validate round numbers
        round_numbers = {rs.round_number for rs in scorecard_data.round_scores}
        expected_numbers = set(range(1, expected_rounds + 1))
        if round_numbers != expected_numbers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Round numbers must be {list(expected_numbers)}",
            )
        
        # Check if user already has a scorecard for this fight
        existing = db.get_user_scorecard_for_fight(
            session, user.id, scorecard_data.fight_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted a scorecard for this fight. Scorecards cannot be changed.",
            )
        
        # Create scorecard
        try:
            round_scores = [
                {
                    "round_number": rs.round_number,
                    "fighter1_score": rs.fighter1_score,
                    "fighter2_score": rs.fighter2_score,
                }
                for rs in scorecard_data.round_scores
            ]
            
            scorecard = db.create_scorecard(
                session=session,
                user_id=user.id,
                fight_id=scorecard_data.fight_id,
                round_scores=round_scores,
            )
            session.commit()
            
            # Reload with relationships
            session.refresh(scorecard)
            
            return scorecard_to_response(scorecard, include_user=False)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )


@router.get("/fight/{fight_id}", response_model=List[ScorecardResponse])
async def get_fight_scorecards(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get all scorecards for a specific fight."""
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        scorecards = db.get_scorecards_for_fight(session, fight_id)
        return [scorecard_to_response(sc) for sc in scorecards]


@router.get("/fight/{fight_id}/stats", response_model=ScorecardStatsResponse)
async def get_fight_scorecard_stats(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get aggregated scorecard statistics for a fight."""
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        stats = db.get_fight_scorecard_stats(session, fight_id)
        return ScorecardStatsResponse(**stats)


@router.get("/mine", response_model=List[ScorecardResponse])
async def get_my_scorecards(
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Get all scorecards submitted by the current user."""
    with db.get_session() as session:
        scorecards = db.get_user_scorecards(session, user.id)
        return [scorecard_to_response(sc, include_user=False, include_fight=True) for sc in scorecards]


@router.get("/mine/fight/{fight_id}", response_model=ScorecardResponse)
async def get_my_fight_scorecard(
    fight_id: int,
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Get current user's scorecard for a specific fight."""
    with db.get_session() as session:
        scorecard = db.get_user_scorecard_for_fight(session, user.id, fight_id)
        
        if not scorecard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't submitted a scorecard for this fight yet.",
            )
        
        return scorecard_to_response(scorecard, include_user=False)

