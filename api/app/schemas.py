from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import Optional


# --- Auth ---
class UserOut(BaseModel):
    id: UUID
    email: str
    name: str
    picture_url: Optional[str]
    is_superadmin: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class UserRoleOut(BaseModel):
    school_id: UUID
    school_name: str
    role: str
    team_ids: list[UUID] = []  # For coaches: assigned team IDs
    model_config = {"from_attributes": True}


# --- Schools ---
class SchoolCreate(BaseModel):
    name: str
    slug: str
    province: Optional[str] = None
    logo_url: Optional[str] = None

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    province: Optional[str] = None
    logo_url: Optional[str] = None

class SchoolOut(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: Optional[str]
    province: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class SchoolWithCount(SchoolOut):
    team_count: int = 0


# --- Teams ---
class TeamCreate(BaseModel):
    name: str
    age_group: Optional[str] = None
    gender: Optional[str] = None
    sport: str = "hockey"
    season_year: Optional[int] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    age_group: Optional[str] = None
    gender: Optional[str] = None
    sport: Optional[str] = None
    season_year: Optional[int] = None
    is_active: Optional[bool] = None

class TeamOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    age_group: Optional[str]
    gender: Optional[str]
    sport: str
    season_year: Optional[int]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class TeamWithCount(TeamOut):
    match_count: int = 0


# --- Players ---
class PlayerCreate(BaseModel):
    name: str
    jersey_number: Optional[int] = None
    position: Optional[str] = None
    date_of_birth: Optional[date] = None

class PlayerOut(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    jersey_number: Optional[int]
    position: Optional[str]
    date_of_birth: Optional[date]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Matches ---
class MatchCreate(BaseModel):
    team_id: UUID
    match_date: date
    opponent: Optional[str] = None
    competition: Optional[str] = None
    venue: Optional[str] = None

class MatchUpdate(BaseModel):
    match_date: Optional[date] = None
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
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    quarters: Optional[list] = None
    created_by: Optional[UUID]
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
    player_name: Optional[str] = None
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


# --- Roles ---
class InviteCreate(BaseModel):
    """Invite a user to a school with a specific role."""
    email: str
    role: str  # school_admin, coach, player, parent
    team_ids: list[UUID] = []  # Required for coach role

class CoachAssignmentCreate(BaseModel):
    team_id: UUID

class GuardianLinkCreate(BaseModel):
    player_id: UUID
