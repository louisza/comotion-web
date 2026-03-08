from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db import get_db
from ..models import Organization, Team, Player
from ..schemas import OrgCreate, OrgOut, TeamCreate, TeamOut, PlayerCreate, PlayerOut

router = APIRouter()


@router.post("/organizations", response_model=OrgOut, status_code=201)
async def create_org(body: OrgCreate, db: AsyncSession = Depends(get_db)):
    org = Organization(name=body.name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/organizations", response_model=list[OrgOut])
async def list_orgs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).order_by(Organization.created_at))
    return result.scalars().all()


@router.get("/organizations/{org_id}", response_model=OrgOut)
async def get_org(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/organizations/{org_id}/teams", response_model=TeamOut, status_code=201)
async def create_team(org_id: UUID, body: TeamCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Organization not found")
    team = Team(org_id=org_id, name=body.name, age_group=body.age_group)
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


@router.get("/organizations/{org_id}/teams", response_model=list[TeamOut])
async def list_teams(org_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.org_id == org_id))
    return result.scalars().all()


@router.post("/teams/{team_id}/players", response_model=PlayerOut, status_code=201)
async def create_player(team_id: UUID, body: PlayerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Team not found")
    player = Player(team_id=team_id, name=body.name, jersey_number=body.jersey_number, position=body.position)
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
