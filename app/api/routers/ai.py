from fastapi import APIRouter, Body, Depends

from app.api.deps import get_ai_generator
from app.core.ai.base import AIStyleGenerator
from app.core.models.ai import GeneratedStyleSpecResponse, PromptGenerateRequest

router = APIRouter(prefix="/ai", tags=["ai"])


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
    payload: PromptGenerateRequest = Body(..., description="Prompt-based generation payload."),
    generator: AIStyleGenerator = Depends(get_ai_generator),
) -> GeneratedStyleSpecResponse:
    return generator.generate_style_spec(payload)
