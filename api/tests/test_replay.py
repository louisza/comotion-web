"""Integration tests for the match replay endpoint."""
import pytest


async def create_match_flow(client):
    """Helper: create school → team → match, return match id."""
    school = await client.post("/api/v1/schools", json={"name": "Test School", "slug": "test-school-replay"})
    assert school.status_code == 201
    school_id = school.json()["id"]

    team = await client.post(f"/api/v1/schools/{school_id}/teams", json={"name": "Test Team"})
    assert team.status_code == 201
    team_id = team.json()["id"]

    match = await client.post("/api/v1/matches", json={"team_id": team_id, "match_date": "2026-03-14"})
    assert match.status_code == 201
    return match.json()["id"]


@pytest.mark.anyio
async def test_replay_not_found(client):
    """Non-existent match → 404."""
    resp = await client.get("/api/v1/matches/00000000-0000-0000-0000-000000000000/replay")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_replay_no_uploads(client):
    """Match with no uploads → empty players."""
    match_id = await create_match_flow(client)
    resp = await client.get(f"/api/v1/matches/{match_id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["players"] == []
    assert data["duration"] == 0.0
    assert data["quarters"] == []


@pytest.mark.anyio
async def test_replay_structure(client):
    """Verify replay response has correct structure."""
    match_id = await create_match_flow(client)
    resp = await client.get(f"/api/v1/matches/{match_id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert "players" in data
    assert "duration" in data
    assert "quarters" in data
    assert isinstance(data["players"], list)
    assert isinstance(data["quarters"], list)
