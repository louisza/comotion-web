from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from ..db import get_db
from ..models import Upload, Match
from ..schemas import UploadOut

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/comotion-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

    # Save file locally (swap to S3 in prod)
    content = await file.read()
    storage_key = f"{match_id}/{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, str(match_id))
    os.makedirs(filepath, exist_ok=True)
    with open(os.path.join(filepath, file.filename), "wb") as f:
        f.write(content)

    upload = Upload(
        match_id=match_id,
        player_id=player_id,
        device_id=device_id,
        filename=file.filename,
        storage_key=storage_key,
        file_size_bytes=len(content),
        status="uploaded",
    )
    db.add(upload)
    await db.commit()
    await db.refresh(upload)

    # TODO: background_tasks.add_task(process_csv, upload.id)

    return upload


@router.get("/matches/{match_id}/uploads", response_model=list[UploadOut])
async def list_uploads(match_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Upload).where(Upload.match_id == match_id))
    return result.scalars().all()
