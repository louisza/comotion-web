"""Tests for the Comotion API."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    async with client as c:
        res = await c.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["service"] == "comotion-api"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_create_org(client):
    async with client as c:
        res = await c.post("/api/v1/organizations", json={"name": "Test School"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Test School"
        assert "id" in data


@pytest.mark.asyncio
async def test_create_team_404(client):
    async with client as c:
        res = await c.post(
            "/api/v1/organizations/00000000-0000-0000-0000-000000000000/teams",
            json={"name": "U14A"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_matches_empty(client):
    async with client as c:
        res = await c.get("/api/v1/matches")
        assert res.status_code == 200
        assert res.json() == []


@pytest.mark.asyncio
async def test_get_match_404(client):
    async with client as c:
        res = await c.get("/api/v1/matches/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_upload_wrong_type(client):
    async with client as c:
        # Create org + team + match first
        org = (await c.post("/api/v1/organizations", json={"name": "Test"})).json()
        team = (await c.post(f"/api/v1/organizations/{org['id']}/teams", json={"name": "U14"})).json()
        match = (await c.post("/api/v1/matches", json={
            "team_id": team["id"],
            "match_date": "2026-03-08",
        })).json()

        # Try uploading non-CSV
        res = await c.post(
            f"/api/v1/matches/{match['id']}/upload",
            files={"file": ("test.txt", b"not a csv", "text/plain")},
        )
        assert res.status_code == 400
