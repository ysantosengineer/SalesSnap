import logging
import re
import uuid
from time import perf_counter

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_context

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("sales_snap.requests")
app = FastAPI(title="SalesSnap API", debug=settings.debug)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    supplied_id = request.headers.get("x-request-id", "")
    request_id = supplied_id if REQUEST_ID_PATTERN.fullmatch(supplied_id) else str(uuid.uuid4())
    context_token = request_id_context.set(request_id)
    started_at = perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )
        return response
    finally:
        request_id_context.reset(context_token)


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
    expose_headers=["X-Request-ID"],
)
app.include_router(api_router)
