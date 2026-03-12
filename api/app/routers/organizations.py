from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..db import get_db
from ..models import School, Team, Player, Match
from ..schemas import SchoolCreate, SchoolUpdate, SchoolOut, SchoolWithCount, TeamCreate, TeamUpdate, TeamOut, TeamWithCount, PlayerCreate, PlayerOut

router = APIRouter()


# --- Schools ---

@router.post("/schools", response_model=SchoolOut, status_code=201)
async def create_school(body: SchoolCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(School).where(School.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="School slug already exists")
    school = School(name=body.name, slug=body.slug, province=body.province, logo_url=body.logo_url)
    db.add(school)
    await db.commit()
    await db.refresh(school)
    return school


@router.get("/schools", response_model=list[SchoolWithCount])
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).order_by(School.name))
    schools = result.scalars().all()
    out = []
    for s in schools:
        team_count_r = await db.execute(select(func.count()).where(Team.school_id == s.id))
        team_count = team_count_r.scalar_one()
        out.append(SchoolWithCount(
            id=s.id, name=s.name, slug=s.slug, logo_url=s.logo_url,
            province=s.province, created_at=s.created_at, team_count=team_count
        ))
    return out


@router.get("/schools/{school_id}", response_model=SchoolOut)
async def get_school(school_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.patch("/schools/{school_id}", response_model=SchoolOut)
async def update_school(school_id: UUID, body: SchoolUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    if body.name is not None:
        school.name = body.name
    if body.province is not None:
        school.province = body.province
    if body.logo_url is not None:
        school.logo_url = body.logo_url
    if body.slug is not None:
        # check uniqueness if slug changed
        if body.slug != school.slug:
            existing = await db.execute(select(School).where(School.slug == body.slug))
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="School slug already exists")
        school.slug = body.slug
    await db.commit()
    await db.refresh(school)
    return school


@router.delete("/schools/{school_id}", status_code=204)
async def delete_school(school_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    # Check for dependent matches (via teams)
    teams_r = await db.execute(select(Team.id).where(Team.school_id == school_id))
    team_ids = [t for t in teams_r.scalars().all()]
    if team_ids:
        match_count_r = await db.execute(select(func.count()).where(Match.team_id.in_(team_ids)))
        match_count = match_count_r.scalar_one()
        if match_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete school: {match_count} match(es) exist under its teams. Delete matches first."
            )
        # Delete orphan teams (no matches) before deleting school
        for tid in team_ids:
            team_obj = await db.get(Team, tid)
            if team_obj:
                await db.delete(team_obj)
    await db.delete(school)
    await db.commit()


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


@router.get("/schools/{school_id}/teams", response_model=list[TeamWithCount])
async def list_teams(school_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.school_id == school_id).order_by(Team.name))
    teams = result.scalars().all()
    out = []
    for t in teams:
        match_count_r = await db.execute(select(func.count()).where(Match.team_id == t.id))
        match_count = match_count_r.scalar_one()
        out.append(TeamWithCount(
            id=t.id, school_id=t.school_id, name=t.name, age_group=t.age_group,
            gender=t.gender, sport=t.sport, season_year=t.season_year,
            is_active=t.is_active, created_at=t.created_at, match_count=match_count
        ))
    return out


@router.get("/teams", response_model=list[TeamWithCount])
async def list_all_teams(db: AsyncSession = Depends(get_db)):
    """List all teams across all schools."""
    result = await db.execute(select(Team).order_by(Team.name))
    teams = result.scalars().all()
    out = []
    for t in teams:
        match_count_r = await db.execute(select(func.count()).where(Match.team_id == t.id))
        match_count = match_count_r.scalar_one()
        out.append(TeamWithCount(
            id=t.id, school_id=t.school_id, name=t.name, age_group=t.age_group,
            gender=t.gender, sport=t.sport, season_year=t.season_year,
            is_active=t.is_active, created_at=t.created_at, match_count=match_count
        ))
    return out


@router.patch("/schools/{school_id}/teams/{team_id}", response_model=TeamOut)
async def update_team(school_id: UUID, team_id: UUID, body: TeamUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id, Team.school_id == school_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if body.name is not None:
        team.name = body.name
    if body.age_group is not None:
        team.age_group = body.age_group
    if body.gender is not None:
        team.gender = body.gender
    if body.sport is not None:
        team.sport = body.sport
    if body.season_year is not None:
        team.season_year = body.season_year
    if body.is_active is not None:
        team.is_active = body.is_active
    await db.commit()
    await db.refresh(team)
    return team


@router.delete("/schools/{school_id}/teams/{team_id}", status_code=204)
async def delete_team(school_id: UUID, team_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id, Team.school_id == school_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    # Check for dependent matches
    match_count_r = await db.execute(select(func.count()).where(Match.team_id == team_id))
    match_count = match_count_r.scalar_one()
    if match_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete team: {match_count} match(es) exist. Delete matches first."
        )
    await db.delete(team)
    await db.commit()


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
