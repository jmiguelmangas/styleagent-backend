# StyleAgent — LLD (MVP: Capture One)

## 1. Repository Structure (Backend)
app/
main.py
api/
routers/
styles.py
artifacts.py
deps.py
core/
models/
style_spec.py
safe_policy.py
services/
style_service.py
compile_service.py
captureone/
costyle_parser.py
costyle_writer.py
safe_policy_apply.py
storage/
fs_store.py
tests/
test_health.py
test_safe_policy.py
test_compile_costyle.py
docs/
HLD.md
LLD.md
ADRs/


## 2. Data Models

### 2.1 Style
- `style_id` (uuid)
- `name` (string, e.g., "Nolan_04_Warm_v1")
- `slug` (string)
- `created_at`

### 2.2 StyleVersion
- `style_id`
- `version` (int or semantic string)
- `style_spec` (json)
- `safe_policy` (json)
- `created_at`

### 2.3 Artifact
- `artifact_id`
- `style_id`
- `version`
- `target` = "captureone"
- `path`
- `sha256`
- `created_at`

## 3. StyleSpec (Pydantic)
MVP spec focuses on Capture One-relevant primitives.

### 3.1 Schema (suggested)
- `name`: str
- `intent`: list[str] (tags: "cinematic", "warm", "moody")
- `captureone`:
  - `keys`: dict[str, str|float|int]  (direct key/value mapping)
  - `notes`: optional str
- `safe`:
  - `remove_lens_light_falloff`: bool (default true)
  - `remove_white_balance`: bool (default true)
  - `remove_exposure`: bool (default false; configurable)

Rationale:
- We keep MVP simple by allowing direct mapping to Capture One keys we already parse (`ColorCorrections`, curves, etc.).
- Later we can introduce abstract “tone_curve/hsl” and compile into these keys.

## 4. SafePolicy Rules (MVP)

### 4.1 Default removals
If enabled:
- remove key: `LensLightFallOff`
If enabled:
- remove keys: `WhiteBalance`, `WhiteBalanceTemperature`, `WhiteBalanceTint`

Optional:
- remove `Exposure` if configured

### 4.2 Application points
Safe policy is applied:
- just before writing `.costyle` output
- never mutates stored original StyleSpec; it mutates the generated artifact representation

## 5. Capture One `.costyle` handling

### 5.1 Supported strategy (MVP)
Two strategies; implement at least one.

#### Strategy A — Patch a baseline `.costyle` template (recommended)
- Input: `base_template.costyle` (known-valid)
- Parse entries: `<E K="..." V="..."/>`
- Overwrite keys present in StyleSpec
- Remove keys per SafePolicy
- Write new `.costyle`

Pros: highest chance Capture One accepts it.
Cons: needs a baseline template in repo or uploaded by user.

#### Strategy B — Generate minimal `.costyle` from scratch
- Generate `<SL Engine="...">` + `<E .../>` entries
- Must match expected root format and engine version

Pros: simpler distribution.
Cons: risk of invalid format for some Capture One versions.

MVP recommendation: implement **Strategy A** first.

### 5.2 Parser/Writer
- `costyle_parser.py`: parse XML-ish content safely:
  - handle long lines
  - tolerate unknown tags
  - return an ordered list of entries: `{key, value, raw_line?}`
- `costyle_writer.py`: produce deterministic output:
  - stable ordering (e.g., preserve template order, then append new keys)
  - newline normalization

## 6. API Design (FastAPI)

### 6.1 Endpoints

#### Health
- `GET /health`
  - 200 `{ "status": "ok" }`

#### Styles
- `POST /styles`
  - body: `{ "name": "Nolan_04_Warm", "slug": "nolan-04-warm" }`
  - returns: `{ "style_id": "...", ... }`

- `POST /styles/{style_id}/versions`
  - body: `StyleSpec`
  - returns: `{ "version": 1, "created_at": ... }`

- `GET /styles/{style_id}/versions/{version}`
  - returns: stored spec + policy

#### Compile / Export
- `POST /styles/{style_id}/versions/{version}/compile`
  - query: `target=captureone`
  - body optional:
    - `template_costyle` reference (path/id) OR use default baseline
  - returns:
    - `{ "artifact_id": "...", "download_url": "...", "sha256": "..." }`

#### Download artifact
- `GET /artifacts/{artifact_id}`
  - returns file stream (`application/octet-stream`)

### 6.2 Error handling
- 404 if style/version not found
- 400 for invalid StyleSpec
- 422 for schema validation errors
- 500 with structured error id for exporter failures

## 7. Storage (MVP: filesystem)

### 7.1 Directory layout
`data/`
- `styles/{style_slug}/versions/{version}/spec.json`
- `styles/{style_slug}/versions/{version}/policy.json`
- `styles/{style_slug}/versions/{version}/artifacts/captureone/{name}.costyle`
- `index/artifacts.json` (simple registry for MVP)

### 7.2 Checksums
Compute SHA-256 for exported artifact and store in metadata.

## 8. Testing Plan

### 8.1 Unit tests
- `test_safe_policy.py`:
  - given a parsed entries dict, removes correct keys
  - does not remove unrelated keys

### 8.2 Contract tests
- `test_compile_costyle.py`:
  - compile endpoint produces a `.costyle` with:
    - removed keys (LensLightFallOff, WhiteBalance*)
    - preserved keys from template
    - deterministic output (same input => same sha)

### 8.3 Smoke
- `test_health.py` already present

## 9. Incremental Implementation Plan (PR-sized)

### Phase 0 — baseline green
- ensure CI passes (ruff + pytest)
- minimal app/main.py + tests

### Phase 1 — StyleSpec + persistence
- implement models + local store
- endpoints: create style, create version, get version

### Phase 2 — Capture One compile (template patch)
- add baseline template (in repo or allow upload later)
- implement parser/writer
- implement compile endpoint returning artifact

### Phase 3 — SafePolicy enforced by default
- defaults applied even if user doesn’t specify
- tests for removals

### Phase 4 — Artifacts listing & download
- list artifacts per style/version
- stream download endpoint

## 10. Acceptance Criteria (MVP)
- Can create a style and a version with StyleSpec JSON
- Can compile/export a `.costyle` artifact
- Export applies safe policy by default removing:
  - LensLightFallOff
  - WhiteBalance, WhiteBalanceTemperature, WhiteBalanceTint
- Artifact is downloadable and stored on disk
- CI green