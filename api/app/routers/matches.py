from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Match, PlayerMatchSummary, PlayerMatchQuarterSummary
from ..schemas import MatchCreate, MatchOut, PlayerMatchSummaryOut

router = APIRouter()


@router.post("/matches", response_model=MatchOut)
async def create_match(body: MatchCreate, db: AsyncSession = Depends(get_db)):
    match = Match(**body.model_dump())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


@router.get("/matches", response_model=list[MatchOut])
async def list_matches(team_id: UUID | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Match).order_by(Match.match_date.desc())
    if team_id:
        q = q.where(Match.team_id == team_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/matches/{match_id}", response_model=MatchOut)
async def get_match(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Match).where(Match.id == match_id))
    return result.scalar_one()


@router.get("/matches/{match_id}/players", response_model=list[PlayerMatchSummaryOut])
async def get_match_players(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PlayerMatchSummary).where(PlayerMatchSummary.match_id == match_id)
    )
    return result.scalars().all()
