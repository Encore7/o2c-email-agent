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
uv run python -m app.main --mode ordered
```

Modes:
- `--mode ordered`: sends one email at a time in `receivedAt` order.
- `--mode fast_crash`: sends aggressively to show overload/failure behavior.

Options:
- `--mode ordered|fast_crash`
- `--limit 100`
- `--backend-url http://127.0.0.1:8000`
- `--tenant-id tenant_id`
- `--date 2026-01-20`
- `--source /absolute/or/relative/path.json`
Source data file:
- `data/emails/tenants/<tenant_id>/<date>.json`
- `data/emails/raw/Sample Emails.json`

Target source DB table:
- `source_emails` in Postgres
