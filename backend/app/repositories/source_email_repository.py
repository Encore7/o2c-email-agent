import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import InvoiceRecord, SourceEmail


class SourceEmailRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_source_email(self, tenant_id: str, source_email_id: str) -> SourceEmail | None:
        source_uuid = uuid.UUID(source_email_id)
        stmt = select(SourceEmail).where(
            SourceEmail.tenant_id == tenant_id,
            SourceEmail.source_email_id == source_uuid,
        )
        return self._session.scalar(stmt)

    def list_invoice_catalog(self, tenant_id: str) -> list[dict]:
        stmt = select(InvoiceRecord).where(InvoiceRecord.tenant_id == tenant_id)
        rows = self._session.scalars(stmt).all()
        return [
            {
                "invoice_id": row.invoice_id,
                "amount": float(row.amount),
                "currency": row.currency,
                "status": row.status,
            }
            for row in rows
        ]
