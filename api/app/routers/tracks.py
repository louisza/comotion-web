"""GPS track data endpoint — serves position/speed data from uploaded CSVs for map visualization."""
import csv
import io
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import Upload, PlayerMatchSummary
from ..processing import _parse_float, _parse_int, _strip_comments

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/comotion-uploads")

# Speed zone thresholds (km/h)
WALK_MAX = 5.0
JOG_MAX = 10.0
RUN_MAX = 15.0
HSR_MAX = 20.0
# Above HSR_MAX = sprint


@router.get("/matches/{match_id}/players/{player_id}/track")
async def get_player_track(
    match_id: UUID,
    player_id: UUID,
    quarter: int | None = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(get_db),
):
    """Return GPS track data for map visualization.

    Returns position points with speed zone classification,
    sprint segments, and zone coverage stats.
    """
    # Find the upload for this player+match
    result = await db.execute(
        select(Upload).where(
            Upload.match_id == match_id,
            Upload.player_id == player_id,
            Upload.status == "done",
        ).order_by(Upload.created_at.desc())
    )
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="No processed upload found for this player")

    filepath = os.path.join(UPLOAD_DIR, str(match_id), upload.filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Upload file not found on disk")

    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    reader = csv.DictReader(io.StringIO(_strip_comments(content)))
    columns = set(reader.fieldnames or [])

    has_filtered = "lat_filt" in columns and "lng_filt" in columns
    has_raw = "lat" in columns and "lng" in columns
    has_speed = "speed" in columns
    has_stale = "gps_stale" in columns

    if not (has_filtered or has_raw):
        return {"points": [], "sprints": [], "zones": {}, "bounds": None}

    # Parse all GPS points
    all_points = []
    first_ts = None
    last_ts = None

    for row in reader:
        ts_str = row.get("timestamp", "").strip()
        if not ts_str:
            continue
        try:
            ts = float(ts_str)
            # Convert ms to seconds
            if ts < 1e9:
                ts = ts / 1000.0
            elif ts > 1e12:
                ts = ts / 1000.0
        except ValueError:
            continue

        if first_ts is None:
            first_ts = ts
        last_ts = ts

        lat = _parse_float(row.get("lat_filt") or row.get("lat") if has_filtered or has_raw else None)
        lng = _parse_float(row.get("lng_filt") or row.get("lng") if has_filtered or has_raw else None)

        if abs(lat) < 0.001 or abs(lng) < 0.001:
            continue

        speed = _parse_float(row.get("speed")) if has_speed else 0.0
        stale = _parse_int(row.get("gps_stale"), 0) if has_stale else 0
        sats = _parse_int(row.get("sats"), 0)

        # Relative time in seconds from start
        rel_time = ts - first_ts if first_ts else 0.0

        # Speed zone classification
        if speed < WALK_MAX:
            zone = 0  # walk/standing
        elif speed < JOG_MAX:
            zone = 1  # jog
        elif speed < RUN_MAX:
            zone = 2  # run
        elif speed < HSR_MAX:
            zone = 3  # high-speed run
        else:
            zone = 4  # sprint

        all_points.append({
            "t": round(rel_time, 2),
            "lat": round(lat, 7),
            "lng": round(lng, 7),
            "spd": round(speed, 1),
            "z": zone,
            "s": stale,
        })

    if not all_points:
        return {"points": [], "sprints": [], "zones": {}, "bounds": None}

    # Quarter filtering
    total_duration = all_points[-1]["t"] - all_points[0]["t"] if len(all_points) > 1 else 0
    if quarter and total_duration > 0:
        q_duration = total_duration / 4
        q_start = (quarter - 1) * q_duration
        q_end = quarter * q_duration
        all_points = [p for p in all_points if q_start <= p["t"] <= q_end]

    if not all_points:
        return {"points": [], "sprints": [], "zones": {}, "bounds": None}

    # Downsample for performance (max ~2000 points for map rendering)
    MAX_POINTS = 2000
    if len(all_points) > MAX_POINTS:
        step = len(all_points) / MAX_POINTS
        sampled = []
        idx = 0.0
        while idx < len(all_points):
            sampled.append(all_points[int(idx)])
            idx += step
        # Always include last point
        if sampled[-1] != all_points[-1]:
            sampled.append(all_points[-1])
        all_points = sampled

    # Extract sprint segments (consecutive zone 4 points)
    sprints = []
    sprint_start = None
    sprint_points = []
    for p in all_points:
        if p["z"] >= 4:
            if sprint_start is None:
                sprint_start = p
                sprint_points = [p]
            else:
                sprint_points.append(p)
        else:
            if sprint_start and len(sprint_points) >= 2:
                sprints.append({
                    "start_t": sprint_start["t"],
                    "end_t": sprint_points[-1]["t"],
                    "duration": round(sprint_points[-1]["t"] - sprint_start["t"], 1),
                    "top_speed": round(max(sp["spd"] for sp in sprint_points), 1),
                    "start": {"lat": sprint_start["lat"], "lng": sprint_start["lng"]},
                    "end": {"lat": sprint_points[-1]["lat"], "lng": sprint_points[-1]["lng"]},
                })
            sprint_start = None
            sprint_points = []

    # Final sprint if still active
    if sprint_start and len(sprint_points) >= 2:
        sprints.append({
            "start_t": sprint_start["t"],
            "end_t": sprint_points[-1]["t"],
            "duration": round(sprint_points[-1]["t"] - sprint_start["t"], 1),
            "top_speed": round(max(sp["spd"] for sp in sprint_points), 1),
            "start": {"lat": sprint_start["lat"], "lng": sprint_start["lng"]},
            "end": {"lat": sprint_points[-1]["lat"], "lng": sprint_points[-1]["lng"]},
        })

    # Zone coverage (% of points in each zone)
    zone_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for p in all_points:
        zone_counts[p["z"]] = zone_counts.get(p["z"], 0) + 1
    total = len(all_points)
    zones = {
        "standing": round(zone_counts[0] / total * 100, 1),
        "walking": round(zone_counts[1] / total * 100, 1),
        "jogging": round(zone_counts[2] / total * 100, 1),
        "running": round(zone_counts[3] / total * 100, 1),
        "sprinting": round(zone_counts[4] / total * 100, 1),
    }

    # Bounds for map centering
    lats = [p["lat"] for p in all_points]
    lngs = [p["lng"] for p in all_points]
    bounds = {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lng": min(lngs),
        "max_lng": max(lngs),
        "center_lat": round(sum(lats) / len(lats), 7),
        "center_lng": round(sum(lngs) / len(lngs), 7),
    }

    return {
        "points": all_points,
        "sprints": sprints,
        "zones": zones,
        "bounds": bounds,
        "total_duration": round(total_duration, 1),
        "point_count": len(all_points),
    }
