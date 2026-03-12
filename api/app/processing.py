"""CSV processing pipeline — validates, cleans, and computes metrics from uploaded sensor data."""
import csv
import io
import math
import os
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import async_session
from .models import Upload, Match, Player, PlayerMatchSummary, PlayerMatchQuarterSummary

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")

# Expected CSV columns (from firmware SD card logging)
REQUIRED_COLUMNS = {"timestamp"}
OPTIONAL_COLUMNS = {
    "ax", "ay", "az", "gx", "gy", "gz",
    "lat", "lng", "lat_filt", "lng_filt",
    "speed", "course", "sats", "gps_stale",
    "audio_rms", "audio_peak", "audio_zcr",
    "event",
}

# Metric thresholds (defaults — will be configurable per org/age-group later)
HSR_THRESHOLD_KMH = 15.0       # High-speed running
SPRINT_THRESHOLD_KMH = 20.0    # Sprint
SPRINT_MIN_DURATION_S = 1.0
ACCEL_THRESHOLD_MS2 = 2.5      # m/s² for acceleration event
DECEL_THRESHOLD_MS2 = -2.5
MIN_SATELLITES = 4


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in metres between two GPS points."""
    R = 6371000.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class QualityFlags:
    def __init__(self):
        self.missing_timestamps = 0
        self.low_satellite_periods = 0
        self.impossible_speeds = 0
        self.impossible_jumps = 0
        self.total_rows = 0
        self.valid_gps_rows = 0

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "missing_timestamps": self.missing_timestamps,
            "low_satellite_periods": self.low_satellite_periods,
            "impossible_speeds": self.impossible_speeds,
            "impossible_jumps": self.impossible_jumps,
            "valid_gps_rows": self.valid_gps_rows,
            "gps_quality_pct": round(self.valid_gps_rows / max(self.total_rows, 1) * 100, 1),
        }


def _parse_float(val: str | None, default: float = 0.0) -> float:
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _parse_int(val: str | None, default: int = 0) -> int:
    if val is None or val.strip() == "":
        return default
    try:
        return int(float(val))
    except ValueError:
        return default


def _extract_metadata(content: str) -> dict[str, str]:
    """Extract metadata from comment lines (# key=value) before CSV header."""
    metadata = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            # Parse "# key=value" or "#key=value"
            kv = line.lstrip("#").strip()
            if "=" in kv:
                key, _, val = kv.partition("=")
                metadata[key.strip()] = val.strip()
        elif line:
            break  # Stop at first non-comment, non-empty line
    return metadata


def _strip_comments(content: str) -> str:
    """Remove leading comment lines from CSV content."""
    lines = content.splitlines(keepends=True)
    result = []
    past_comments = False
    for line in lines:
        if not past_comments and line.strip().startswith("#"):
            continue
        past_comments = True
        result.append(line)
    return "".join(result)


def _parse_rows(content: str) -> tuple[list[dict], set[str]]:
    """Parse CSV content, return list of row dicts and set of column names."""
    clean = _strip_comments(content)
    # Normalize line endings (strip \r that breaks column name matching)
    clean = clean.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(clean))
    # Strip whitespace from field names
    columns = set((f or "").strip() for f in (reader.fieldnames or []))
    reader.fieldnames = [f.strip() for f in (reader.fieldnames or [])]
    rows = list(reader)
    return rows, columns


def validate_csv(rows: list[dict], columns: set[str]) -> tuple[QualityFlags, list[str]]:
    """Stage 1+2: Validate and flag quality issues."""
    flags = QualityFlags()
    errors = []

    if not columns & REQUIRED_COLUMNS:
        errors.append(f"Missing required columns: {REQUIRED_COLUMNS - columns}")
        return flags, errors

    flags.total_rows = len(rows)
    if flags.total_rows == 0:
        errors.append("CSV file is empty (no data rows)")
        return flags, errors

    prev_ts = None
    for i, row in enumerate(rows):
        ts_str = row.get("timestamp", "").strip()
        if not ts_str:
            flags.missing_timestamps += 1
            continue

        # Check satellites
        sats = _parse_int(row.get("sats"), 0)
        if sats > 0 and sats < MIN_SATELLITES:
            flags.low_satellite_periods += 1

        # Check GPS validity
        lat = _parse_float(row.get("lat_filt") or row.get("lat"))
        lng = _parse_float(row.get("lng_filt") or row.get("lng"))
        if abs(lat) > 0.001 and abs(lng) > 0.001:
            flags.valid_gps_rows += 1

        # Check speed spikes
        speed = _parse_float(row.get("speed"))
        if speed > 50.0:  # 50 km/h is impossible for field hockey
            flags.impossible_speeds += 1

    return flags, errors


