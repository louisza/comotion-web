from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .db import engine, Base, get_db
from .routers import matches, players, uploads, organizations, health, auth, live, tracks
from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add columns that create_all can't add to existing tables
        for stmt in [
            "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS hardware_device_id VARCHAR(16)",
            "ALTER TABLE devices ADD COLUMN IF NOT EXISTS hardware_id VARCHAR(16)",
            "ALTER TABLE player_match_summaries ADD COLUMN IF NOT EXISTS track_data JSONB",
            "ALTER TABLE player_match_summaries ADD COLUMN IF NOT EXISTS device_id VARCHAR(16)",
            "ALTER TABLE matches ADD COLUMN IF NOT EXISTS start_time TIMESTAMP",
            "ALTER TABLE matches ADD COLUMN IF NOT EXISTS end_time TIMESTAMP",
            "ALTER TABLE matches ADD COLUMN IF NOT EXISTS quarters JSONB",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # Column may already exist or table missing
    yield

app = FastAPI(
    title="Comotion API",
    version="0.1.0",
    description="Coach analytics API for Comotion wearable tracker data",
    lifespan=lifespan,
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, tags=["auth"])
app.include_router(organizations.router, prefix="/api/v1", tags=["organizations"])
app.include_router(matches.router, prefix="/api/v1", tags=["matches"])
app.include_router(players.router, prefix="/api/v1", tags=["players"])
app.include_router(uploads.router, prefix="/api/v1", tags=["uploads"])
app.include_router(tracks.router, prefix="/api/v1", tags=["tracks"])
app.include_router(live.router, prefix="/api/v1", tags=["live"])
