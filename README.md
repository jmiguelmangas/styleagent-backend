# StyleAgent Backend

FastAPI backend for StyleAgent.

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

## Test

```bash
pytest -q
```

## Lint

```bash
ruff check .
```
