# recon

Universal customer-support access layer.

## Monorepo layout

```text
ai_engine/     FastAPI AI orchestration service
apps/web/      Astro frontend
supabase/      Supabase CLI (migrations, local dev)
```

### Quick start

**AI Engine (FastAPI)**

```bash
cd ai_engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Web (Astro)**

```bash
cd apps/web
npm install
npm run dev
```

**Supabase**

```bash
supabase start
```
