# O2C Email Agent Monorepo

## Structure

- `backend/`: FastAPI backend (LangChain + LangGraph workflow, Postgres persistence)
- `frontend/`: Static dashboard (HTML/CSS/JS modules)
- `simulator/`: Source-system simulator (writes source emails, calls backend endpoint)
- `database/`: Postgres schema + seed initialization (invoices, tables)

## Run With Docker

Start full stack from clean state:

```bash
cp backend/.env.example backend/.env
docker compose down -v --remove-orphans
docker compose up --build -d
```

Run simulator:

```bash
docker compose run --rm simulator
```

Ordered mode (stable demo):

```bash
docker compose run --rm simulator python -m app.main --mode ordered \
  --tenant-id tenant_id \
  --date 2026-01-20 \
  --backend-url http://backend:8000 \
  --postgres-dsn postgresql://o2c:o2c@postgres:5432/o2c
```

Fast crash mode (load/failure demo):

```bash
docker compose run --rm simulator python -m app.main --mode fast_crash \
  --tenant-id tenant_id \
  --date 2026-01-20 \
  --backend-url http://backend:8000 \
  --postgres-dsn postgresql://o2c:o2c@postgres:5432/o2c
```

## Data Flow

1. Simulator reads emails in `receivedAt` order from `simulator/data/emails/tenants/<tenant_id>/<date>.json`.
2. Simulator writes each email to Postgres `source_emails` (source system simulation).
3. Simulator calls backend sync endpoint with `source_email_id`.
4. Backend runs LangGraph workflow per email:
   - classify + extract
   - invoice match
   - case draft + structured-case tool
   - next-best-action
   - recommended reply draft
5. Backend stores classification/case/reply data in Postgres.
6. Frontend reads `dashboard` and `emails` APIs.

Frontend URL:
- `http://localhost:5173`

Backend URL:
- `http://localhost:8000/docs`

## LLM Provider

Primary LLM is selected by environment and can be swapped:
- `LLM_PROVIDER=ollama|groq|openai|anthropic|google`
- `LLM_MODEL=...`
- fallback stays Ollama with:
  - `LLM_FALLBACK_PROVIDER=ollama`
  - `LLM_FALLBACK_MODEL=...`

Example (`backend/.env`) for Groq primary + Ollama fallback:

```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_key

LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3.1:latest
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## Tests

```bash
cd backend
uv sync --extra dev
uv run pytest -q
```
