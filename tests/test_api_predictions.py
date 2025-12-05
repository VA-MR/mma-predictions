"""Tests for Predictions API endpoints."""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from database.models import User, Prediction, PredictedWinner, WinMethod
from api.auth import create_access_token


class TestCreatePrediction:
    """Tests for creating predictions."""

    def test_create_prediction_success(self, client: TestClient, sample_fight, sample_user):
        """Test creating a prediction successfully."""
        # Create auth token for user
        token = create_access_token(sample_user.id, sample_user.telegram_id)
        
        response = client.post(
            "/api/predictions",
            json={
                "fight_id": sample_fight.id,
                "predicted_winner": "fighter1",
                "win_method": "ko_tko",
                "confidence": 4,
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["predicted_winner"] == "fighter1"
        assert data["win_method"] == "ko_tko"
        assert data["confidence"] == 4

    def test_create_prediction_without_auth(self, client: TestClient, sample_fight):
        """Test creating prediction without authentication."""
        response = client.post(
            "/api/predictions",
            json={
                "fight_id": sample_fight.id,
                "predicted_winner": "fighter1",
                "win_method": "ko_tko",
            }
        )
        assert response.status_code == 401

    def test_create_duplicate_prediction(self, client: TestClient, sample_fight, sample_user, db_session):
        """Test that duplicate predictions are rejected."""
        # Create existing prediction
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        db_session.add(prediction)
        db_session.commit()

        # Try to create another
        token = create_access_token(sample_user.id, sample_user.telegram_id)
        response = client.post(
            "/api/predictions",
            json={
                "fight_id": sample_fight.id,
                "predicted_winner": "fighter2",
                "win_method": "submission",
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 409
        assert "already" in response.json()["detail"].lower()

    def test_create_prediction_invalid_fight(self, client: TestClient, sample_user):
        """Test creating prediction for non-existent fight."""
        token = create_access_token(sample_user.id, sample_user.telegram_id)
        response = client.post(
            "/api/predictions",
            json={
                "fight_id": 99999,
                "predicted_winner": "fighter1",
                "win_method": "ko_tko",
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404


class TestGetPredictions:
    """Tests for getting predictions."""

    def test_get_fight_predictions(self, client: TestClient, sample_fight, sample_user, db_session):
        """Test getting all predictions for a fight."""
        # Create some predictions
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.DECISION,
        )
        db_session.add(prediction)
        db_session.commit()

        response = client.get(f"/api/predictions/fight/{sample_fight.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_prediction_stats(self, client: TestClient, sample_fight, db_session):
        """Test getting prediction statistics."""
        # Create a user and predictions
        user1 = User(
            telegram_id=111111,
            first_name="User1",
            auth_date=datetime.now(timezone.utc),
        )
        user2 = User(
            telegram_id=222222,
            first_name="User2",
            auth_date=datetime.now(timezone.utc),
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        pred1 = Prediction(
            user_id=user1.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.KO_TKO,
        )
        pred2 = Prediction(
            user_id=user2.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER2,
            win_method=WinMethod.SUBMISSION,
        )
        db_session.add(pred1)
        db_session.add(pred2)
        db_session.commit()

        response = client.get(f"/api/predictions/fight/{sample_fight.id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_predictions"] == 2
        assert data["fighter1_picks"] == 1
        assert data["fighter2_picks"] == 1
        assert data["fighter1_percentage"] == 50.0
        assert data["fighter2_percentage"] == 50.0

    def test_get_my_predictions(self, client: TestClient, sample_fight, sample_user, db_session):
        """Test getting current user's predictions."""
        # Create prediction
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER1,
            win_method=WinMethod.DECISION,
        )
        db_session.add(prediction)
        db_session.commit()

        token = create_access_token(sample_user.id, sample_user.telegram_id)
        response = client.get(
            "/api/predictions/mine",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_my_fight_prediction(self, client: TestClient, sample_fight, sample_user, db_session):
        """Test getting user's prediction for specific fight."""
        prediction = Prediction(
            user_id=sample_user.id,
            fight_id=sample_fight.id,
            predicted_winner=PredictedWinner.FIGHTER2,
            win_method=WinMethod.SUBMISSION,
        )
        db_session.add(prediction)
        db_session.commit()

        token = create_access_token(sample_user.id, sample_user.telegram_id)
        response = client.get(
            f"/api/predictions/mine/fight/{sample_fight.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["predicted_winner"] == "fighter2"
        assert data["win_method"] == "submission"

