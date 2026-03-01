from __future__ import annotations

import logging
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from app.api.deps import get_ai_generator, get_store
from app.core.ai.base import AIStyleGenerator
from app.core.models import (
    AIChatSession,
    AIChatSessionCreateRequest,
    AIChatSessionDetail,
    AIChatTurn,
    AIChatTurnCreateRequest,
    AIChatTurnResponse,
    AIConversationGuidance,
    AIPromptPreviewResponse,
    AIParameterChange,
    StyleSpec,
)
from app.core.models.ai import AIGenerationRecord, GeneratedStyleSpecResponse, PromptGenerateRequest
from app.storage.base import Store

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
_PARAMETER_GUARDRAILS: dict[str, dict[str, float]] = {
    "Exposure": {"min": -4.0, "max": 4.0, "max_delta": 0.6},
    "Contrast": {"min": -100.0, "max": 100.0, "max_delta": 12.0},
    "Saturation": {"min": -100.0, "max": 100.0, "max_delta": 12.0},
    "Clarity": {"min": -100.0, "max": 100.0, "max_delta": 12.0},
    "Brightness": {"min": -100.0, "max": 100.0, "max_delta": 15.0},
    "Highlights": {"min": -100.0, "max": 100.0, "max_delta": 15.0},
    "Shadows": {"min": -100.0, "max": 100.0, "max_delta": 15.0},
    "WhiteBalanceTemperature": {"min": 2000.0, "max": 12000.0, "max_delta": 400.0},
    "WhiteBalanceTint": {"min": -50.0, "max": 50.0, "max_delta": 10.0},
    "ColorBalanceRed": {"min": -50.0, "max": 50.0, "max_delta": 8.0},
    "ColorBalanceGreen": {"min": -50.0, "max": 50.0, "max_delta": 8.0},
    "ColorBalanceBlue": {"min": -50.0, "max": 50.0, "max_delta": 8.0},
}


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


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _blocked_by_safe_policy(spec: StyleSpec, key: str) -> bool:
    safe = spec.safe
    if safe.remove_exposure and key == "Exposure":
        return True
    if safe.remove_white_balance and key in {"WhiteBalance", "WhiteBalanceTemperature", "WhiteBalanceTint"}:
        return True
    if safe.remove_lens_light_falloff and key == "LensLightFallOff":
        return True
    return False


def _derive_change_intents(message: str) -> dict[str, float]:
    text = message.lower()
    suggestions: dict[str, float] = {}

    if any(token in text for token in ("bright", "brighter", "lighter", "exposure up", "more exposure")):
        suggestions["Exposure"] = suggestions.get("Exposure", 0.0) + 0.2
    if any(token in text for token in ("dark", "darker", "moody", "less exposure")):
        suggestions["Exposure"] = suggestions.get("Exposure", 0.0) - 0.2
    if any(token in text for token in ("more contrast", "high contrast", "punchy")):
        suggestions["Contrast"] = suggestions.get("Contrast", 0.0) + 4.0
    if any(token in text for token in ("less contrast", "soft", "flat")):
        suggestions["Contrast"] = suggestions.get("Contrast", 0.0) - 4.0
    if any(token in text for token in ("vibrant", "colorful", "more saturation", "richer color")):
        suggestions["Saturation"] = suggestions.get("Saturation", 0.0) + 4.0
    if any(token in text for token in ("muted", "desaturated", "less saturation")):
        suggestions["Saturation"] = suggestions.get("Saturation", 0.0) - 4.0
    if any(token in text for token in ("crisp", "clear", "clarity up")):
        suggestions["Clarity"] = suggestions.get("Clarity", 0.0) + 3.0
    if any(token in text for token in ("softer texture", "less clarity", "clarity down")):
        suggestions["Clarity"] = suggestions.get("Clarity", 0.0) - 3.0
    if "cinematic" in text:
        suggestions["Contrast"] = suggestions.get("Contrast", 0.0) + 2.0
        suggestions["Saturation"] = suggestions.get("Saturation", 0.0) - 2.0
    if "warm" in text:
        suggestions["WhiteBalanceTemperature"] = suggestions.get("WhiteBalanceTemperature", 0.0) + 180.0
        suggestions["ColorBalanceRed"] = suggestions.get("ColorBalanceRed", 0.0) + 2.0
    if "cool" in text:
        suggestions["WhiteBalanceTemperature"] = suggestions.get("WhiteBalanceTemperature", 0.0) - 180.0
        suggestions["ColorBalanceBlue"] = suggestions.get("ColorBalanceBlue", 0.0) + 2.0
    if any(token in text for token in ("teal", "cyan")):
        suggestions["ColorBalanceBlue"] = suggestions.get("ColorBalanceBlue", 0.0) + 4.0
    if any(token in text for token in ("magenta", "pink")):
        suggestions["WhiteBalanceTint"] = suggestions.get("WhiteBalanceTint", 0.0) + 3.0
    if any(token in text for token in ("green tint", "green cast")):
        suggestions["WhiteBalanceTint"] = suggestions.get("WhiteBalanceTint", 0.0) - 3.0
    if any(token in text for token in ("recover highlights", "reduce highlights")):
        suggestions["Highlights"] = suggestions.get("Highlights", 0.0) - 5.0
    if any(token in text for token in ("lift shadows", "open shadows", "more shadow detail")):
        suggestions["Shadows"] = suggestions.get("Shadows", 0.0) + 5.0

    if not suggestions:
        suggestions["Contrast"] = 1.0

    return suggestions


