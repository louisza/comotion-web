from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Match, Player, PlayerMatchSummary, PlayerMatchQuarterSummary
from ..schemas import MatchCreate, MatchUpdate, MatchOut, PlayerMatchSummaryOut

router = APIRouter()

# Player colors for replay visualization
_PLAYER_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8C471", "#82E0AA", "#F1948A", "#AED6F1", "#D7BDE2",
]


@router.post("/matches", response_model=MatchOut, status_code=201)
async def create_match(body: MatchCreate, db: AsyncSession = Depends(get_db)):
    match = Match(**body.model_dump())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


@router.get("/matches", response_model=list[MatchOut])
async def list_matches(team_id: UUID | None = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    q = select(Match).order_by(Match.match_date.desc()).limit(limit)
    if team_id:
        q = q.where(Match.team_id == team_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/matches/{match_id}", response_model=MatchOut)
async def get_match(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.delete("/matches/{match_id}", status_code=204)
async def delete_match(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    await db.delete(match)
    await db.commit()


@router.patch("/matches/{match_id}", response_model=MatchOut)
async def update_match(match_id: UUID, body: MatchUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    update_data = body.model_dump(exclude_unset=True)
    # Prevent explicitly setting non-nullable match_date to None via PATCH
    if "match_date" in update_data and update_data["match_date"] is None:
        raise HTTPException(status_code=422, detail="match_date cannot be null")
    for field, value in update_data.items():
        setattr(match, field, value)
    await db.commit()
    await db.refresh(match)
    return match


@router.get("/matches/{match_id}/players", response_model=list[PlayerMatchSummaryOut])
async def get_match_players(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlayerMatchSummary).where(PlayerMatchSummary.match_id == match_id)
    )
    summaries = result.scalars().all()

    # Attach player names
    out = []
    for s in summaries:
        player_result = await db.execute(select(Player.name).where(Player.id == s.player_id))
        player_name = player_result.scalar_one_or_none()
        d = PlayerMatchSummaryOut.model_validate(s, from_attributes=True)
        d.player_name = player_name
        out.append(d)
    return out


@router.get("/matches/{match_id}/quarters")
async def get_match_quarters(match_id: UUID, player_id: UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(PlayerMatchQuarterSummary).where(PlayerMatchQuarterSummary.match_id == match_id)
    if player_id:
        q = q.where(PlayerMatchQuarterSummary.player_id == player_id)
    q = q.order_by(PlayerMatchQuarterSummary.quarter)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/matches/{match_id}/replay")
async def get_match_replay(match_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return all players' track data merged into a single timeline for replay visualization."""
    # Get match
    match_result = await db.execute(select(Match).where(Match.id == match_id))
    match = match_result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match_start_ts = match.start_time.timestamp() if match.start_time else None

    # Get all player summaries with track data
    result = await db.execute(
        select(PlayerMatchSummary).where(PlayerMatchSummary.match_id == match_id)
    )
    summaries = result.scalars().all()

    players = []
    max_duration = 0.0

    for i, s in enumerate(summaries):
        # Get player name
        player_result = await db.execute(select(Player.name).where(Player.id == s.player_id))
        player_name = player_result.scalar_one_or_none() or "Unknown"

        color = _PLAYER_COLORS[i % len(_PLAYER_COLORS)]

        points = []
        if s.track_data and "points" in s.track_data:
            raw_points = s.track_data["points"]
            # Points already have relative 't' from compute_track_data
            # If match_start_ts exists, points are already relative to player's first timestamp
            # For replay, we keep them as-is (relative to player start ≈ match start)
            for p in raw_points:
                points.append({
                    "t": p.get("t", 0),
                    "lat": p.get("lat"),
                    "lng": p.get("lng"),
                    "spd": p.get("spd", 0),
                    "z": p.get("z", 0),
                })
            if raw_points:
                player_dur = raw_points[-1].get("t", 0)
                if player_dur > max_duration:
                    max_duration = player_dur

        players.append({
            "player_id": str(s.player_id),
            "player_name": player_name,
            "color": color,
            "points": points,
        })

    # Quarters — adjust to relative time if match_start_ts available
    quarters = []
    if match.quarters:
        for q in match.quarters:
            q_start = q.get("start", 0)
            q_end = q.get("end", 0)
            if match_start_ts:
                q_start = q_start - match_start_ts
                q_end = q_end - match_start_ts
            quarters.append({"start": round(q_start, 2), "end": round(q_end, 2)})

    return {
        "players": players,
        "duration": round(max_duration, 1),
        "quarters": quarters,
    }
