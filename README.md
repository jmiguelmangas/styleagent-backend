# StyleAgent Backend

FastAPI backend for StyleAgent MVP (Capture One first).

Current implementation includes:
- styles + versions API
- compile/export flow for Capture One `.costyle`
- artifact download endpoint
- safe policy system
- filesystem persistence
- request-id middleware and structured error responses

## Requirements

- Python 3.12+

## Setup (Local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run (Local)

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

## Run With Docker

Build image from `backend/`:

```bash
docker build -t styleagent-backend:dev .
```

Run container:

```bash
docker run --rm -p 8000:8000 styleagent-backend:dev
```

Service URL:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## API Endpoints (Current)

- `GET /health`
- `GET /styles`
- `POST /styles`
- `GET /styles/{style_id}`
- `POST /styles/{style_id}/versions`
- `GET /styles/{style_id}/versions/{version}`
- `POST /styles/{style_id}/versions/{version}/compile?target=captureone`
- `GET /styles/{style_id}/artifacts`
- `GET /artifacts/{artifact_id}`

## Storage Layout (Filesystem)

Storage root is `data/`.

- `data/styles/{style_slug}/style.json`
- `data/styles/{style_slug}/versions/{version}/version.json`
- `data/styles/{style_slug}/versions/{version}/spec.json`
- `data/styles/{style_slug}/versions/{version}/policy.json`
- `data/styles/{style_slug}/versions/{version}/artifacts/{target}/{filename}`
- `data/index/styles.json`
- `data/index/artifacts.json`

## CI

GitHub Actions workflow is in `.github/workflows/ci.yml` and runs:
- `ruff check .`
- `pytest -q`