def _derive_change_intents_from_ai(
    message: str,
    spec: StyleSpec,
    goals: list[str],
    generator: AIStyleGenerator,
) -> tuple[dict[str, float], list[str], str, str]:
    constraints = {
        "mode": "chat_turn_delta",
        "allowed_keys": sorted(_PARAMETER_GUARDRAILS.keys()),
        "current_keys": {
            key: float(value)
            for key, value in spec.captureone.keys.items()
            if key in _PARAMETER_GUARDRAILS and isinstance(value, (int, float))
        },
    }
    payload = PromptGenerateRequest(
        prompt=message,
        intent=goals or None,
        constraints=constraints,
        target="captureone",
    )
    response = generator.generate_style_spec(payload)

    suggestions: dict[str, float] = {}
    warnings = list(response.warnings)
    for key, value in response.style_spec.captureone.keys.items():
        if key not in _PARAMETER_GUARDRAILS:
            continue
        if not isinstance(value, (int, float)):
            warnings.append(f"Skipped non-numeric AI value for {key}.")
            continue
        current_raw = spec.captureone.keys.get(key, 0.0)
        if not isinstance(current_raw, (int, float)):
            warnings.append(f"Skipped {key}; current value is non-numeric.")
            continue
        delta = float(value) - float(current_raw)
        if delta != 0.0:
            suggestions[key] = delta

    if not suggestions:
        warnings.append("AI chat produced no supported deltas; heuristic fallback used.")
        return _derive_change_intents(message), warnings, response.provider, response.model

    return suggestions, warnings, response.provider, response.model


def _detect_conversation_goals(message: str) -> list[str]:
    text = message.lower()
    goals: list[str] = []
    if any(token in text for token in ("bright", "brighter", "lighter", "exposure up")):
        goals.append("increase_brightness")
    if any(token in text for token in ("dark", "darker", "moody", "less exposure")):
        goals.append("decrease_brightness")
    if any(token in text for token in ("contrast", "punchy")):
        goals.append("contrast_tuning")
    if any(token in text for token in ("vibrant", "colorful", "saturation", "muted", "desaturated")):
        goals.append("color_intensity_tuning")
    if any(token in text for token in ("warm", "cool", "temperature", "tint", "teal", "magenta")):
        goals.append("color_balance_tuning")
    if "cinematic" in text:
        goals.append("cinematic_look")
    if "portrait" in text:
        goals.append("portrait_balance")
    if not goals:
        goals.append("micro_adjustment")
    return goals


