from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from app.api.deps import get_ai_generator
from app.core.ai.base import AIStyleGenerator
from app.core.models.ai import GeneratedStyleSpecResponse, PromptGenerateRequest

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger("styleagent.backend.ai")


class _SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        min_allowed = now - window_seconds

        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < min_allowed:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_rate_limiter = _SlidingWindowRateLimiter()


def _rate_limit_per_minute() -> int:
    raw = os.getenv("STYLEAGENT_AI_RATE_LIMIT_PER_MINUTE", "30").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 30


def _request_client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def reset_ai_rate_limiter_for_tests() -> None:
    _rate_limiter.reset()


@router.post(
    "/generate-style-spec",
    response_model=GeneratedStyleSpecResponse,
    summary="Generate StyleSpec From Prompt",
    description=(
        "Generate a Capture One-compatible `StyleSpec` from a natural-language prompt. "
        "Provider is selected through backend configuration (`mock` or local `ollama`)."
    ),
    response_description="Generated style specification and generation metadata.",
)
def generate_style_spec(
    request: Request,
    payload: PromptGenerateRequest = Body(..., description="Prompt-based generation payload."),
    generator: AIStyleGenerator = Depends(get_ai_generator),
) -> GeneratedStyleSpecResponse:
    client_key = _request_client_key(request)
    if not _rate_limiter.allow(client_key, _rate_limit_per_minute(), window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI generation rate limit exceeded. Please retry shortly.",
        )

    start = time.perf_counter()
    response = generator.generate_style_spec(payload)
    duration_ms = int((time.perf_counter() - start) * 1000)
    fallback_used = any("fallback mock used" in warning.lower() for warning in response.warnings)
    response.generation_ms = duration_ms
    response.fallback_used = fallback_used

    logger.info(
        "ai.generate provider=%s model=%s client=%s duration_ms=%s fallback=%s warnings=%s",
        response.provider,
        response.model,
        client_key,
        duration_ms,
        fallback_used,
        len(response.warnings),
    )
    return response