def compute_metrics(rows: list[dict], columns: set[str]) -> dict:
    """Stage 3+4: Compute derived metrics from cleaned rows."""
    has_filtered_gps = "lat_filt" in columns and "lng_filt" in columns
    has_raw_gps = "lat" in columns and "lng" in columns
    has_speed = "speed" in columns
    has_imu = "ax" in columns and "ay" in columns and "az" in columns

    total_distance = 0.0
    speeds = []
    accels = []
    positions = []
    load_sum = 0.0
    sprint_count = 0
    accel_count = 0
    decel_count = 0
    hsr_distance = 0.0
    in_sprint = False
    sprint_start = None

    prev_lat, prev_lng = None, None
    prev_speed = None
    prev_ts = None

    for row in rows:
        # Parse timestamp
        ts_str = row.get("timestamp", "").strip()
        if not ts_str:
            continue
        try:
            ts = float(ts_str)
            # Detect millisecond timestamps (uptime_ms from firmware)
            # If value looks like ms (> year 2000 in seconds but < year 2000 as ms),
            # or if it's clearly an uptime (< 1e9 which is ~31 years in seconds),
            # convert to seconds
            if ts < 1e9:
                # Uptime in ms (< ~31 years) — convert to seconds
                ts = ts / 1000.0
            elif ts > 1e12:
                # Unix epoch in ms — convert to seconds
                ts = ts / 1000.0
        except ValueError:
            try:
                ts = datetime.fromisoformat(ts_str).timestamp()
            except (ValueError, TypeError):
                continue

        dt = (ts - prev_ts) if prev_ts is not None else 0.0
        prev_ts = ts

        if dt <= 0 or dt > 10:  # skip gaps >10s
            prev_speed = None
            prev_lat, prev_lng = None, None
            continue

        # GPS position
        lat = _parse_float(row.get("lat_filt") or row.get("lat") if has_filtered_gps or has_raw_gps else None)
        lng = _parse_float(row.get("lng_filt") or row.get("lng") if has_filtered_gps or has_raw_gps else None)
        gps_stale = _parse_int(row.get("gps_stale"), 0)

        if abs(lat) > 0.001 and abs(lng) > 0.001:
            positions.append((lat, lng))
            # Only compute distance from fresh GPS fixes
            if prev_lat is not None and gps_stale == 0:
                d = haversine_m(prev_lat, prev_lng, lat, lng)
                if d < 50:  # reject jumps >50m in one sample
                    total_distance += d
                    # HSR contribution
                    speed_ms = d / dt
                    speed_kmh = speed_ms * 3.6
                    if speed_kmh >= HSR_THRESHOLD_KMH:
                        hsr_distance += d
            prev_lat, prev_lng = lat, lng

        # Speed from CSV
        speed = _parse_float(row.get("speed")) if has_speed else 0.0
        if speed < 50:
            speeds.append(speed)

        # Acceleration from speed
        if has_speed and prev_speed is not None and dt > 0:
            accel_ms2 = (speed / 3.6 - prev_speed / 3.6) / dt
            accels.append(accel_ms2)
            if accel_ms2 > ACCEL_THRESHOLD_MS2:
                accel_count += 1
            elif accel_ms2 < DECEL_THRESHOLD_MS2:
                decel_count += 1
        prev_speed = speed if speed < 50 else prev_speed

        # Sprint detection
        if speed >= SPRINT_THRESHOLD_KMH:
            if not in_sprint:
                in_sprint = True
                sprint_start = ts
        else:
            if in_sprint and sprint_start is not None:
                if (ts - sprint_start) >= SPRINT_MIN_DURATION_S:
                    sprint_count += 1
                in_sprint = False

        # IMU load (simplified: magnitude of acceleration vector minus gravity)
        if has_imu:
            ax = _parse_float(row.get("ax"))
            ay = _parse_float(row.get("ay"))
            az = _parse_float(row.get("az"))
            mag = math.sqrt(ax * ax + ay * ay + az * az)
            dynamic = abs(mag - 9.81)  # subtract gravity
            load_sum += dynamic * dt

    # Final sprint if still running
    if in_sprint and sprint_start is not None and prev_ts is not None:
        if (prev_ts - sprint_start) >= SPRINT_MIN_DURATION_S:
            sprint_count += 1

    # Compute summary
    first_ts = None
    last_ts = None
    for row in rows:
        ts_str = row.get("timestamp", "").strip()
        if ts_str:
            try:
                t = float(ts_str)
                if t < 1e9:
                    t = t / 1000.0
                elif t > 1e12:
                    t = t / 1000.0
            except ValueError:
                try:
                    t = datetime.fromisoformat(ts_str).timestamp()
                except (ValueError, TypeError):
                    continue
            if first_ts is None:
                first_ts = t
            last_ts = t

    minutes_played = (last_ts - first_ts) / 60.0 if first_ts and last_ts and last_ts > first_ts else 0.0

    # Average position
    avg_lat = sum(p[0] for p in positions) / len(positions) if positions else None
    avg_lng = sum(p[1] for p in positions) / len(positions) if positions else None

    # Rolling peaks (simplified: best N-minute window of distance/min)
    peak_1min = 0.0
    peak_3min = 0.0
    peak_5min = 0.0
    # TODO: implement proper rolling window peaks

    result = {
        "minutes_played": round(minutes_played, 1),
        "active_time_min": round(minutes_played, 1),  # TODO: filter idle time
        "total_distance_m": round(total_distance, 1),
        "distance_per_min": round(total_distance / max(minutes_played, 0.1), 1),
        "avg_speed_kmh": round(sum(speeds) / max(len(speeds), 1), 1),
        "top_speed_kmh": round(max(speeds) if speeds else 0.0, 1),
        "hsr_distance_m": round(hsr_distance, 1),
        "sprint_count": sprint_count,
        "accel_count": accel_count,
        "decel_count": decel_count,
        "max_accel": round(max(accels) if accels else 0.0, 2),
        "max_decel": round(min(accels) if accels else 0.0, 2),
        "total_load": round(load_sum, 1),
        "load_per_min": round(load_sum / max(minutes_played, 0.1), 1),
        "peak_1min_intensity": peak_1min,
        "peak_3min_intensity": peak_3min,
        "peak_5min_intensity": peak_5min,
        "avg_lat": avg_lat,
        "avg_lng": avg_lng,
        "impact_count": 0,  # populated below
        "movement_count": len(rows),
    }

    # Impact count from event/impact column
    has_event = "event" in columns
    has_impact = "impact" in columns
    impact_total = 0
    for row in rows:
        if has_impact:
            impact_total += _parse_int(row.get("impact"), 0)
        elif has_event:
            ev = (row.get("event") or "").strip().lower()
            if "impact" in ev:
                impact_total += 1
    result["impact_count"] = impact_total

    return result