def _guidance_for_turn(goals: list[str], warnings: list[str], changes: list[AIParameterChange]) -> AIConversationGuidance:
    constrained = " with guard-rail constraints applied" if warnings else ""
    reasoning_summary = (
        f"Detected goals: {', '.join(goals)}. "
        f"Proposed {len(changes)} parameter changes{constrained}."
    )
    suggested_next_messages = [
        "make skin tones more natural",
        "reduce highlights and keep contrast",
        "add a softer cinematic finish",
        "cool shadows and keep warm skin tones",
    ]
    return AIConversationGuidance(
        detected_goals=goals,
        reasoning_summary=reasoning_summary,
        suggested_next_messages=suggested_next_messages,
    )


def _guardrail_changes(spec: StyleSpec, suggestions: dict[str, float]) -> tuple[list[AIParameterChange], list[str]]:
    changes: list[AIParameterChange] = []
    warnings: list[str] = []
    keys = spec.captureone.keys

    for key, delta in suggestions.items():
        guardrail = _PARAMETER_GUARDRAILS.get(key)
        if guardrail is None:
            warnings.append(f"Skipped unsupported key: {key}")
            continue
        if _blocked_by_safe_policy(spec, key):
            warnings.append(f"Skipped {key} due to safe policy.")
            continue

        current_raw = keys.get(key, 0.0)
        if not isinstance(current_raw, (int, float)):
            warnings.append(f"Skipped {key}; current value is non-numeric.")
            continue

        adjusted_delta = float(delta)
        max_delta = guardrail["max_delta"]
        if abs(adjusted_delta) > max_delta:
            adjusted_delta = max_delta if adjusted_delta > 0 else -max_delta
            warnings.append(f"Capped {key} delta to {adjusted_delta}.")

        target = float(current_raw) + adjusted_delta
        clamped = _clamp(target, guardrail["min"], guardrail["max"])
        if clamped != target:
            warnings.append(f"Clamped {key} to allowed range [{guardrail['min']}, {guardrail['max']}].")

        changes.append(
            AIParameterChange(
                key=key,
                from_value=float(current_raw),
                to_value=clamped,
                reason="Conversation-guided adjustment",
            )
        )

    return changes, warnings


def _apply_parameter_changes(spec: StyleSpec, changes: list[AIParameterChange]) -> StyleSpec:
    updated = spec.model_copy(deep=True)
    for change in changes:
        updated.captureone.keys[change.key] = change.to_value
    return updated


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
    store: Store = Depends(get_store),
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

    try:
        store.create_ai_generation(
            AIGenerationRecord(
                client_key=client_key,
                prompt=payload.prompt,
                intent=payload.intent,
                constraints=payload.constraints,
                target=payload.target,
                style_spec=response.style_spec,
                rationale=response.rationale,
                warnings=response.warnings,
                provider=response.provider,
                model=response.model,
                generation_ms=response.generation_ms,
                fallback_used=response.fallback_used,
            )
        )
    except Exception:  # noqa: BLE001
        logger.exception("ai.generate persistence_failed client=%s", client_key)
        response.warnings.append("Generation saved failed; result returned without history persistence.")

    return response


@router.get(
    "/generations",
    response_model=list[AIGenerationRecord],
    summary="List AI Generations",
    description="Return persisted AI generation history records, newest first.",
    response_description="AI generation history records.",
)
def list_ai_generations(
    limit: int = Query(
        default=20,
        ge=1,
        le=200,
        description="Maximum number of generation records to return.",
    ),
    store: Store = Depends(get_store),
) -> list[AIGenerationRecord]:
    return store.list_ai_generations(limit=limit)


