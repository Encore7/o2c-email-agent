from sqlalchemy.orm import Session

from app.db.models import OutboundEmailRecord, SourceEmail


class OutboundEmailRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def log_outbound_email(
        self,
        source_email: SourceEmail,
        subject: str,
        body: str,
        status: str,
    ) -> None:
        outbound = OutboundEmailRecord(
            source_email_id=source_email.source_email_id,
            tenant_id=source_email.tenant_id,
            email_id=source_email.email_id,
            subject=subject,
            body=body,
            status=status,
        )
        self._session.add(outbound)
        self._session.commit()
