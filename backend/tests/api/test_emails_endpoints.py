from fastapi.testclient import TestClient

from app.api.deps import (
    get_email_repository,
    get_processing_service,
    get_reply_actions_service,
)
from app.main import app
from app.schemas.email import ClassifiedEmail


def _classified_email() -> ClassifiedEmail:
    return ClassifiedEmail(
        source_email_id="11111111-1111-1111-1111-111111111111",
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


class FakeIngestionService:
    def process_source_email(self, tenant_id: str, request):
        del tenant_id, request
        return "processed", _classified_email()

    def send_reply(self, tenant_id: str, source_email_id: str, reply_subject: str, reply_body: str):
        del tenant_id, source_email_id, reply_subject, reply_body
        return "email_sent", _classified_email()

    def create_gmail_draft(self, tenant_id: str, source_email_id: str, reply_subject: str, reply_body: str):
        del tenant_id, source_email_id, reply_subject, reply_body
        return "gmail_draft_created", _classified_email(), "r-draft-123"


class FakeRepo:
    def category_counts(self, tenant_id: str, on_date=None):
        del tenant_id, on_date
        return {"payment_claim": 2, "dispute": 1, "general_ar_request": 1}

    def list_emails(self, tenant_id: str, category=None, on_date=None, order="desc"):
        del tenant_id, category, on_date, order
        return [_classified_email()]

    def update_case_status(self, tenant_id: str, source_email_id: str, status: str):
        del tenant_id, source_email_id
        updated = _classified_email()
        updated.case_status = status
        return updated


def test_process_source_email_api():
    app.dependency_overrides[get_processing_service] = lambda: FakeIngestionService()
    client = TestClient(app)
    res = client.post(
        "/api/v1/tenants/tenant_id/process-source-email",
        json={"source_email_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "processed"
    assert payload["email"]["category"] == "payment_claim"
    app.dependency_overrides.clear()


def test_send_reply_api():
    app.dependency_overrides[get_reply_actions_service] = lambda: FakeIngestionService()
    client = TestClient(app)
    res = client.post(
        "/api/v1/tenants/tenant_id/emails/11111111-1111-1111-1111-111111111111/send-reply",
        json={"reply_subject": "S", "reply_body": "B"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "email_sent"
    app.dependency_overrides.clear()


def test_gmail_draft_api():
    app.dependency_overrides[get_reply_actions_service] = lambda: FakeIngestionService()
    client = TestClient(app)
    res = client.post(
        "/api/v1/tenants/tenant_id/emails/11111111-1111-1111-1111-111111111111/gmail-draft",
        json={"reply_subject": "S", "reply_body": "B"},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "gmail_draft_created"
    assert payload["draft_id"] == "r-draft-123"
    app.dependency_overrides.clear()


def test_dashboard_and_list_api():
    app.dependency_overrides[get_email_repository] = lambda: FakeRepo()
    client = TestClient(app)
    dash = client.get("/api/v1/tenants/tenant_id/dashboard")
    emails = client.get("/api/v1/tenants/tenant_id/emails")
    assert dash.status_code == 200
    assert dash.json()["total_emails"] == 4
    assert emails.status_code == 200
    assert emails.json()["total"] == 1
    app.dependency_overrides.clear()


def test_update_case_status_api():
    app.dependency_overrides[get_email_repository] = lambda: FakeRepo()
    client = TestClient(app)
    res = client.patch(
        "/api/v1/tenants/tenant_id/emails/11111111-1111-1111-1111-111111111111/status",
        json={"status": "reviewed"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "status_updated"
    assert res.json()["email"]["case_status"] == "reviewed"
    app.dependency_overrides.clear()
