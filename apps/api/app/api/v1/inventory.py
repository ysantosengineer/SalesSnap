from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.api.v1.datasets import read_limited_upload, validate_csv_file
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.schemas.inventory import InventoryImportSummary
from app.services.inventory_import import import_inventory_csv

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/import", response_model=InventoryImportSummary)
async def import_inventory(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> InventoryImportSummary:
    validate_csv_file(file)
    content = await read_limited_upload(file, get_settings().max_upload_size_mb * 1024 * 1024)
    try:
        return import_inventory_csv(session, current_user.company_id, content)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
