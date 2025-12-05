"""Service for resolving predictions and scorecards against official fight results."""

from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session

from database.models import (
    Fight,
    FightResult,
    Prediction,
    Scorecard,
    RoundScore,
    OfficialScorecard,
    OfficialRoundScore,
    FightWinner,
    PredictedWinner,
)


def utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def resolve_predictions(session: Session, fight_id: int, fight_result: FightResult) -> int:
    """
    Resolve all predictions for a fight against the official result.
    
    A prediction is correct if:
    - predicted_winner matches result.winner (accounting for enum differences)
    - win_method matches result.method
    
    Args:
        session: Database session
        fight_id: ID of the fight
        fight_result: Official fight result
        
    Returns:
        Number of predictions resolved
    """
    # Get all predictions for this fight
    predictions = session.query(Prediction).filter(
        Prediction.fight_id == fight_id
    ).all()
    
    resolved_count = 0
    
    for prediction in predictions:
        # Map FightWinner to PredictedWinner for comparison
        if fight_result.winner == FightWinner.FIGHTER1:
            correct_winner = PredictedWinner.FIGHTER1
        elif fight_result.winner == FightWinner.FIGHTER2:
            correct_winner = PredictedWinner.FIGHTER2
        else:
            # Draw or No Contest - no predictions can be correct
            correct_winner = None
        
        # Check if prediction is correct
        if correct_winner is None:
            is_correct = False
        else:
            is_correct = (
                prediction.predicted_winner == correct_winner and
                prediction.win_method == fight_result.method
            )
        
        # Update prediction
        prediction.is_correct = is_correct
        prediction.resolved_at = utc_now()
        resolved_count += 1
    
    session.commit()
    return resolved_count


def resolve_scorecards(session: Session, fight_id: int, official_scorecards: List[OfficialScorecard]) -> int:
    """
    Resolve all user scorecards for a fight against official judge scorecards.
    
    A round is correct if the user's score for that round matches ANY of the 3 judges' scores.
    For example, if user scored round 1 as 10-9 fighter1, and at least one judge also scored
    it 10-9 fighter1, then that round is correct.
    
    Args:
        session: Database session
        fight_id: ID of the fight
        official_scorecards: List of official judge scorecards
        
    Returns:
        Number of scorecards resolved
    """
    # Get all user scorecards for this fight
    user_scorecards = session.query(Scorecard).filter(
        Scorecard.fight_id == fight_id
    ).all()
    
    if not official_scorecards:
        # No official scorecards to compare against
        return 0
    
    # Build a lookup of official scores by round
    # Structure: {round_number: [(f1_score, f2_score), ...]}
    official_scores_by_round = {}
    for official_scorecard in official_scorecards:
        for round_score in official_scorecard.round_scores:
            round_num = round_score.round_number
            if round_num not in official_scores_by_round:
                official_scores_by_round[round_num] = []
            official_scores_by_round[round_num].append(
                (round_score.fighter1_score, round_score.fighter2_score)
            )
    
    resolved_count = 0
    
    for user_scorecard in user_scorecards:
        correct_rounds = 0
        total_rounds = len(user_scorecard.round_scores)
        
        # Check each round score
        for user_round_score in user_scorecard.round_scores:
            round_num = user_round_score.round_number
            user_score = (user_round_score.fighter1_score, user_round_score.fighter2_score)
            
            # Check if this score matches any official judge's score for this round
            is_correct = False
            if round_num in official_scores_by_round:
                official_scores = official_scores_by_round[round_num]
                if user_score in official_scores:
                    is_correct = True
            
            # Update the round score
            user_round_score.is_correct = is_correct
            if is_correct:
                correct_rounds += 1
        
        # Update the scorecard summary
        user_scorecard.correct_rounds = correct_rounds
        user_scorecard.total_rounds = total_rounds
        user_scorecard.resolved_at = utc_now()
        resolved_count += 1
    
    session.commit()
    return resolved_count


def resolve_fight_result(session: Session, fight_result: FightResult) -> dict:
    """
    Resolve all predictions and scorecards for a fight.
    
    Args:
        session: Database session
        fight_result: The fight result to resolve against
        
    Returns:
        Dictionary with resolution statistics
    """
    fight_id = fight_result.fight_id
    
    # Resolve predictions
    predictions_resolved = resolve_predictions(session, fight_id, fight_result)
    
    # Resolve scorecards
    scorecards_resolved = resolve_scorecards(session, fight_id, fight_result.official_scorecards)
    
    # Mark the fight result as resolved
    fight_result.is_resolved = True
    session.commit()
    
    return {
        "predictions_resolved": predictions_resolved,
        "scorecards_resolved": scorecards_resolved,
        "fight_id": fight_id
    }

