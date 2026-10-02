from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
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
UPLOAD_READ_CHUNK_BYTES = 64 * 1024
MAX_MULTIPART_OVERHEAD_BYTES = 64 * 1024


@router.post("/import", response_model=DatasetImportResponse, status_code=status.HTTP_201_CREATED)
async def import_csv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> DatasetImportResponse:
    enforce_rate_limit(
        request,
        "import",
        str(current_user.id),
        get_settings().rate_limit_import_per_minute,
    )
    dataset_name = validate_csv_file(file)
    max_upload_bytes = get_settings().max_upload_size_mb * 1024 * 1024
    reject_oversized_content_length(request, max_upload_bytes)
    content = await read_limited_upload(file, max_upload_bytes)
    try:
        return import_sales_dataset(session, current_user.company_id, dataset_name, content)
    except DatasetImportFailure as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"dataset_id": str(error.dataset_id), "message": error.message},
        ) from error


@router.get("", response_model=list[DatasetSummaryResponse])
def list_datasets(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> list[DatasetSummaryResponse]:
    return [
        DatasetSummaryResponse(
            id=item.id, name=item.name, status=item.status, created_at=item.created_at
        )
        for item in get_company_datasets(session, current_user.company_id, limit, offset)
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


def reject_oversized_content_length(request: Request, max_upload_bytes: int) -> None:
    content_length = request.headers.get("content-length")
    try:
        request_size = int(content_length) if content_length is not None else 0
    except ValueError:
        return
    if request_size > max_upload_bytes + MAX_MULTIPART_OVERHEAD_BYTES:
        raise file_too_large_error()


async def read_limited_upload(file: UploadFile, max_upload_bytes: int) -> bytes:
    chunks: list[bytes] = []
    received_bytes = 0
    while chunk := await file.read(UPLOAD_READ_CHUNK_BYTES):
        received_bytes += len(chunk)
        if received_bytes > max_upload_bytes:
            await file.close()
            raise file_too_large_error()
        chunks.append(chunk)
    return b"".join(chunks)


def file_too_large_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        detail="CSV file exceeds the configured upload size limit",
    )
