# O2C Email Simulator

Service that simulates source-system behavior:
1. email is stored in source DB first
2. then backend is called to process that DB row synchronously

## Setup

```bash
cd simulator
uv sync
```

## Run

```bash
cd simulator
uv run python -m app.main --mode fast
```

Options:
- `--mode fast|slow`
- `--interval-seconds 0.2`
- `--limit 20`
- `--backend-url http://127.0.0.1:8000`
- `--tenant-id tenant_id`
- `--date 2026-01-20`
- `--request-timeout-seconds 0` (0 means no timeout)
- `--source /absolute/or/relative/path.json` (optional override)

Source data file:
- `data/emails/tenants/<tenant_id>/<date>.json`
- `data/emails/raw/Sample Emails.json` (raw copy kept in repo)

Target source DB table:
- `source_emails` in Postgres
