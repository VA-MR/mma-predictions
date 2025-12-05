"""Pytest configuration and fixtures for MMA Scoring tests."""

import os
import pytest
from datetime import datetime, timezone
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment variables before importing app
os.environ["JWT_SECRET"] = "test-secret-key-for-testing"
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD"] = "testpass123"

from database.models import Base, Event, Fight, Fighter, User, Prediction, Scorecard
from database import Database
from api.main import app, get_database


# Test database setup
TEST_DB_PATH = "test_mma_data.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    # Cleanup after all tests
    Base.metadata.drop_all(engine)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Database, None, None]:
    """Create a test Database instance."""
    db = Database(TEST_DB_PATH)
    yield db


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database."""
    # Override the database dependency
    def override_get_database():
        return test_db
    
    from api.main import get_database
    from api.auth import get_db
    
    app.dependency_overrides[get_database] = override_get_database
    app.dependency_overrides[get_db] = override_get_database
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_fighter(db_session) -> Fighter:
    """Create a sample fighter for testing."""
    fighter = Fighter(
        name="Test Fighter",
        country="USA",
        wins=10,
        losses=2,
        draws=0,
    )
    db_session.add(fighter)
    db_session.commit()
    db_session.refresh(fighter)
    return fighter


@pytest.fixture
def sample_fighters(db_session) -> tuple[Fighter, Fighter]:
    """Create two sample fighters for testing."""
    fighter1 = Fighter(
        name="Fighter One",
        country="USA",
        wins=15,
        losses=3,
        draws=1,
    )
    fighter2 = Fighter(
        name="Fighter Two",
        country="Brazil",
        wins=12,
        losses=4,
        draws=0,
    )
    db_session.add(fighter1)
    db_session.add(fighter2)
    db_session.commit()
    db_session.refresh(fighter1)
    db_session.refresh(fighter2)
    return fighter1, fighter2


@pytest.fixture
def sample_event(db_session) -> Event:
    """Create a sample event for testing."""
    event = Event(
        name="Test Event 1",
        organization="UFC",
        slug="test-event-1",
        url="https://example.com/test-event-1",
        event_date=datetime(2025, 12, 15).date(),
        location="Las Vegas, NV",
        is_upcoming=True,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def sample_fight(db_session, sample_event, sample_fighters) -> Fight:
    """Create a sample fight for testing."""
    fighter1, fighter2 = sample_fighters
    fight = Fight(
        event_id=sample_event.id,
        fighter1_id=fighter1.id,
        fighter2_id=fighter2.id,
        card_type="main",
        weight_class="Lightweight",
        rounds=5,
        fight_order=1,
    )
    db_session.add(fight)
    db_session.commit()
    db_session.refresh(fight)
    return fight


@pytest.fixture
def sample_user(db_session) -> User:
    """Create a sample user for testing."""
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        auth_date=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_session(client) -> str:
    """Login as admin and return session cookie."""
    response = client.post(
        "/api/admin/login",
        json={"username": "testadmin", "password": "testpass123"}
    )
    assert response.status_code == 200
    return response.cookies.get("admin_session")

