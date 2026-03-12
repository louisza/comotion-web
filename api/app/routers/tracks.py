"""GPS track data endpoint — serves position/speed data from DB for map visualization."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import PlayerMatchSummary

router = APIRouter()


@router.get("/matches/{match_id}/players/{player_id}/track")
async def get_player_track(
    match_id: UUID,
    player_id: UUID,
    quarter: int | None = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(get_db),
):
    """Return GPS track data for map visualization from stored DB JSON."""
    result = await db.execute(
        select(PlayerMatchSummary).where(
            PlayerMatchSummary.match_id == match_id,
            PlayerMatchSummary.player_id == player_id,
        )
    )
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="No player summary found")

    track = summary.track_data
    if not track or not track.get("points"):
        return {"points": [], "sprints": [], "zones": {}, "bounds": None}

    # Quarter filtering
    if quarter:
        points = track["points"]
        total_duration = track.get("total_duration", 0)
        if total_duration > 0:
            q_dur = total_duration / 4
            q_start = (quarter - 1) * q_dur
            q_end = quarter * q_dur
            filtered = [p for p in points if q_start <= p["t"] <= q_end]
            track = {**track, "points": filtered, "point_count": len(filtered)}

    return track
