import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, DateTime, Date, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .db import Base


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    teams: Mapped[list["Team"]] = relationship(back_populates="organization")


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255))
    age_group: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    organization: Mapped["Organization"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    name: Mapped[str] = mapped_column(String(255))
    jersey_number: Mapped[int | None] = mapped_column(Integer)
    position: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    team: Mapped["Team"] = relationship(back_populates="players")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String(255))
    mac_address: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    match_date: Mapped[date] = mapped_column(Date)
    opponent: Mapped[str | None] = mapped_column(String(255))
    competition: Mapped[str | None] = mapped_column(String(255))
    venue: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, processing, ready, error
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Upload(Base):
    __tablename__ = "uploads"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"))
    player_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("players.id"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"))
    filename: Mapped[str] = mapped_column(String(500))
    storage_key: Mapped[str] = mapped_column(String(500))  # S3 key
    file_size_bytes: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")  # uploaded, validating, processing, done, error
    error_message: Mapped[str | None] = mapped_column(Text)
    quality_flags: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlayerMatchSummary(Base):
    __tablename__ = "player_match_summaries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"))
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


class PlayerMatchQuarterSummary(Base):
    __tablename__ = "player_match_quarter_summaries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id"))
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"))
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
