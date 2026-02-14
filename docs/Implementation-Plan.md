# StyleAgent Backend — Implementation Plan (MVP: Capture One)

This plan breaks the MVP into small, reviewable PR-sized phases.  
Target: Generate and export Capture One `.costyle` artifacts from a stored StyleSpec, applying safe policies by default.

---

## Conventions

### Branch naming
- `feature/<slug>` for features
- `fix/<slug>` for bugfixes
- `chore/<slug>` for infra/docs/refactor

### PR requirements
Each PR must include:
- Summary (what/why)
- How to test (commands)
- Tests added/updated (or explicit reason why none)
- Updated docs if behavior changes

### Commands (baseline)
- Run: `uvicorn app.main:app --reload`
- Test: `pytest -q`
- Lint: `ruff check .`

---

## Phase 0 — Repo baseline & DX (1 PR)

**Goal:** Ensure a stable baseline project structure that always passes CI.

**Deliverables**
- Ensure folder structure exists:
  - `app/api/`, `app/core/`, `app/storage/`, `tests/`
- Add/confirm:
  - `requirements.txt` includes: `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `ruff`
  - `README.md` includes run/test instructions
- `GET /health` endpoint returns `{ "status": "ok" }`
- CI workflow runs lint + tests successfully

**Acceptance criteria**
- `pytest -q` passes locally
- `ruff check .` passes locally
- GitHub Actions status is green on `main`

---

## Phase 1 — Domain models: Style, Version, Artifact (1 PR)

**Goal:** Establish minimal domain models + types for the MVP.

**Deliverables**
- Pydantic models:
  - `StyleCreate`, `Style`
  - `StyleSpec` (MVP schema)
  - `StyleVersionCreate`, `StyleVersion`
  - `Artifact`
- Utilities:
  - `slugify(name) -> slug`
  - basic ID generation (UUID)

**Acceptance criteria**
- Models validate expected payloads
- Unit tests for `slugify` and model validation edge cases

---

## Phase 2 — Filesystem storage layer (1–2 PRs)

**Goal:** Persist styles, versions, and artifacts on disk with reproducible structure.

**Deliverables**
- `app/storage/fs_store.py`:
  - `create_style(style: Style) -> Style`
  - `get_style(style_id) -> Style | None`
  - `create_version(style_id, version: StyleVersion) -> StyleVersion`
  - `get_version(style_id, version) -> StyleVersion | None`
  - `save_artifact(style_id, version, target, filename, bytes) -> Artifact`
  - `get_artifact(artifact_id) -> (Artifact, bytes) | None`
- Storage layout under `data/`:
  - `data/styles/{slug}/versions/{version}/spec.json`
  - `data/styles/{slug}/versions/{version}/policy.json` (if present)
  - `data/styles/{slug}/versions/{version}/artifacts/captureone/{name}.costyle`
  - `data/index/artifacts.json` (simple registry for MVP)
- SHA-256 checksum for artifact content.

**Acceptance criteria**
- Creating style + version writes files correctly
- Artifact save + load roundtrip works
- Unit tests using `tmp_path` (no real filesystem pollution)

---

## Phase 3 — API: Styles & Versions (1 PR)

**Goal:** Implement CRUD-lite endpoints for styles and versions.

**Endpoints**
- `POST /styles` → create style
- `GET /styles/{style_id}` → get style
- `POST /styles/{style_id}/versions` → create version (stores StyleSpec)
- `GET /styles/{style_id}/versions/{version}` → fetch stored version
- (Optional) `GET /styles/{style_id}/versions` list versions

**Acceptance criteria**
- Endpoints return correct codes (201/200/404)
- Contract tests using FastAPI `TestClient`
- Stored spec returned matches input

---

## Phase 4 — Capture One `.costyle` core: parser + writer (1–2 PRs)

**Goal:** Build the minimal library to read/patch/write `.costyle` deterministically.

**Deliverables**
- `app/core/captureone/costyle_parser.py`
  - Parse `.costyle` XML-ish format into an internal representation:
    - preserve template order
    - capture entries `<E K="..." V="..."/>`
    - tolerate unknown tags and long lines
- `app/core/captureone/costyle_writer.py`
  - Write the internal representation back to `.costyle`
  - deterministic output:
    - stable ordering (template order preserved)
    - newline normalization
- Include a minimal baseline template:
  - Option A: store `app/core/captureone/templates/base.costyle`
  - Option B: allow user-provided template later (not MVP)

**Acceptance criteria**
- Parsing and writing a template roundtrips with minimal/no diff (or a documented normalization diff)
- Unit tests for parser/writer on a sample `.costyle` fixture

---

## Phase 5 — Safe Policy system (1 PR)

**Goal:** Implement safe-by-default key removal prior to export.

**Default rules (MVP)**
- Remove:
  - `LensLightFallOff`
  - `WhiteBalance`
  - `WhiteBalanceTemperature`
  - `WhiteBalanceTint`

**Deliverables**
- `app/core/models/safe_policy.py`:
  - config flags with defaults:
    - `remove_lens_light_falloff=True`
    - `remove_white_balance=True`
    - `remove_exposure=False` (optional)
- `app/core/captureone/safe_policy_apply.py`:
  - `apply_safe_policy(entries, policy) -> entries`
- Tests:
  - ensures removed keys are gone
  - ensures unrelated keys remain
  - ensures idempotency (apply twice = same output)

**Acceptance criteria**
- Unit tests pass
- Safe policy applied by default even if the user doesn’t specify it

---

## Phase 6 — Compile/Export service (1–2 PRs)

**Goal:** Convert stored StyleSpec into a `.costyle` artifact using a template-patch strategy.

**Deliverables**
- `app/core/services/compile_service.py`:
  - Load template `.costyle`
  - Parse → patch keys from `StyleSpec.captureone.keys`
  - Apply safe policy
  - Write output bytes
  - Persist artifact via FS store
- `StyleSpec.captureone.keys` rules:
  - Only overwrite keys present in `keys`
  - Keep others from template intact

**Acceptance criteria**
- Deterministic output:
  - same input spec produces same SHA-256
- Contract test:
  - compile endpoint generates `.costyle`
  - returned metadata includes sha256 + artifact_id
  - artifact stored on disk

---

## Phase 7 — API: Compile + Download (1 PR)

**Goal:** Expose compile/export and artifact download endpoints.

**Endpoints**
- `POST /styles/{style_id}/versions/{version}/compile?target=captureone`
  - returns `{ artifact_id, sha256, download_url }`
- `GET /artifacts/{artifact_id}`
  - streams the `.costyle` file

**Acceptance criteria**
- 404 on missing style/version/artifact
- Response includes correct content type and filename
- Contract tests cover both endpoints

---

## Phase 8 — Hardening (optional, timeboxed)

**Goal:** Small improvements that reduce future pain.

**Deliverables (pick a subset)**
- Better error responses (error_id, message, context)
- Minimal logging with request IDs
- Add `GET /styles` list styles (optional)
- Add `GET /styles/{style_id}/artifacts` list artifacts (optional)
- ADRs for key decisions
- Add `Makefile` or `taskfile` for commands

**Acceptance criteria**
- No regression in existing tests
- CI remains green

---

## Definition of Done (MVP)

MVP is done when:
- A style and version can be created via API
- A `.costyle` can be compiled/exported from a stored StyleSpec
- Safe policy is applied by default removing:
  - LensLightFallOff
  - WhiteBalance / Temperature / Tint
- Artifact is stored and downloadable
- CI is green

---

## Suggested PR sequence

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7
9. Phase 8 (optional)
