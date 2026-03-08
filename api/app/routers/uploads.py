from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from ..db import get_db
from ..models import Upload, Match
from ..schemas import UploadOut
from ..processing import process_upload

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/comotion-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/matches/{match_id}/upload", response_model=UploadOut)
async def upload_csv(
    match_id: UUID,
    player_id: UUID | None = None,
    device_id: UUID | None = None,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    # Verify match exists
    result = await db.execute(select(Match).where(Match.id == match_id))
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Validate file type
    if file.filename and not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Save file locally (swap to S3 in prod)
    storage_key = f"{match_id}/{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, str(match_id))
    os.makedirs(filepath, exist_ok=True)
    with open(os.path.join(filepath, file.filename), "wb") as f:
        f.write(content)

    upload = Upload(
        match_id=match_id,
        player_id=player_id,
        device_id=device_id,
        filename=file.filename or "unknown.csv",
        storage_key=storage_key,
        file_size_bytes=len(content),
        status="uploaded",
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    # Trigger background processing
    background_tasks.add_task(process_upload, upload.id)

    return upload


@router.get("/matches/{match_id}/uploads", response_model=list[UploadOut])
async def list_uploads(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Upload).where(Upload.match_id == match_id).order_by(Upload.created_at.desc())
    )
    return result.scalars().all()


@router.get("/uploads/{upload_id}", response_model=UploadOut)
async def get_upload(upload_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload
