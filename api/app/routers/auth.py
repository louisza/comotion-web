"""
Google OAuth2 login flow.
Frontend redirects to /auth/google/login → Google → /auth/google/callback → JWT returned.
"""
import os
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import User
from ..auth import create_token

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/auth/google/login")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        "response_type=code&"
        "scope=openid email profile&"
        "access_type=offline"
    )
    return RedirectResponse(url)


@router.get("/auth/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange Google auth code for tokens, create/update user, return JWT."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google code")
        tokens = token_res.json()

        # Get user info
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")
        userinfo = userinfo_res.json()

    email = userinfo.get("email")
    google_sub = userinfo.get("sub")
    name = userinfo.get("name", email)
    picture = userinfo.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # Find or create user
    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if not user:
        # Try by email (pre-invited user)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user:
        user.name = name
        user.picture_url = picture
        user.google_sub = google_sub
        user.last_login = datetime.utcnow()
    else:
        user = User(
            email=email,
            name=name,
            picture_url=picture,
            google_sub=google_sub,
            last_login=datetime.utcnow(),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create JWT
    token = create_token(user.id)

    # Redirect to frontend with token
    return RedirectResponse(f"{FRONTEND_URL}/auth/callback?token={token}")


@router.get("/auth/me")
async def get_me(user: User = Depends(get_db)):
    """Get current authenticated user info."""
    # This needs the auth dependency — will be wired in later
    pass
