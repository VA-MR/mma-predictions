"""Prediction routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from database import Database, User, PredictedWinner, WinMethod
from api.auth import get_db, get_current_user, require_auth
from api.schemas import PredictionCreate, PredictionResponse, PredictionStatsResponse
from api.converters import prediction_to_response

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    prediction_data: PredictionCreate,
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Create a new prediction for a fight.
    
    Predictions are immutable - once submitted, they cannot be changed.
    Only authenticated users can create predictions.
    """
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, prediction_data.fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {prediction_data.fight_id} not found",
            )
        
        # Check if user already has a prediction for this fight
        existing = db.get_user_prediction_for_fight(
            session, user.id, prediction_data.fight_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted a prediction for this fight. Predictions cannot be changed.",
            )
        
        # Create prediction
        try:
            prediction = db.create_prediction(
                session=session,
                user_id=user.id,
                fight_id=prediction_data.fight_id,
                predicted_winner=PredictedWinner(prediction_data.predicted_winner.value),
                win_method=WinMethod(prediction_data.win_method.value),
                confidence=prediction_data.confidence,
            )
            session.commit()
            
            # Reload with relationships
            session.refresh(prediction)
            
            return prediction_to_response(prediction, include_user=False)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )


@router.get("/fight/{fight_id}", response_model=List[PredictionResponse])
async def get_fight_predictions(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get all predictions for a specific fight."""
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        predictions = db.get_predictions_for_fight(session, fight_id)
        return [prediction_to_response(p) for p in predictions]


@router.get("/fight/{fight_id}/stats", response_model=PredictionStatsResponse)
async def get_fight_prediction_stats(
    fight_id: int,
    db: Database = Depends(get_db),
):
    """Get aggregated prediction statistics for a fight."""
    with db.get_session() as session:
        # Check if fight exists
        fight = db.get_fight_by_id(session, fight_id)
        if not fight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Fight with ID {fight_id} not found",
            )
        
        stats = db.get_fight_prediction_stats(session, fight_id)
        return PredictionStatsResponse(**stats)


@router.get("/mine", response_model=List[PredictionResponse])
async def get_my_predictions(
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Get all predictions made by the current user."""
    with db.get_session() as session:
        predictions = db.get_user_predictions(session, user.id)
        return [prediction_to_response(p, include_user=False, include_fight=True) for p in predictions]


@router.get("/mine/fight/{fight_id}", response_model=PredictionResponse)
async def get_my_fight_prediction(
    fight_id: int,
    user: User = Depends(require_auth),
    db: Database = Depends(get_db),
):
    """Get current user's prediction for a specific fight."""
    with db.get_session() as session:
        prediction = db.get_user_prediction_for_fight(session, user.id, fight_id)
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't made a prediction for this fight yet.",
            )
        
        return prediction_to_response(prediction, include_user=False)

