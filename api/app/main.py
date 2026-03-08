from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from .db import engine, Base, get_db
from .routers import matches, players, uploads, organizations, health, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
