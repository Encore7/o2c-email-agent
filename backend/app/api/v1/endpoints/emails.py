from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import (
    get_email_repository,
    get_processing_service,
    get_reply_actions_service,
)
from app.schemas.email import (
    Category,
    DashboardCard,
    EmailIngestResponse,
    GmailDraftResponse,
    ProcessSourceEmailRequest,
    SendReplyRequest,
    TenantDashboardResponse,
    TenantEmailListResponse,
    UpdateCaseStatusRequest,
)
from app.services.analysis import LLMUnavailableError
from app.services.email_processing import EmailProcessingService
from app.services.gmail import GmailIntegrationError
from app.services.reply_actions import ReplyActionsService
from app.repositories.classified_email_repository import ClassifiedEmailRepository

router = APIRouter()


@router.post("/process-source-email", response_model=EmailIngestResponse, status_code=200)
def process_source_email(
    tenant_id: str,
    request: ProcessSourceEmailRequest,
    processing_service: EmailProcessingService = Depends(get_processing_service),
) -> EmailIngestResponse:
    try:
        status, classified = processing_service.process_source_email(tenant_id=tenant_id, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LLMUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Model unavailable. Try again later. {exc}",
        ) from exc
    return EmailIngestResponse(
        status=status,
        tenant_id=tenant_id,
        email=classified,
    )


@router.post("/emails/{source_email_id}/send-reply", response_model=EmailIngestResponse, status_code=200)
def send_reply_for_email(
    tenant_id: str,
    source_email_id: str,
    request: SendReplyRequest,
    reply_actions_service: ReplyActionsService = Depends(get_reply_actions_service),
) -> EmailIngestResponse:
    try:
        status, classified = reply_actions_service.send_reply(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
            reply_subject=request.reply_subject,
            reply_body=request.reply_body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EmailIngestResponse(status=status, tenant_id=tenant_id, email=classified)


@router.post("/emails/{source_email_id}/gmail-draft", response_model=GmailDraftResponse, status_code=200)
def create_gmail_draft_for_email(
    tenant_id: str,
    source_email_id: str,
    request: SendReplyRequest,
    reply_actions_service: ReplyActionsService = Depends(get_reply_actions_service),
) -> GmailDraftResponse:
    try:
        status, classified, draft_id = reply_actions_service.create_gmail_draft(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
            reply_subject=request.reply_subject,
            reply_body=request.reply_body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GmailIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return GmailDraftResponse(status=status, tenant_id=tenant_id, draft_id=draft_id, email=classified)


@router.patch("/emails/{source_email_id}/status", response_model=EmailIngestResponse, status_code=200)
def update_case_status_for_email(
    tenant_id: str,
    source_email_id: str,
    request: UpdateCaseStatusRequest,
    repository: ClassifiedEmailRepository = Depends(get_email_repository),
) -> EmailIngestResponse:
    try:
        updated = repository.update_case_status(
            tenant_id=tenant_id,
            source_email_id=source_email_id,
            status=request.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EmailIngestResponse(status="status_updated", tenant_id=tenant_id, email=updated)


@router.get("/dashboard", response_model=TenantDashboardResponse)
def get_tenant_dashboard(
    tenant_id: str,
    selected_date: date | None = Query(default=None, alias="date"),
    repository: ClassifiedEmailRepository = Depends(get_email_repository),
) -> TenantDashboardResponse:
    counts = repository.category_counts(tenant_id=tenant_id, on_date=selected_date)
    cards = [
        DashboardCard(category="payment_claim", count=counts["payment_claim"]),
        DashboardCard(category="dispute", count=counts["dispute"]),
        DashboardCard(category="general_ar_request", count=counts["general_ar_request"]),
    ]
    return TenantDashboardResponse(
        tenant_id=tenant_id,
        total_emails=sum(card.count for card in cards),
        cards=cards,
    )


@router.get("/emails", response_model=TenantEmailListResponse)
def list_classified_emails(
    tenant_id: str,
    category: Category | None = Query(default=None),
    selected_date: date | None = Query(default=None, alias="date"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    repository: ClassifiedEmailRepository = Depends(get_email_repository),
) -> TenantEmailListResponse:
    emails = repository.list_emails(
        tenant_id=tenant_id,
        category=category,
        on_date=selected_date,
        order=order,
    )
    return TenantEmailListResponse(
        tenant_id=tenant_id,
        total=len(emails),
        emails=emails,
    )
