from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Match, Player, PlayerMatchSummary, PlayerMatchQuarterSummary
from ..schemas import MatchCreate, MatchOut, PlayerMatchSummaryOut

router = APIRouter()


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
