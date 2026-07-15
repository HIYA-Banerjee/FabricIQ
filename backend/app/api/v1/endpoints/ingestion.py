from fastapi import APIRouter, Depends, Header, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.ingestion_service import IngestionService
from app.core.config import settings
from typing import Optional

router = APIRouter()

@router.post("/upload")
async def upload_production_file(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Ingests orders from an Excel or CSV file.
    Performs data cleaning, validation, and registers new orders.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    contents = await file.read()
    
    res = IngestionService.process_file_upload(db, contents, file.filename, t_id)
    return res
