"""
Live data streaming — phone relays BLE packets to web dashboard.

Phase 1: Simple HTTP POST endpoint for batch upload of live packets.
Phase 2: WebSocket for true real-time streaming.
"""
from uuid import UUID
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db

router = APIRouter()


class LivePacket(BaseModel):
    """A single BLE packet relayed from the phone app."""
    device_id: str  # BLE MAC address
    player_id: Optional[UUID] = None
    timestamp: float  # Unix timestamp
    lat: Optional[float] = None
    lng: Optional[float] = None
    speed_kmh: Optional[float] = None
    intensity_1s: Optional[int] = None
    intensity_1min: Optional[int] = None
    battery_pct: Optional[int] = None
    bearing_deg: Optional[float] = None
    hdop: Optional[float] = None
    impact_count: Optional[int] = None


class LiveBatch(BaseModel):
    """Batch of packets from one or more devices."""
    match_id: UUID
    packets: list[LivePacket]


# In-memory store for active matches (Phase 1 — swap for Redis in prod)
_live_data: dict[str, list[LivePacket]] = {}  # match_id → recent packets


@router.post("/matches/{match_id}/live")
async def post_live_packets(
    match_id: UUID,
    batch: LiveBatch,
    db: AsyncSession = Depends(get_db),
):
    """
    Phone app posts BLE packets here for live dashboard viewing.
    Keeps last 300 packets per match in memory (5 min at 1Hz).
    """
    key = str(match_id)
    if key not in _live_data:
        _live_data[key] = []

    _live_data[key].extend(batch.packets)

    # Keep only last 300 packets per match
    if len(_live_data[key]) > 300:
        _live_data[key] = _live_data[key][-300:]

    return {"received": len(batch.packets), "buffered": len(_live_data[key])}


@router.get("/matches/{match_id}/live")
async def get_live_packets(
    match_id: UUID,
    since: Optional[float] = None,
    device_id: Optional[str] = None,
):
    """
    Dashboard polls this endpoint for live data.
    Optional filters: since (unix timestamp), device_id.
    """
    key = str(match_id)
    packets = _live_data.get(key, [])

    if since is not None:
        packets = [p for p in packets if p.timestamp > since]

    if device_id is not None:
        packets = [p for p in packets if p.device_id == device_id]

    return {
        "match_id": str(match_id),
        "packets": [p.model_dump() for p in packets],
        "count": len(packets),
        "server_time": datetime.utcnow().timestamp(),
    }


@router.delete("/matches/{match_id}/live")
async def clear_live_data(match_id: UUID):
    """Clear live data buffer for a match (match ended)."""
    key = str(match_id)
    _live_data.pop(key, None)
    return {"cleared": True}
