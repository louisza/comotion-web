"""
Authentication — Google OAuth2 + JWT session tokens.

Flow:
1. Frontend redirects to /auth/google
2. Google redirects back with code
3. Backend exchanges code for token, creates/updates User, returns JWT
4. Frontend stores JWT in cookie/localStorage, sends as Bearer token
"""
import os
import time
from datetime import datetime
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_db
from .models import User

# Config
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "72"))


def create_token(user_id: UUID) -> str:
    """Create a JWT for an authenticated user."""
    payload = {
        "sub": str(user_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_HOURS * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """
    Extract and validate the current user from the request.
    Supports: Authorization: Bearer <token>
    
    In dev mode (no JWT_SECRET set or DEV_USER_ID set), returns a dev user.
    """
    # Dev bypass: if DEV_USER_ID is set, use that user directly
    dev_user_id = os.getenv("DEV_USER_ID")
    if dev_user_id:
        result = await db.execute(select(User).where(User.id == dev_user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth[7:]
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """Like get_current_user but returns None instead of 401 for unauthenticated requests."""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
