import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, DateTime, Date, Text, ForeignKey, Boolean, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .db import Base


# ──────────────────────────────────────────────
# TENANT: School (top-level isolation boundary)
# ──────────────────────────────────────────────

class School(Base):
    """Top-level tenant. All data is scoped to a school."""
    __tablename__ = "schools"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # URL-friendly: "menlopark"
    logo_url: Mapped[str | None] = mapped_column(String(500))
    province: Mapped[str | None] = mapped_column(String(100))  # Gauteng, WC, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    teams: Mapped[list["Team"]] = relationship(back_populates="school", cascade="all, delete-orphan")
    devices: Mapped[list["Device"]] = relationship(back_populates="school", cascade="all, delete-orphan")
    user_roles: Mapped[list["UserSchoolRole"]] = relationship(back_populates="school", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# AUTH: User + Roles
# ──────────────────────────────────────────────

class User(Base):
    """Authenticated user (Google OAuth). Can have roles at multiple schools."""
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture_url: Mapped[str | None] = mapped_column(String(500))
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)  # Google subject ID
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)  # Platform admin (us)
    last_login: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    school_roles: Mapped[list["UserSchoolRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserSchoolRole(Base):
    """
    A user's role within a specific school.
    Roles: school_admin, coach, player, parent
    - school_admin: full access to all school data
    - coach: access to assigned teams only
    - player: access to own data only
    - parent: access to linked children's data only
    """
    __tablename__ = "user_school_roles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(50))  # school_admin, coach, player, parent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="school_roles")
    school: Mapped["School"] = relationship(back_populates="user_roles")

    # Coach-specific: which teams this coach can access
    team_assignments: Mapped[list["CoachTeamAssignment"]] = relationship(back_populates="role_entry", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "school_id", "role", name="uq_user_school_role"),
    )


class CoachTeamAssignment(Base):
    """Links a coach role to specific teams they can access."""
    __tablename__ = "coach_team_assignments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_school_roles.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    role_entry: Mapped["UserSchoolRole"] = relationship(back_populates="team_assignments")
    team: Mapped["Team"] = relationship()

    __table_args__ = (
        UniqueConstraint("role_id", "team_id", name="uq_coach_team"),
    )


class PlayerGuardian(Base):
    """Links a parent user to a player (their child). Parent can view child's data."""
    __tablename__ = "player_guardians"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), default="parent")  # parent, guardian
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
    player: Mapped["Player"] = relationship(back_populates="guardians")

    __table_args__ = (
        UniqueConstraint("user_id", "player_id", name="uq_guardian_player"),
    )


# ──────────────────────────────────────────────
# CORE: Team, Player, Device
# ──────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    age_group: Mapped[str | None] = mapped_column(String(50))  # U14, U16, U19, Open
    gender: Mapped[str | None] = mapped_column(String(10))  # M, F, Mixed
    sport: Mapped[str] = mapped_column(String(50), default="hockey")
    season_year: Mapped[int | None] = mapped_column(Integer)  # 2026
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    school: Mapped["School"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # Optional: link to user account
    name: Mapped[str] = mapped_column(String(255))
    jersey_number: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(50))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    team: Mapped["Team"] = relationship(back_populates="players")
    guardians: Mapped[list["PlayerGuardian"]] = relationship(back_populates="player", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    mac_address: Mapped[str | None] = mapped_column(String(50), unique=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    school: Mapped["School"] = relationship(back_populates="devices")


# ──────────────────────────────────────────────
# MATCH DATA
# ──────────────────────────────────────────────

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), index=True)
    match_date: Mapped[date] = mapped_column(Date)
    opponent: Mapped[str | None] = mapped_column(String(255))
    competition: Mapped[str | None] = mapped_column(String(255))
    venue: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, ready, error
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(500))
    storage_key: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    error_message: Mapped[str | None] = mapped_column(Text)
    quality_flags: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlayerMatchSummary(Base):
    __tablename__ = "player_match_summaries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), index=True)
    # Exposure
    minutes_played: Mapped[float | None] = mapped_column(Float)
    active_time_min: Mapped[float | None] = mapped_column(Float)
    # Running
    total_distance_m: Mapped[float | None] = mapped_column(Float)
    distance_per_min: Mapped[float | None] = mapped_column(Float)
    avg_speed_kmh: Mapped[float | None] = mapped_column(Float)
    top_speed_kmh: Mapped[float | None] = mapped_column(Float)
    hsr_distance_m: Mapped[float | None] = mapped_column(Float)
    sprint_count: Mapped[int | None] = mapped_column(Integer)
    # Explosive
    accel_count: Mapped[int | None] = mapped_column(Integer)
    decel_count: Mapped[int | None] = mapped_column(Integer)
    max_accel: Mapped[float | None] = mapped_column(Float)
    max_decel: Mapped[float | None] = mapped_column(Float)
    # Load
    total_load: Mapped[float | None] = mapped_column(Float)
    load_per_min: Mapped[float | None] = mapped_column(Float)
    peak_1min_intensity: Mapped[float | None] = mapped_column(Float)
    peak_3min_intensity: Mapped[float | None] = mapped_column(Float)
    peak_5min_intensity: Mapped[float | None] = mapped_column(Float)
    # Spatial
    avg_lat: Mapped[float | None] = mapped_column(Float)
    avg_lng: Mapped[float | None] = mapped_column(Float)
    # Impacts
    impact_count: Mapped[int | None] = mapped_column(Integer)
    movement_count: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_player"),
    )


class PlayerMatchQuarterSummary(Base):
    __tablename__ = "player_match_quarter_summaries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    quarter: Mapped[int] = mapped_column(Integer)  # 1-4
    minutes_played: Mapped[float | None] = mapped_column(Float)
    total_distance_m: Mapped[float | None] = mapped_column(Float)
    distance_per_min: Mapped[float | None] = mapped_column(Float)
    top_speed_kmh: Mapped[float | None] = mapped_column(Float)
    hsr_distance_m: Mapped[float | None] = mapped_column(Float)
    sprint_count: Mapped[int | None] = mapped_column(Integer)
    total_load: Mapped[float | None] = mapped_column(Float)
    accel_count: Mapped[int | None] = mapped_column(Integer)
    decel_count: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", "quarter", name="uq_match_player_quarter"),
    )
