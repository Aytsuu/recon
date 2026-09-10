# AI Engine

FastAPI service for the recon platform.

## Setup

```bash
cd ai_engine
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

Copy environment variables as needed:

```bash
# from repo root
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

## Project layout

```text
ai_engine/
├── app/
│   ├── api/          # Route modules
│   ├── core/         # Config and shared utilities
│   └── main.py       # FastAPI application entrypoint
├── tests/
└── pyproject.toml
```
