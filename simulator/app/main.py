from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import psycopg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate inbound emails sent to backend API."
    )
    parser.add_argument("--tenant-id", default="tenant_id")
    parser.add_argument("--date", default="2026-01-20")
    parser.add_argument("--source", default=None)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--postgres-dsn", default="postgresql://o2c:o2c@localhost:5432/o2c"
    )
    parser.add_argument("--mode", choices=["ordered", "fast_crash"], default="ordered")
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def load_source(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    emails = payload.get("emails", [])
    if not isinstance(emails, list):
        raise ValueError("Source JSON must include an 'emails' list.")
    return emails


def resolve_mode_preset(mode: str) -> tuple[float, float | None]:
    """
    ordered: realistic one-by-one processing in received order.
    fast_crash: intentionally aggressive mode to demonstrate API overload/failures.
    """
    if mode == "fast_crash":
        return 0.0, 3.0
    return 2.0, None


def resolve_source_path(tenant_id: str, batch_date: str, source: str | None) -> Path:
    if source:
        return Path(source)
    return (
        Path(__file__).resolve().parents[1]
        / "data"
        / "emails"
        / "tenants"
        / tenant_id
        / f"{batch_date}.json"
    )


def order_by_received_at(emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(emails, key=lambda item: item.get("receivedAt", ""))


def write_source_email_to_db(
    postgres_dsn: str, tenant_id: str, email: dict[str, Any]
) -> str:
    source_email_id = str(uuid.uuid4())
    query = """
    INSERT INTO source_emails (
      source_email_id, tenant_id, email_id, received_at, from_email, subject, body
    ) VALUES (%s::uuid, %s, %s, %s::timestamptz, %s, %s, %s)
    ON CONFLICT (tenant_id, email_id) DO UPDATE
    SET
      received_at = EXCLUDED.received_at,
      from_email = EXCLUDED.from_email,
      subject = EXCLUDED.subject,
      body = EXCLUDED.body
    RETURNING source_email_id::text
    """
    with psycopg.connect(postgres_dsn) as conn, conn.cursor() as cur:
        cur.execute(
            query,
            (
                source_email_id,
                tenant_id,
                email["id"],
                email["receivedAt"],
                email["from"],
                email["subject"],
                email["body"],
            ),
        )
        db_source_id = cur.fetchone()[0]
        conn.commit()
    return db_source_id


def main() -> None:
    args = parse_args()
    source = resolve_source_path(
        tenant_id=args.tenant_id, batch_date=args.date, source=args.source
    )
    emails = order_by_received_at(load_source(source))[: args.limit]
    interval, timeout_value = resolve_mode_preset(args.mode)
    endpoint = (
        f"{args.backend_url}/api/v1/tenants/{args.tenant_id}/process-source-email"
    )

    print(
        f"Mode={args.mode}. Streaming {len(emails)} emails from {source} with interval {interval}s "
        f"and request timeout {'none' if timeout_value is None else f'{timeout_value}s'}"
    )
    with httpx.Client(timeout=timeout_value) as client:
        for index, email in enumerate(emails, start=1):
            source_email_id = write_source_email_to_db(
                postgres_dsn=args.postgres_dsn,
                tenant_id=args.tenant_id,
                email=email,
            )
            try:
                response = client.post(
                    endpoint, json={"source_email_id": source_email_id}
                )
            except httpx.ReadTimeout:
                print(
                    f"[{index}] timeout after {timeout_value}s for source_email_id={source_email_id}"
                )
                raise
            if response.status_code >= 400:
                print(f"[{index}] failed: {response.status_code} {response.text}")
            else:
                payload = response.json()
                print(
                    f"[{index}] status={payload['status']} email_id={payload['email']['id']} "
                    f"category={payload['email']['category']} case={payload['email']['case_id']}"
                )
            if index < len(emails):
                time.sleep(interval)


if __name__ == "__main__":
    main()
