# StyleAgent Backend

FastAPI backend for StyleAgent MVP (Capture One first).

Current implementation includes:
- health endpoint
- styles + versions API
- domain models and validation
- filesystem storage layer
- Capture One `.costyle` parser/writer core

## Requirements

- Python 3.12+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Lint

```bash
ruff check .
```

## Tests

```bash
pytest -q
```

## API Endpoints (Current)

- `GET /health`
  - Returns `{ "status": "ok" }`

- `POST /styles`
  - Creates a style from `StyleCreate`

- `GET /styles/{style_id}`
  - Returns stored style or `404`

- `POST /styles/{style_id}/versions`
  - Creates a style version from `StyleVersionCreate`

- `GET /styles/{style_id}/versions/{version}`
  - Returns stored version or `404`

## Storage Layout (Filesystem)

Current storage root is `data/`.

- `data/styles/{style_slug}/style.json`
- `data/styles/{style_slug}/versions/{version}/version.json`
- `data/styles/{style_slug}/versions/{version}/spec.json`
- `data/styles/{style_slug}/versions/{version}/policy.json`
- `data/styles/{style_slug}/versions/{version}/artifacts/{target}/{filename}`
- `data/index/styles.json`
- `data/index/artifacts.json`

## Project Structure (Current)

```text
app/
  main.py
  api/
    deps.py
    routers/
      styles.py
  core/
    models/
      style_models.py
      style_spec.py
    utils/
      ids.py
      text.py
    captureone/
      costyle_parser.py
      costyle_writer.py
      templates/
        base.costyle
  storage/
    fs_store.py

tests/
  test_health.py
  test_utils.py
  test_models.py
  test_fs_store.py
  test_styles_api.py
  test_costyle_parser_writer.py
  fixtures/
    sample.costyle
```

## Test Coverage (Current)

- `tests/test_health.py`
  - health endpoint contract

- `tests/test_utils.py`
  - `slugify()` behavior and ID generation

- `tests/test_models.py`
  - Pydantic model validation edge cases

- `tests/test_fs_store.py`
  - filesystem storage roundtrips (`tmp_path`)

- `tests/test_styles_api.py`
  - API contracts for styles/versions (`201/200/404`)

- `tests/test_costyle_parser_writer.py`
  - `.costyle` parser/writer parsing and deterministic roundtrip

## CI

GitHub Actions workflow is defined in `.github/workflows/ci.yml` and runs:
- lint (`ruff check .`)
- tests (`pytest -q`)

## Notes

- This backend is currently focused on Phases 0-4 from `docs/Implementation-Plan.md`.
- Next phases add safe-policy application and compile/export endpoints.
