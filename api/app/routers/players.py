from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Player, PlayerMatchSummary
from ..schemas import PlayerOut, PlayerMatchSummaryOut

router = APIRouter()


@router.get("/players/{player_id}/matches", response_model=list[PlayerMatchSummaryOut])
async def get_player_matches(player_id: UUID, db: AsyncSession = Depends(get_db)):
    # Verify player exists
    result = await db.execute(select(Player).where(Player.id == player_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Player not found")

    result = await db.execute(
        select(PlayerMatchSummary)
        .where(PlayerMatchSummary.player_id == player_id)
        .order_by(PlayerMatchSummary.match_id)
    )
    return result.scalars().all()
