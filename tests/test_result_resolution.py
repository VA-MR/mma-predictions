"""Tests for fight result resolution logic."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models import (
    Fight, FightResult, Prediction, Scorecard, RoundScore,
    OfficialScorecard, OfficialRoundScore,
    User, PredictedWinner, WinMethod, FightWinner,
)
from api.services.result_resolution import (
    resolve_predictions,
    resolve_scorecards,
    resolve_fight_result,
)


class TestResolvePredictions:
    """Tests for prediction resolution."""

    def test_correct_prediction_winner_and_method(self, db_session: Session, sample_fight, sample_user):
        """Test that correct winner + method prediction is marked correct."""
        # Create prediction
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        db_session.add(prediction)
        db_session.commit()

        # Create fight result
        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER1,
            method=WinMethod.KO_TKO,
            finish_round=2,
        )
        db_session.add(result)
        db_session.commit()

        # Resolve
        count = resolve_predictions(db_session, sample_fight.id, result)
        
        assert count == 1
        db_session.refresh(prediction)
        assert prediction.is_correct is True
        assert prediction.resolved_at is not None

    def test_wrong_winner_prediction(self, db_session: Session, sample_fight, sample_user):
        """Test that wrong winner prediction is marked incorrect."""
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        db_session.add(prediction)
        db_session.commit()

        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER2,  # Different winner
            method=WinMethod.KO_TKO,
        )
        db_session.add(result)
        db_session.commit()

        resolve_predictions(db_session, sample_fight.id, result)
        
        db_session.refresh(prediction)
        assert prediction.is_correct is False

    def test_wrong_method_prediction(self, db_session: Session, sample_fight, sample_user):
        """Test that wrong method prediction is marked incorrect."""
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        db_session.add(prediction)
        db_session.commit()

        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER1,  # Correct winner
            method=WinMethod.SUBMISSION,  # Different method
        )
        db_session.add(result)
        db_session.commit()

        resolve_predictions(db_session, sample_fight.id, result)
        
        db_session.refresh(prediction)
        assert prediction.is_correct is False

    def test_draw_result_marks_all_incorrect(self, db_session: Session, sample_fight, sample_user):
        """Test that draw result marks all predictions incorrect."""
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.DECISION,
        )
        db_session.add(prediction)
        db_session.commit()

        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.DRAW,
            method=WinMethod.DECISION,
        )
        db_session.add(result)
        db_session.commit()

        resolve_predictions(db_session, sample_fight.id, result)
        
        db_session.refresh(prediction)
        assert prediction.is_correct is False


class TestResolveScorecards:
    """Tests for scorecard resolution."""

    def test_correct_round_score(self, db_session: Session, sample_fight, sample_user):
        """Test that matching round score is marked correct."""
        # Create user scorecard
        scorecard = Scorecard(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
        )
        db_session.add(scorecard)
        db_session.commit()

        round_score = RoundScore(
            scorecard_id=scorecard.id,
            round_number=1,
            fighter1_score=10,
            fighter2_score=9,
        )
        db_session.add(round_score)
        db_session.commit()

        # Create fight result with official scorecard
        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER1,
            method=WinMethod.DECISION,
        )
        db_session.add(result)
        db_session.commit()

        official = OfficialScorecard(
            fight_result_id=result.id,
            judge_name="Judge 1",
        )
        db_session.add(official)
        db_session.commit()

        official_round = OfficialRoundScore(
            official_scorecard_id=official.id,
            round_number=1,
            fighter1_score=10,
            fighter2_score=9,
        )
        db_session.add(official_round)
        db_session.commit()

        # Resolve
        count = resolve_scorecards(db_session, sample_fight.id, [official])
        
        assert count == 1
        db_session.refresh(scorecard)
        db_session.refresh(round_score)
        assert round_score.is_correct is True
        assert scorecard.correct_rounds == 1
        assert scorecard.total_rounds == 1

    def test_wrong_round_score(self, db_session: Session, sample_fight, sample_user):
        """Test that non-matching round score is marked incorrect."""
        scorecard = Scorecard(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
        )
        db_session.add(scorecard)
        db_session.commit()

        round_score = RoundScore(
            scorecard_id=scorecard.id,
            round_number=1,
            fighter1_score=10,
            fighter2_score=9,
        )
        db_session.add(round_score)
        db_session.commit()

        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER2,
            method=WinMethod.DECISION,
        )
        db_session.add(result)
        db_session.commit()

        official = OfficialScorecard(
            fight_result_id=result.id,
            judge_name="Judge 1",
        )
        db_session.add(official)
        db_session.commit()

        # Different score
        official_round = OfficialRoundScore(
            official_scorecard_id=official.id,
            round_number=1,
            fighter1_score=9,
            fighter2_score=10,
        )
        db_session.add(official_round)
        db_session.commit()

        resolve_scorecards(db_session, sample_fight.id, [official])
        
        db_session.refresh(round_score)
        assert round_score.is_correct is False


class TestFullResolution:
    """Tests for complete fight result resolution."""

    def test_resolve_fight_result_marks_resolved(self, db_session: Session, sample_fight, sample_user):
        """Test that resolve_fight_result marks result as resolved."""
        # Create prediction
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        db_session.add(prediction)
        db_session.commit()

        # Create result
        result = FightResult(
            fight_id=sample_fight.id,
            winner=FightWinner.FIGHTER1,
            method=WinMethod.KO_TKO,
            is_resolved=False,
        )
        db_session.add(result)
        db_session.commit()

        # Resolve
        stats = resolve_fight_result(db_session, result)
        
        assert stats["predictions_resolved"] == 1
        assert stats["fight_id"] == sample_fight.id
        
        db_session.refresh(result)
        assert result.is_resolved is True