# Speed zone thresholds (km/h) for track visualization
_WALK_MAX = 5.0
_JOG_MAX = 10.0
_RUN_MAX = 15.0
_HSR_MAX = 20.0

def compute_track_data(rows: list[dict], columns: set[str]) -> dict | None:
    """Compute GPS track data for map visualization. Returns JSON-serializable dict."""
    has_filtered = "lat_filt" in columns and "lng_filt" in columns
    has_raw = "lat" in columns and "lng" in columns
    has_speed = "speed" in columns
    has_stale = "gps_stale" in columns

    if not (has_filtered or has_raw):
        return None

    all_points = []
    first_ts = None

    for row in rows:
        ts_str = (row.get("timestamp") or "").strip()
        if not ts_str:
            continue
        try:
            ts = float(ts_str)
            if ts > 1e12:
                ts = ts / 1000.0
        except ValueError:
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                continue

        if first_ts is None:
            first_ts = ts

        lat = _parse_float(row.get("lat_filt") or row.get("lat"))
        lng = _parse_float(row.get("lng_filt") or row.get("lng"))

        if abs(lat) < 0.001 or abs(lng) < 0.001:
            continue

        speed = _parse_float(row.get("speed")) if has_speed else 0.0
        stale = _parse_int(row.get("gps_stale"), 0) if has_stale else 0
        rel_time = ts - first_ts if first_ts else 0.0

        if speed < _WALK_MAX:
            zone = 0
        elif speed < _JOG_MAX:
            zone = 1
        elif speed < _RUN_MAX:
            zone = 2
        elif speed < _HSR_MAX:
            zone = 3
        else:
            zone = 4

        all_points.append({
            "t": round(rel_time, 2),
            "lat": round(lat, 7),
            "lng": round(lng, 7),
            "spd": round(speed, 1),
            "z": zone,
            "s": stale,
        })

    if not all_points:
        return None

    # Downsample (max 2000 points)
    MAX_PTS = 2000
    if len(all_points) > MAX_PTS:
        step = len(all_points) / MAX_PTS
        sampled = []
        idx = 0.0
        while idx < len(all_points):
            sampled.append(all_points[int(idx)])
            idx += step
        if sampled[-1] != all_points[-1]:
            sampled.append(all_points[-1])
        all_points = sampled

    # Sprint segments
    sprints = []
    sprint_start = None
    sprint_pts = []
    for p in all_points:
        if p["z"] >= 4:
            if sprint_start is None:
                sprint_start = p
                sprint_pts = [p]
            else:
                sprint_pts.append(p)
        else:
            if sprint_start and len(sprint_pts) >= 2:
                sprints.append({
                    "start_t": sprint_start["t"],
                    "end_t": sprint_pts[-1]["t"],
                    "duration": round(sprint_pts[-1]["t"] - sprint_start["t"], 1),
                    "top_speed": round(max(sp["spd"] for sp in sprint_pts), 1),
                })
            sprint_start = None
            sprint_pts = []
    if sprint_start and len(sprint_pts) >= 2:
        sprints.append({
            "start_t": sprint_start["t"],
            "end_t": sprint_pts[-1]["t"],
            "duration": round(sprint_pts[-1]["t"] - sprint_start["t"], 1),
            "top_speed": round(max(sp["spd"] for sp in sprint_pts), 1),
        })

    # Zone coverage
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

    # Bounds
    lats = [p["lat"] for p in all_points]
    lngs = [p["lng"] for p in all_points]
    bounds = {
        "min_lat": min(lats), "max_lat": max(lats),
        "min_lng": min(lngs), "max_lng": max(lngs),
        "center_lat": round(sum(lats) / len(lats), 7),
        "center_lng": round(sum(lngs) / len(lngs), 7),
    }

    total_duration = all_points[-1]["t"] - all_points[0]["t"] if len(all_points) > 1 else 0

    return {
        "points": all_points,
        "sprints": sprints,
        "zones": zones,
        "bounds": bounds,
        "total_duration": round(total_duration, 1),
        "point_count": len(all_points),
    }


