"""
Permission scoping — every data query goes through here.

Usage in routers:
    user = await get_current_user(request, db)
    scope = PermissionScope(db, user)
    teams = await scope.get_teams(school_id)        # filtered by role
    match = await scope.get_match(match_id)          # raises 403 if not allowed
"""
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    User, UserSchoolRole, CoachTeamAssignment, PlayerGuardian,
    School, Team, Player, Match, Upload, PlayerMatchSummary,
)


class PermissionScope:
    """Scopes all data access to what the current user is allowed to see."""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

    # ── Helpers ──

    async def _get_user_roles(self, school_id: UUID) -> list[UserSchoolRole]:
        result = await self.db.execute(
            select(UserSchoolRole).where(
                UserSchoolRole.user_id == self.user.id,
                UserSchoolRole.school_id == school_id,
            )
        )
        return list(result.scalars().all())

    async def _has_role(self, school_id: UUID, role: str) -> bool:
        roles = await self._get_user_roles(school_id)
        return any(r.role == role for r in roles)

    async def _get_coach_team_ids(self, school_id: UUID) -> set[UUID]:
        """Get team IDs a coach user is assigned to."""
        result = await self.db.execute(
            select(CoachTeamAssignment.team_id)
            .join(UserSchoolRole, CoachTeamAssignment.role_id == UserSchoolRole.id)
            .where(
                UserSchoolRole.user_id == self.user.id,
                UserSchoolRole.school_id == school_id,
                UserSchoolRole.role == "coach",
            )
        )
        return set(result.scalars().all())

    async def _get_player_ids_for_parent(self) -> set[UUID]:
        """Get player IDs linked to this parent user."""
        result = await self.db.execute(
            select(PlayerGuardian.player_id).where(PlayerGuardian.user_id == self.user.id)
        )
        return set(result.scalars().all())

    async def _get_player_id_for_user(self) -> UUID | None:
        """Get player record linked to this user account."""
        result = await self.db.execute(
            select(Player.id).where(Player.user_id == self.user.id)
        )
        return result.scalar_one_or_none()

    # ── School access ──

    async def get_schools(self) -> list[School]:
        """Schools the user has any role in."""
        if self.user.is_superadmin:
            result = await self.db.execute(select(School).order_by(School.name))
            return list(result.scalars().all())

        result = await self.db.execute(
            select(School)
            .join(UserSchoolRole, UserSchoolRole.school_id == School.id)
            .where(UserSchoolRole.user_id == self.user.id)
            .order_by(School.name)
        )
        return list(result.scalars().unique().all())

    async def require_school_access(self, school_id: UUID) -> School:
        """Verify user has any role at this school. Returns school or raises 403."""
        result = await self.db.execute(select(School).where(School.id == school_id))
        school = result.scalar_one_or_none()
        if not school:
            raise HTTPException(status_code=404, detail="School not found")

        if self.user.is_superadmin:
            return school

        roles = await self._get_user_roles(school_id)
        if not roles:
            raise HTTPException(status_code=403, detail="No access to this school")
        return school

    # ── Team access ──

    async def get_teams(self, school_id: UUID) -> list[Team]:
        """Teams the user can see at this school."""
        await self.require_school_access(school_id)

        if self.user.is_superadmin or await self._has_role(school_id, "school_admin"):
            result = await self.db.execute(
                select(Team).where(Team.school_id == school_id).order_by(Team.name)
            )
            return list(result.scalars().all())

        if await self._has_role(school_id, "coach"):
            team_ids = await self._get_coach_team_ids(school_id)
            result = await self.db.execute(
                select(Team).where(Team.id.in_(team_ids)).order_by(Team.name)
            )
            return list(result.scalars().all())

        # Player/parent: get teams through their player records
        return []  # TODO: derive from player.team_id

    async def require_team_access(self, team_id: UUID) -> Team:
        """Verify user can access this team."""
        result = await self.db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        if self.user.is_superadmin:
            return team

        school_id = team.school_id
        if await self._has_role(school_id, "school_admin"):
            return team

        if await self._has_role(school_id, "coach"):
            coach_teams = await self._get_coach_team_ids(school_id)
            if team_id in coach_teams:
                return team

        raise HTTPException(status_code=403, detail="No access to this team")

    # ── Match access ──

    async def get_matches(self, team_id: UUID | None = None, limit: int = 50) -> list[Match]:
        """Matches the user can see, optionally filtered by team."""
        q = select(Match).order_by(Match.match_date.desc()).limit(limit)

        if team_id:
            await self.require_team_access(team_id)
            q = q.where(Match.team_id == team_id)
        elif not self.user.is_superadmin:
            # Get all accessible team IDs across all schools
            role_result = await self.db.execute(
                select(UserSchoolRole).where(UserSchoolRole.user_id == self.user.id)
            )
            roles = list(role_result.scalars().all())

            accessible_team_ids: set[UUID] = set()
            for role in roles:
                if role.role == "school_admin":
                    team_result = await self.db.execute(
                        select(Team.id).where(Team.school_id == role.school_id)
                    )
                    accessible_team_ids.update(team_result.scalars().all())
                elif role.role == "coach":
                    coach_teams = await self._get_coach_team_ids(role.school_id)
                    accessible_team_ids.update(coach_teams)

            if not accessible_team_ids:
                return []
            q = q.where(Match.team_id.in_(accessible_team_ids))

        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def require_match_access(self, match_id: UUID) -> Match:
        """Verify user can access this match."""
        result = await self.db.execute(select(Match).where(Match.id == match_id))
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if self.user.is_superadmin:
            return match

        # Access through team
        await self.require_team_access(match.team_id)
        return match

    # ── Player data access ──

    async def get_player_summaries(self, match_id: UUID) -> list[PlayerMatchSummary]:
        """Player summaries for a match, filtered by access."""
        await self.require_match_access(match_id)

        q = select(PlayerMatchSummary).where(PlayerMatchSummary.match_id == match_id)

        # Parents/players: filter to only their player(s)
        # For now, coaches + admins see all players in the match
        # TODO: implement player-level filtering for parent/player roles

        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def can_upload(self, match_id: UUID) -> bool:
        """Only coaches and admins can upload data."""
        match = await self.require_match_access(match_id)
        result = await self.db.execute(select(Team).where(Team.id == match.team_id))
        team = result.scalar_one_or_none()
        if not team:
            return False

        if self.user.is_superadmin:
            return True
        if await self._has_role(team.school_id, "school_admin"):
            return True
        if await self._has_role(team.school_id, "coach"):
            return True
        return False
