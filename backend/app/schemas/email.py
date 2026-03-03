from typing import Literal

from pydantic import BaseModel, ConfigDict


Category = Literal["payment_claim", "dispute", "general_ar_request"]
CaseStatus = Literal["new", "under_review", "reviewed", "needs_further_review"]


class ClassifiedEmail(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    source_email_id: str
    id: str
    tenant_id: str
    received_at: str
    from_email: str
    subject: str
    body: str
    category: Category
    confidence: float
    reason: str
    classification_source: str
    customer_name: str | None = None
    invoice_references: list[str] | None = None
    amounts: list[float] | None = None
    mentioned_dates: list[str] | None = None
    extraction_source: str
    invoice_match_summary: str | None = None
    invoice_matches: list[dict] | None = None
    case_id: str
    case_title: str | None = None
    case_summary: str | None = None
    case_priority: str | None = None
    next_best_action: str
    next_best_action_reason: str | None = None
    reply_draft_subject: str | None = None
    reply_draft_body: str | None = None
    case_status: str
    detail: str | None = None


class EmailIngestResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    status: str
    tenant_id: str
    email: ClassifiedEmail


class GmailDraftResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    status: str
    tenant_id: str
    draft_id: str
    email: ClassifiedEmail


class ProcessSourceEmailRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    source_email_id: str


class SendReplyRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    reply_subject: str
    reply_body: str


class UpdateCaseStatusRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    status: CaseStatus


class DashboardCard(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: Category
    count: int


class TenantDashboardResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    tenant_id: str
    total_emails: int
    cards: list[DashboardCard]


class TenantEmailListResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    tenant_id: str
    total: int
    emails: list[ClassifiedEmail]
