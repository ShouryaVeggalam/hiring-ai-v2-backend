"""Integration tests for authentication."""
from __future__ import annotations

from app.core.config import settings


class TestAuth:
    def test_health_endpoint(self, client):
        resp = client.get(f"{settings.API_V1_PREFIX}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_login_success(self, client, admin_user):
        resp = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            json={"email": "admin@test.com", "password": "Test@12345"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self, client, admin_user):
        resp = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            json={"email": "admin@test.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_me_endpoint(self, client, auth_headers):
        resp = client.get(f"{settings.API_V1_PREFIX}/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@test.com"
        assert resp.json()["role"] == "admin"

    def test_unauthenticated_me(self, client):
        resp = client.get(f"{settings.API_V1_PREFIX}/auth/me")
        assert resp.status_code == 401
