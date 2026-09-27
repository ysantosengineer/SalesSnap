from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.db.session import get_db_session
from app.models import User
from app.schemas.dataset_import import DatasetImportResponse, DatasetSummaryResponse
from app.services.dataset_import import (
    DatasetImportFailure,
    get_company_datasets,
    get_dataset,
    import_sales_dataset,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])
CSV_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}


@router.post("/import", response_model=DatasetImportResponse, status_code=status.HTTP_201_CREATED)
async def import_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetImportResponse:
    dataset_name = validate_csv_file(file)
    content = await file.read()
    if len(content) > get_settings().max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="CSV file exceeds the configured upload size limit",
        )
    try:
        return import_sales_dataset(session, current_user.company_id, dataset_name, content)
    except DatasetImportFailure as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"dataset_id": str(error.dataset_id), "message": error.message},
        ) from error


@router.get("", response_model=list[DatasetSummaryResponse])
def list_datasets(
    current_user: User = Depends(get_current_user), session: Session = Depends(get_db_session)
) -> list[DatasetSummaryResponse]:
    return [
        DatasetSummaryResponse(
            id=item.id, name=item.name, status=item.status, created_at=item.created_at
        )
        for item in get_company_datasets(session, current_user.company_id)
    ]


@router.get("/{dataset_id}", response_model=DatasetSummaryResponse)
def get_dataset_summary(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetSummaryResponse:
    try:
        import uuid

        parsed_id = uuid.UUID(dataset_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        ) from None
    dataset = get_dataset(session, current_user.company_id, parsed_id)
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return DatasetSummaryResponse(
        id=dataset.id, name=dataset.name, status=dataset.status, created_at=dataset.created_at
    )


def validate_csv_file(file: UploadFile) -> str:
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are supported",
        )
    if file.content_type and file.content_type not in CSV_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are supported",
        )
    return filename[:255]