@router.post(
    "/debug/prompt-preview",
    response_model=AIPromptPreviewResponse,
    summary="Preview AI Provider Prompt",
    description=(
        "Render the provider-specific prompt that would be sent for a generation request, "
        "including selected in-context examples."
    ),
    response_description="Prompt preview and selected example metadata.",
)
def preview_ai_prompt(
    payload: PromptGenerateRequest = Body(..., description="Prompt payload to preview."),
    generator: AIStyleGenerator = Depends(get_ai_generator),
) -> AIPromptPreviewResponse:
    return generator.preview_prompt(payload)


@router.post(
    "/chat/sessions",
    response_model=AIChatSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI Chat Session",
    description="Create a chat-guided AI session starting from a base style spec.",
)
def create_ai_chat_session(
    payload: AIChatSessionCreateRequest = Body(..., description="AI chat session create payload."),
    store: Store = Depends(get_store),
) -> AIChatSession:
    session = AIChatSession(title=payload.title, style_spec=payload.style_spec)
    return store.create_ai_chat_session(session)


@router.get(
    "/chat/sessions/{session_id}",
    response_model=AIChatSessionDetail,
    summary="Get AI Chat Session",
    description="Fetch a chat session with all turns in ascending chronological order.",
)
def get_ai_chat_session(
    session_id: str,
    store: Store = Depends(get_store),
) -> AIChatSessionDetail:
    session = store.get_ai_chat_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ai chat session not found")
    turns = store.list_ai_chat_turns(session_id)
    return AIChatSessionDetail(session=session, turns=turns)


@router.post(
    "/chat/sessions/{session_id}/turns",
    response_model=AIChatTurnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI Chat Turn",
    description="Create a new conversation turn with guard-railed parameter proposals.",
)
def create_ai_chat_turn(
    session_id: str,
    payload: AIChatTurnCreateRequest = Body(..., description="AI chat turn payload."),
    generator: AIStyleGenerator = Depends(get_ai_generator),
    store: Store = Depends(get_store),
) -> AIChatTurnResponse:
    session = store.get_ai_chat_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ai chat session not found")

    goals = _detect_conversation_goals(payload.message)
    suggestions, ai_warnings, provider, model = _derive_change_intents_from_ai(
        payload.message,
        session.style_spec,
        goals,
        generator,
    )
    proposed_changes, warnings = _guardrail_changes(session.style_spec, suggestions)
    warnings = [*ai_warnings, *warnings]
    guidance = _guidance_for_turn(goals, warnings, proposed_changes)
    assistant_message = (
        f"I analyzed your request with {provider}/{model} and prepared guard-railed parameter updates. "
        "Review or apply the proposed changes."
    )
    turn = AIChatTurn(
        session_id=session.session_id,
        user_message=payload.message,
        assistant_message=assistant_message,
        proposed_changes=proposed_changes,
        warnings=warnings,
        guidance=guidance,
        applied=False,
    )

    if payload.auto_apply:
        session.style_spec = _apply_parameter_changes(session.style_spec, proposed_changes)
        session.updated_at = datetime.now(timezone.utc)
        turn.applied = True
        store.update_ai_chat_session(session)

    store.create_ai_chat_turn(turn)
    return AIChatTurnResponse(session=session, turn=turn)


@router.post(
    "/chat/sessions/{session_id}/turns/{turn_id}/apply",
    response_model=AIChatTurnResponse,
    summary="Apply AI Chat Turn",
    description="Apply a previously proposed turn to the session style spec (idempotent).",
)
def apply_ai_chat_turn(
    session_id: str,
    turn_id: str,
    store: Store = Depends(get_store),
) -> AIChatTurnResponse:
    session = store.get_ai_chat_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ai chat session not found")
    turn = store.get_ai_chat_turn(session_id, turn_id)
    if turn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ai chat turn not found")

    if not turn.applied:
        session.style_spec = _apply_parameter_changes(session.style_spec, turn.proposed_changes)
        session.updated_at = datetime.now(timezone.utc)
        turn.applied = True
        store.update_ai_chat_session(session)
        store.update_ai_chat_turn(turn)

    return AIChatTurnResponse(session=session, turn=turn)
