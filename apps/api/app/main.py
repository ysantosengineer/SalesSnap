from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="SalesSnap API", debug=settings.debug)


@app.middleware("http")
async def reject_large_dataset_requests(request: Request, call_next):
    """Reject obviously oversized imports before FastAPI parses multipart form data."""
    if request.url.path == "/api/v1/datasets/import":
        content_length = request.headers.get("content-length")
        max_upload_bytes = settings.max_upload_size_mb * 1024 * 1024
        try:
            request_size = int(content_length) if content_length is not None else 0
        except ValueError:
            request_size = 0
        if request_size > max_upload_bytes + 64 * 1024:
            return Response(status_code=status.HTTP_413_CONTENT_TOO_LARGE)
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
