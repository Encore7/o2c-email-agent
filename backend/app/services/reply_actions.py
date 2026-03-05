from app.schemas.email import ClassifiedEmail
from app.repositories.classified_email_repository import ClassifiedEmailRepository
from app.repositories.outbound_email_repository import OutboundEmailRepository
from app.repositories.source_email_repository import SourceEmailRepository
from app.services.gmail import GmailClient, GmailIntegrationError


class ReplyActionsService:
    def __init__(
        self,
        source_repository: SourceEmailRepository,
        classified_repository: ClassifiedEmailRepository,
        outbound_repository: OutboundEmailRepository,
        gmail_client: GmailClient | None = None,
    ) -> None:
        self._source_repository = source_repository
        self._classified_repository = classified_repository
        self._outbound_repository = outbound_repository
        self._gmail_client = gmail_client

    def send_reply(
        self,
        tenant_id: str,
        source_email_id: str,
        reply_subject: str,
        reply_body: str,
    ) -> tuple[str, ClassifiedEmail]:
        updated = self._classified_repository.update_reply_draft(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
            reply_subject=reply_subject,
            reply_body=reply_body,
        )
        source_email = self._source_repository.get_source_email(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
        )
        if source_email is None:
            raise ValueError(f"source_email_id {source_email_id} not found")
        self._outbound_repository.log_outbound_email(
            source_email=source_email,
            subject=reply_subject,
            body=reply_body,
            status="sent_simulated",
        )
        return "email_sent", updated

    def create_gmail_draft(
        self,
        tenant_id: str,
        source_email_id: str,
        reply_subject: str,
        reply_body: str,
    ) -> tuple[str, ClassifiedEmail, str]:
        if self._gmail_client is None:
            raise GmailIntegrationError("Gmail integration is not configured.")
        updated = self._classified_repository.update_reply_draft(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
            reply_subject=reply_subject,
            reply_body=reply_body,
        )
        draft_id = self._gmail_client.create_draft(
            to_email=updated.from_email,
            subject=reply_subject,
            body=reply_body,
        )
        source_email = self._source_repository.get_source_email(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
        )
        if source_email is None:
            raise ValueError(f"source_email_id {source_email_id} not found")
        self._outbound_repository.log_outbound_email(
            source_email=source_email,
            subject=reply_subject,
            body=reply_body,
            status=f"draft_created:{draft_id}",
        )
        return "gmail_draft_created", updated, draft_id
