# AGENTS.md — StyleAgent (MVP: Capture One)

## Goal
Build the MVP of StyleAgent: a system that generates and exports Capture One Styles (.costyle) from a structured StyleSpec and optional presets/diffs, with safe policies applied (e.g., remove LensLightFallOff, WB, etc.). Provide a minimal API and a minimal UI later; for MVP focus on backend + export pipeline.

## Working agreement
- Always work via branches + PRs. Never push to main directly.
- Keep PRs small and reviewable (ideally <300 LOC).
- Every PR must include:
  - clear description
  - tests or a justification for why tests are not applicable
  - updated docs if behavior changes
- Prefer “boring” and maintainable code: typed, explicit error handling, deterministic outputs.

## MVP Scope
### In scope
- FastAPI backend with:
  - StyleSpec schema (Pydantic)
  - endpoints to create styles, versions, compile/export .costyle
  - safe policy application (remove specific keys)
  - storage on local filesystem (later S3)
  - job execution can be synchronous for MVP (async queue later)
- Capture One exporter:
  - read/transform .costyle templates OR generate minimal valid .costyle
  - apply safe policy removing disallowed keys (LensLightFallOff, WhiteBalance*)
  - deterministic formatting and stable outputs
- Basic tests:
  - unit tests for safe policy removal
  - contract test for compile endpoint returning a valid .costyle artifact

### Out of scope (MVP)
- Lightroom
- DaVinci LUT generation
- PRO rendering/automation
- Authentication (use a simple API key placeholder or none)
- Complex UI

## Repo commands (Backend)
- Install: `pip install -r requirements.txt`
- Run: `uvicorn app.main:app --reload`
- Test: `pytest -q`
- Lint: `ruff check .`

## Architecture references
- Read `docs/HLD.md` first, then implement from `docs/LLD.md`.
- Record new key decisions in `docs/ADRs/ADR-XXXX-<slug>.md`.

## Implementation style
- Use `app/` as the main package.
- Keep API routers under `app/api/`.
- Keep core domain (styles, specs, exporter) under `app/core/`.
- Keep storage utils under `app/storage/`.
- Always type public functions.
- Prefer pure functions for transformations (easy to test).

## Output expectations
- The compile/export must produce a .costyle that Capture One can import.
- Safe policy must be applied by default:
  - remove LensLightFallOff
  - remove WhiteBalance, WhiteBalanceTemperature, WhiteBalanceTint
  - (optional) remove absolute Exposure if configured
- All artifacts must be stored with reproducible naming:
  - `{style_slug}/{version}/capture-one/{style_name}.costyle`