async def process_upload(upload_id: UUID):
    """Background task: process an uploaded CSV file."""
    async with async_session() as db:
        result = await db.execute(select(Upload).where(Upload.id == upload_id))
        upload = result.scalar_one_or_none()
        if not upload:
            return

        try:
            # Update upload + match status to processing
            upload.status = "processing"
            match_result_pre = await db.execute(select(Match).where(Match.id == upload.match_id))
            match_pre = match_result_pre.scalar_one_or_none()
            if match_pre and match_pre.status == "pending":
                match_pre.status = "processing"
            await db.commit()

            # Read file
            filepath = os.path.join(UPLOAD_DIR, str(upload.match_id), upload.filename)
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()

            # Extract device metadata from comment lines
            metadata = _extract_metadata(content)
            hw_id = metadata.get("device_id")
            if hw_id:
                try:
                    upload.hardware_device_id = hw_id
                except Exception:
                    pass  # Column may not exist yet in DB

            rows, columns = _parse_rows(content)

            # Validate
            flags, errors = validate_csv(rows, columns)
            upload.row_count = flags.total_rows
            upload.quality_flags = flags.to_dict()

            if errors:
                upload.status = "error"
                upload.error_message = "; ".join(errors)
                # Set match to error too
                match_val_err = await db.execute(select(Match).where(Match.id == upload.match_id))
                match_val = match_val_err.scalar_one_or_none()
                if match_val and match_val.status in ("pending", "processing"):
                    match_val.status = "error"
                await db.commit()
                return

            # Compute metrics
            metrics = compute_metrics(rows, columns)

            # Compute GPS track data for map visualization
            track = compute_track_data(rows, columns)

            # Resolve or create player
            player_id = upload.player_id
            if not player_id:
                # Try to get player name from CSV column first
                player_name_col = None
                if "player_name" in columns and rows:
                    first_name = (rows[0].get("player_name") or "").strip()
                    if first_name:
                        player_name_col = first_name

                match_result = await db.execute(select(Match).where(Match.id == upload.match_id))
                match_obj = match_result.scalar_one()
                label = player_name_col or upload.filename.replace(".CSV", "").replace(".csv", "")
                player = Player(
                    team_id=match_obj.team_id,
                    name=label,
                )
                db.add(player)
                await db.flush()
                player_id = player.id
                upload.player_id = player_id

            # Upsert player match summary
            existing = await db.execute(
                select(PlayerMatchSummary).where(
                    PlayerMatchSummary.match_id == upload.match_id,
                    PlayerMatchSummary.player_id == player_id,
                )
            )
            summary = existing.scalar_one_or_none()
            if summary:
                for k, v in metrics.items():
                    if hasattr(summary, k):
                        setattr(summary, k, v)
                summary.track_data = track
            else:
                summary = PlayerMatchSummary(
                    match_id=upload.match_id,
                    player_id=player_id,
                    track_data=track,
                    **{k: v for k, v in metrics.items() if hasattr(PlayerMatchSummary, k)},
                )
                db.add(summary)

            upload.status = "done"

            # Update match status to ready (all uploads processed)
            match_result_done = await db.execute(select(Match).where(Match.id == upload.match_id))
            match_done = match_result_done.scalar_one_or_none()
            if match_done:
                match_done.status = "ready"

            await db.commit()

        except Exception as e:
            upload.status = "error"
            upload.error_message = str(e)[:500]
            # Update match status to error
            try:
                match_err_result = await db.execute(select(Match).where(Match.id == upload.match_id))
                match_err = match_err_result.scalar_one_or_none()
                if match_err and match_err.status in ("pending", "processing"):
                    match_err.status = "error"
            except Exception:
                pass
            await db.commit()
