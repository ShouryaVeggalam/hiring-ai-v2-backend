"""Integration tests for key API endpoints."""
from __future__ import annotations

from app.core.config import settings


class TestDashboardAPI:
    def test_dashboard_requires_auth(self, client):
        resp = client.get(f"{settings.API_V1_PREFIX}/dashboard")
        assert resp.status_code == 401

    def test_dashboard_returns_kpis(self, client, auth_headers):
        resp = client.get(f"{settings.API_V1_PREFIX}/dashboard", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "open_roles" in data
        assert "hiring_health_score" in data
        assert "recent_activity" in data


class TestJobAPI:
    def test_create_and_list_jobs(self, client, auth_headers):
        resp = client.post(
            f"{settings.API_V1_PREFIX}/job/openings",
            headers=auth_headers,
            json={
                "title": "Data Scientist",
                "required_skills": ["python", "machine learning"],
            },
        )
        assert resp.status_code == 201
        job_id = resp.json()["id"]

        resp = client.get(f"{settings.API_V1_PREFIX}/job/openings", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_job_blueprint(self, client, auth_headers):
        resp = client.post(
            f"{settings.API_V1_PREFIX}/job/blueprint",
            headers=auth_headers,
            json={
                "title": "ML Engineer",
                "seniority": "senior",
                "must_have_skills": ["python", "pytorch"],
            },
            params={"persist": "false"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "pytorch" in resp.json()["output"]["required_skills"]


class TestWorkforceAPI:
    def test_workforce_analyze(self, client, auth_headers, db_session):
        from app.repositories.company import CompanyRepository, DepartmentRepository

        company = CompanyRepository(db_session).create(name="TestCo")
        DepartmentRepository(db_session).create(
            name="Product", company_id=company.id, headcount=3, target_headcount=8
        )
        db_session.commit()

        resp = client.post(
            f"{settings.API_V1_PREFIX}/workforce/analyze",
            headers=auth_headers,
            json={"company_id": company.id, "horizon_months": 6},
        )
        assert resp.status_code == 200
        assert resp.json()["output"]["total_headcount_gap"] == 5
