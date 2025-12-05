"""Tests for admin authentication system."""

import pytest
from fastapi.testclient import TestClient


class TestAdminLogin:
    """Tests for admin login endpoint."""

    def test_login_success(self, client: TestClient):
        """Test successful admin login."""
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "admin_session" in response.cookies

    def test_login_wrong_username(self, client: TestClient):
        """Test login with wrong username."""
        response = client.post(
            "/api/admin/login",
            json={"username": "wronguser", "password": "testpass123"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password."""
        response = client.post(
            "/api/admin/login",
            json={"username": "testadmin", "password": "wrongpass"}
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_login_empty_credentials(self, client: TestClient):
        """Test login with empty credentials."""
        response = client.post(
            "/api/admin/login",
            json={"username": "", "password": ""}
        )
        assert response.status_code == 401


class TestAdminLogout:
    """Tests for admin logout endpoint."""

    def test_logout_success(self, client: TestClient, admin_session: str):
        """Test successful admin logout."""
        client.cookies.set("admin_session", admin_session)
        response = client.post("/api/admin/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_logout_without_session(self, client: TestClient):
        """Test logout without active session."""
        response = client.post("/api/admin/logout")
        # Should still return success (idempotent)
        assert response.status_code == 200


class TestAdminMe:
    """Tests for admin session check endpoint."""

    def test_me_authenticated(self, client: TestClient, admin_session: str):
        """Test /me endpoint when authenticated."""
        client.cookies.set("admin_session", admin_session)
        response = client.get("/api/admin/me")
        assert response.status_code == 200
        assert response.json()["authenticated"] is True

    def test_me_not_authenticated(self, client: TestClient):
        """Test /me endpoint when not authenticated."""
        response = client.get("/api/admin/me")
        assert response.status_code == 401

    def test_me_invalid_session(self, client: TestClient):
        """Test /me endpoint with invalid session token."""
        client.cookies.set("admin_session", "invalid-token-12345")
        response = client.get("/api/admin/me")
        assert response.status_code == 401


class TestAdminRouteProtection:
    """Tests for admin route protection."""

    def test_protected_route_without_auth(self, client: TestClient):
        """Test accessing protected route without authentication."""
        response = client.get("/api/admin/fighters")
        assert response.status_code == 401

    def test_protected_route_with_auth(self, client: TestClient, admin_session: str):
        """Test accessing protected route with authentication."""
        client.cookies.set("admin_session", admin_session)
        response = client.get("/api/admin/fighters")
        assert response.status_code == 200

    def test_protected_post_without_auth(self, client: TestClient):
        """Test POST to protected route without authentication."""
        response = client.post(
            "/api/admin/fighters",
            json={"name": "New Fighter"}
        )
        assert response.status_code == 401

    def test_protected_delete_without_auth(self, client: TestClient):
        """Test DELETE on protected route without authentication."""
        response = client.delete("/api/admin/fighters/1")
        assert response.status_code == 401

