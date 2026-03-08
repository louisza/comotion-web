from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import School, Team, Player
from ..schemas import SchoolCreate, SchoolOut, TeamCreate, TeamOut, PlayerCreate, PlayerOut

router = APIRouter()


# --- Schools ---

@router.post("/schools", response_model=SchoolOut, status_code=201)
async def create_school(body: SchoolCreate, db: AsyncSession = Depends(get_db)):
    # Check slug uniqueness
    existing = await db.execute(select(School).where(School.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="School slug already exists")
    school = School(name=body.name, slug=body.slug, province=body.province)
    db.add(school)
    await db.commit()
    await db.refresh(school)
    return school


@router.get("/schools", response_model=list[SchoolOut])
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).order_by(School.name))
    return result.scalars().all()


@router.get("/schools/{school_id}", response_model=SchoolOut)
async def get_school(school_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


# --- Teams ---

@router.post("/schools/{school_id}/teams", response_model=TeamOut, status_code=201)
async def create_team(school_id: UUID, body: TeamCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="School not found")
    team = Team(school_id=school_id, name=body.name, age_group=body.age_group, gender=body.gender, sport=body.sport, season_year=body.season_year)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("/schools/{school_id}/teams", response_model=list[TeamOut])
async def list_teams(school_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.school_id == school_id).order_by(Team.name))
    return result.scalars().all()


# --- Players ---

@router.post("/teams/{team_id}/players", response_model=PlayerOut, status_code=201)
async def create_player(team_id: UUID, body: PlayerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")
    player = Player(team_id=team_id, name=body.name, jersey_number=body.jersey_number, position=body.position, date_of_birth=body.date_of_birth)
    db.add(player)
    await db.commit()
    await db.refresh(player)
    return player


@router.get("/teams/{team_id}/players", response_model=list[PlayerOut])
async def list_players(team_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.team_id == team_id))
    return result.scalars().all()


@router.get("/players/{player_id}", response_model=PlayerOut)
async def get_player(player_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
