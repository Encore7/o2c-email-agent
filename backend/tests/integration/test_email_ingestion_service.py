from types import SimpleNamespace

from app.schemas.email import ClassifiedEmail, ProcessSourceEmailRequest
from app.services.email_processing import EmailProcessingService
from app.services.reply_actions import ReplyActionsService


def _classified_email(source_email_id: str) -> ClassifiedEmail:
    return ClassifiedEmail(
        source_email_id=source_email_id,
        id="email_001",
        tenant_id="tenant_id",
        received_at="2026-01-20T08:00:00Z",
        from_email="ap@freshmart.com",
        subject="Payment sent INV-10000",
        body="Body",
        category="payment_claim",
        confidence=0.9,
        reason="Payment stated.",
        classification_source="llm_primary",
        customer_name="FreshMart",
        invoice_references=["INV-10000"],
        amounts=[1375.0],
        mentioned_dates=["2026-01-20"],
        extraction_source="hybrid_llm_regex",
        invoice_match_summary="1 match",
        invoice_matches=[{"invoice_id": "INV-10000", "match_confidence": 1.0}],
        case_id="case_tenant_id_email_001",
        case_title="Payment claim",
        case_summary="Customer says paid.",
        case_priority="medium",
        next_best_action="Match payment.",
        next_best_action_reason="Need verify in ledger.",
        reply_draft_subject="Next Steps on Your AR Request",
        reply_draft_body="Hi\n\nOur AR team will now: Match payment.\n\nRegards,\nAR Team",
        case_status="open",
        detail="Paid today",
    )


class MockSourceRepository:
    def get_source_email(self, tenant_id: str, source_email_id: str):
        del tenant_id, source_email_id
        return SimpleNamespace(
            source_email_id="11111111-1111-1111-1111-111111111111",
            tenant_id="tenant_id",
            email_id="email_001",
            received_at="2026-01-20T08:00:00Z",
            from_email="ap@freshmart.com",
            subject="Payment sent INV-10000",
            body="Please apply payment. Regards, FreshMart",
        )

    def list_invoice_catalog(self, tenant_id: str):
        del tenant_id
        return [{"invoice_id": "INV-10000", "amount": 1375.0, "status": "open"}]


class MockClassifiedRepository:
    def __init__(self) -> None:
        self.existing = None
        self.outbound_logged = False
        self.saved = _classified_email("11111111-1111-1111-1111-111111111111")

    def get_classified_by_source(self, tenant_id: str, source_email_id: str):
        del tenant_id, source_email_id
        return self.existing

    def save_case_and_classification(self, **kwargs):
        del kwargs
        return self.saved

    def update_reply_draft(self, tenant_id: str, source_email_id: str, reply_subject: str, reply_body: str):
        del tenant_id, source_email_id
        self.saved.reply_draft_subject = reply_subject
        self.saved.reply_draft_body = reply_body
        return self.saved

class MockOutboundRepository:
    def __init__(self) -> None:
        self.logged = False

    def log_outbound_email(self, source_email, subject: str, body: str, status: str):
        del source_email, subject, body, status
        self.logged = True


class MockAnalyzer:
    def analyze(self, subject: str, body: str, invoice_catalog: list[dict]):
        del subject, body, invoice_catalog
        return SimpleNamespace(
            category="payment_claim",
            confidence=0.9,
            reason="Payment stated.",
            classification_source="llm_primary",
            customer_name="FreshMart",
            invoice_references=["INV-10000"],
            amounts=[1375.0],
            mentioned_dates=["2026-01-20"],
            detail="Paid today",
            extraction_source="hybrid_llm_regex",
            case_title="Payment claim",
            case_summary="Customer says paid.",
            case_priority="medium",
            invoice_match_summary="1 match",
            invoice_matches=[{"invoice_id": "INV-10000", "match_confidence": 1.0}],
            next_best_action="Match payment.",
            next_best_action_reason="Need verify in ledger.",
            reply_draft_subject="Next Steps on Your AR Request",
            reply_draft_body="Hi\n\nOur AR team will now: Match payment.\n\nRegards,\nAR Team",
        )


def test_process_source_email_integration():
    source_repository = MockSourceRepository()
    classified_repository = MockClassifiedRepository()
    service = EmailProcessingService(
        source_repository=source_repository,
        classified_repository=classified_repository,
        analyzer=MockAnalyzer(),
    )
    status, email = service.process_source_email(
        tenant_id="tenant_id",
        request=ProcessSourceEmailRequest(source_email_id="11111111-1111-1111-1111-111111111111"),
    )
    assert status == "processed"
    assert email.category == "payment_claim"


def test_send_reply_integration_logs_outbound():
    source_repository = MockSourceRepository()
    classified_repository = MockClassifiedRepository()
    outbound_repository = MockOutboundRepository()
    service = ReplyActionsService(
        source_repository=source_repository,
        classified_repository=classified_repository,
        outbound_repository=outbound_repository,
    )
    status, email = service.send_reply(
        tenant_id="tenant_id",
        source_email_id="11111111-1111-1111-1111-111111111111",
        reply_subject="Custom Subject",
        reply_body="Custom body",
    )
    assert status == "email_sent"
    assert email.reply_draft_subject == "Custom Subject"
    assert outbound_repository.logged is True
