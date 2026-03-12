"""Tests for the Comotion API."""
import pytest


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


@pytest.mark.asyncio
async def test_patch_match_404(client):
    async with client as c:
        res = await c.patch(
            "/api/v1/matches/00000000-0000-0000-0000-000000000000",
            json={"opponent": "Away Team"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_patch_match_partial_update(client):
    async with client as c:
        # Create a school, team and match
        school = (await c.post("/api/v1/schools", json={"name": "Test School", "slug": "test-school"})).json()
        team = (await c.post(f"/api/v1/schools/{school['id']}/teams", json={"name": "U14A"})).json()
        match = (await c.post("/api/v1/matches", json={
            "team_id": team["id"],
            "match_date": "2026-03-08",
            "opponent": "Old Opponent",
            "competition": "League",
            "venue": "Home Ground",
        })).json()

        # Patch only the opponent field
        res = await c.patch(f"/api/v1/matches/{match['id']}", json={"opponent": "New Opponent"})
        assert res.status_code == 200
        data = res.json()
        assert data["opponent"] == "New Opponent"
        # Unpatched fields must remain unchanged
        assert data["competition"] == "League"
        assert data["venue"] == "Home Ground"
        assert data["match_date"] == "2026-03-08"


@pytest.mark.asyncio
async def test_patch_match_clear_nullable_field(client):
    async with client as c:
        # Create a school, team and match with all optional fields set
        school = (await c.post("/api/v1/schools", json={"name": "Clear Test School", "slug": "clear-school"})).json()
        team = (await c.post(f"/api/v1/schools/{school['id']}/teams", json={"name": "U16B"})).json()
        match = (await c.post("/api/v1/matches", json={
            "team_id": team["id"],
            "match_date": "2026-04-01",
            "opponent": "Some Team",
            "competition": "Cup",
            "venue": "Away Ground",
        })).json()

        # Clear the nullable opponent and venue fields
        res = await c.patch(f"/api/v1/matches/{match['id']}", json={"opponent": None, "venue": None})
        assert res.status_code == 200
        data = res.json()
        assert data["opponent"] is None
        assert data["venue"] is None
        # competition was not patched and must remain
        assert data["competition"] == "Cup"
