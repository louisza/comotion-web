from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import Optional


# --- Organizations ---
class OrgCreate(BaseModel):
    name: str

class OrgOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Teams ---
class TeamCreate(BaseModel):
    name: str
    age_group: Optional[str] = None

class TeamOut(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    age_group: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Players ---
class PlayerCreate(BaseModel):
    name: str
    jersey_number: Optional[int] = None
    position: Optional[str] = None

class PlayerOut(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    jersey_number: Optional[int]
    position: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Matches ---
class MatchCreate(BaseModel):
    team_id: UUID
    match_date: date
    opponent: Optional[str] = None
    competition: Optional[str] = None
    venue: Optional[str] = None

class MatchOut(BaseModel):
    id: UUID
    team_id: UUID
    match_date: date
    opponent: Optional[str]
    competition: Optional[str]
    venue: Optional[str]
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Uploads ---
class UploadOut(BaseModel):
    id: UUID
    match_id: UUID
    player_id: Optional[UUID]
    filename: str
    status: str
    row_count: Optional[int]
    quality_flags: Optional[dict]
    error_message: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Player Match Summary ---
class PlayerMatchSummaryOut(BaseModel):
    id: UUID
    match_id: UUID
    player_id: UUID
    minutes_played: Optional[float]
    total_distance_m: Optional[float]
    distance_per_min: Optional[float]
    top_speed_kmh: Optional[float]
    hsr_distance_m: Optional[float]
    sprint_count: Optional[int]
    accel_count: Optional[int]
    decel_count: Optional[int]
    total_load: Optional[float]
    load_per_min: Optional[float]
    peak_1min_intensity: Optional[float]
    peak_3min_intensity: Optional[float]
    peak_5min_intensity: Optional[float]
    impact_count: Optional[int]
    movement_count: Optional[int]
    model_config = {"from_attributes": True}
