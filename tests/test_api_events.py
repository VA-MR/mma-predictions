"""Tests for Events API endpoints."""

import pytest
from fastapi.testclient import TestClient
from database.models import Event


class TestListEvents:
    """Tests for listing events."""

    def test_list_events_empty(self, client: TestClient):
        """Test listing events when none exist."""
        response = client.get("/api/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_events_with_data(self, client: TestClient, sample_event):
        """Test listing events with data."""
        response = client.get("/api/events")
        assert response.status_code == 200
        events = response.json()
        assert len(events) >= 1
        assert any(e["slug"] == "test-event-1" for e in events)

    def test_list_events_upcoming_only(self, client: TestClient, test_db, db_session):
        """Test filtering for upcoming events only."""
        # Create a past event
        past_event = Event(
            name="Past Event",
            organization="UFC",
            slug="past-event",
            url="https://example.com/past",
            is_upcoming=False,
        )
        db_session.add(past_event)
        db_session.commit()

        # Create upcoming event
        upcoming_event = Event(
            name="Upcoming Event",
            organization="UFC",
            slug="upcoming-event",
            url="https://example.com/upcoming",
            is_upcoming=True,
        )
        db_session.add(upcoming_event)
        db_session.commit()

        # Default should only show upcoming
        response = client.get("/api/events")
        assert response.status_code == 200
        events = response.json()
        assert all(e["is_upcoming"] for e in events)

    def test_list_events_all(self, client: TestClient, test_db, db_session):
        """Test listing all events including past."""
        response = client.get("/api/events?upcoming_only=false")
        assert response.status_code == 200


class TestGetEvent:
    """Tests for getting single event."""

    def test_get_event_by_slug(self, client: TestClient, sample_event):
        """Test getting event by slug."""
        response = client.get(f"/api/events/{sample_event.slug}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_event.name
        assert data["slug"] == sample_event.slug
        assert "fights" in data

    def test_get_event_not_found(self, client: TestClient):
        """Test getting non-existent event."""
        response = client.get("/api/events/non-existent-slug")
        assert response.status_code == 404

    def test_get_event_with_fights(self, client: TestClient, sample_fight):
        """Test getting event includes its fights."""
        # sample_fight fixture creates event and fight
        response = client.get("/api/events/test-event-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["fights"]) >= 1


class TestAdminEvents:
    """Tests for admin event management."""

    def test_create_event(self, client: TestClient, admin_session: str):
        """Test creating a new event."""
        client.cookies.set("admin_session", admin_session)
        response = client.post(
            "/api/admin/events",
            json={
                "name": "New Test Event",
                "organization": "Bellator",
                "slug": "new-test-event",
                "url": "https://example.com/new-test",
                "location": "New York",
                "is_upcoming": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Test Event"
        assert data["organization"] == "Bellator"

    def test_update_event(self, client: TestClient, admin_session: str, sample_event):
        """Test updating an event."""
        client.cookies.set("admin_session", admin_session)
        response = client.put(
            f"/api/admin/events/{sample_event.id}",
            json={
                "name": "Updated Event Name",
                "organization": "UFC",
                "slug": sample_event.slug,
                "url": sample_event.url,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Event Name"

    def test_delete_event(self, client: TestClient, admin_session: str, db_session):
        """Test deleting an event."""
        # Create event to delete
        event = Event(
            name="Event to Delete",
            organization="UFC",
            slug="delete-me",
            url="https://example.com/delete",
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.id

        client.cookies.set("admin_session", admin_session)
        response = client.delete(f"/api/admin/events/{event_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

