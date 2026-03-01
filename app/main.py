import logging
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import ai_router, artifacts_router, runner_router, styles_router

app = FastAPI(
    title="StyleAgent Backend API",
    version="0.9.0",
    description=(
        "Backend API for managing StyleAgent styles, versions, and Capture One artifacts. "
        "Includes compile/export flow, safe-policy enforcement, and artifact download."
    ),
)
logger = logging.getLogger("styleagent.backend")


def _allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS")
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def _request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def _error_response(
    request: Request,
    status_code: int,
    error_id: str,
    message: str,
    context: dict | None = None,
) -> JSONResponse:
    request_id = _request_id_from(request)
    payload_context = {"request_id": request_id}
    if context:
        payload_context.update(context)

    return JSONResponse(
        status_code=status_code,
        content={
            "error_id": error_id,
            "message": message,
            "context": payload_context,
        },
        headers={"X-Request-ID": request_id},
    )


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "%s %s -> %s [%s]",
        request.method,
        request.url.path,
        response.status_code,
        request_id,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    error_id = "http_error"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        error_id = "not_found"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        error_id = "bad_request"

    return _error_response(
        request=request,
        status_code=exc.status_code,
        error_id=error_id,
        message=str(exc.detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_id="validation_error",
        message="request validation failed",
        context={"errors": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error: %s", exc)
    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_id="internal_error",
        message="internal server error",
    )

app.include_router(styles_router)
app.include_router(artifacts_router)
app.include_router(runner_router)
app.include_router(ai_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/health",
    summary="Health Check",
    description="Simple liveness endpoint to verify the API process is running.",
    response_description="Service health status.",
)
def health():
    return {"status": "ok"}
