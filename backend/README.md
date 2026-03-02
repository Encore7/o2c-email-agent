# O2C Email Agent Backend

FastAPI backend for synchronous O2C email processing:
- read source email from Postgres by `source_email_id`
- run LangGraph workflow (classification, extraction, invoice match, case creation, next action, reply draft)
- persist case/classification/reply data
- expose dashboard/query APIs used by frontend

## Setup

```bash
cd backend
uv sync --extra dev
```

## Run API

```bash
cd backend
uv run uvicorn app.main:app --reload
```

## Process Endpoint

`POST /api/v1/tenants/{tenant_id}/process-source-email`

Request body shape:
- `source_email_id` (UUID stored in `source_emails`)

## LLM Provider Selection

Set via environment variables:
- `LLM_PROVIDER=ollama|groq|openai|anthropic|google`
- `LLM_MODEL=<provider-model-name>`
- for Ollama: `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- for cloud: one of `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`

## UI Query Endpoints

- `GET /api/v1/tenants/{tenant_id}/dashboard`
- `GET /api/v1/tenants/{tenant_id}/emails`
- `GET /api/v1/tenants/{tenant_id}/emails?category=dispute`
- `POST /api/v1/tenants/{tenant_id}/emails/{source_email_id}/send-reply`

## Workflow Summary

Per inbound email, backend executes:
1. classify + extract
2. invoice match against `invoices` table
3. case draft + structured case tool
4. next best action
5. recommended reply draft

## Tests

```bash
cd backend
uv run pytest -q
```
