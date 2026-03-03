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

Set via environment variables (no code changes required):
- `LLM_PROVIDER=ollama|groq|openai|anthropic|google`
- `LLM_MODEL=<provider-model-name>`
- for Ollama: `OLLAMA_BASE_URL=http://host.docker.internal:11434`
- for cloud: one of `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`

Recommended setup:
- keep fallback on local Ollama always
- switch only primary provider while testing

Required fallback settings:
- `LLM_FALLBACK_PROVIDER=ollama`
- `LLM_FALLBACK_MODEL=<local-ollama-model>`

Examples:

Groq primary:
```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=...
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3.1:latest
```

OpenAI primary:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini
OPENAI_API_KEY=...
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3.1:latest
```

Anthropic primary:
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-latest
ANTHROPIC_API_KEY=...
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3.1:latest
```

Gemini primary:
```env
LLM_PROVIDER=google
LLM_MODEL=gemini-1.5-pro
GOOGLE_API_KEY=...
LLM_FALLBACK_PROVIDER=ollama
LLM_FALLBACK_MODEL=llama3.1:latest
```

## UI Query Endpoints

- `GET /api/v1/tenants/{tenant_id}/dashboard`
- `GET /api/v1/tenants/{tenant_id}/emails`
- `GET /api/v1/tenants/{tenant_id}/emails?category=dispute`
- `POST /api/v1/tenants/{tenant_id}/emails/{source_email_id}/send-reply`
- `POST /api/v1/tenants/{tenant_id}/emails/{source_email_id}/gmail-draft`

## Gmail Draft Integration

Direct Gmail API draft creation using OAuth refresh token:
- `GMAIL_ENABLED=true`
- `GMAIL_CLIENT_ID=...`
- `GMAIL_CLIENT_SECRET=...`
- `GMAIL_REFRESH_TOKEN=...`
- `GMAIL_USER_ID=me` (default)

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
