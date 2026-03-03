import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import CaseRecord, ClassifiedEmailRecord, SourceEmail
from app.schemas.email import Category, ClassifiedEmail

CASE_STATUS_MAP = {
    "open": "under_review",
    "waiting_customer": "needs_further_review",
    "resolved": "reviewed",
}
VALID_CASE_STATUSES = {"new", "under_review", "reviewed", "needs_further_review"}


class ClassifiedEmailRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_classified_by_source(self, tenant_id: str, source_email_id: str) -> ClassifiedEmail | None:
        source_uuid = uuid.UUID(source_email_id)
        stmt = (
            select(ClassifiedEmailRecord)
            .options(selectinload(ClassifiedEmailRecord.case))
            .where(
                ClassifiedEmailRecord.tenant_id == tenant_id,
                ClassifiedEmailRecord.source_email_id == source_uuid,
            )
        )
        record = self._session.scalar(stmt)
        return self._to_classified_email(record) if record else None

    def save_case_and_classification(
        self,
        tenant_id: str,
        source_email: SourceEmail,
        category: Category,
        confidence: float,
        reason: str,
        classification_source: str,
        customer_name: str | None,
        invoice_references: list[str] | None,
        amounts: list[float] | None,
        mentioned_dates: list[str] | None,
        detail: str | None,
        extraction_source: str,
        case_title: str,
        case_summary: str,
        case_priority: str,
        invoice_match_summary: str | None,
        invoice_matches: list[dict] | None,
        next_best_action: str,
        next_best_action_reason: str,
        reply_draft_subject: str,
        reply_draft_body: str,
    ) -> ClassifiedEmail:
        case_id = f"case_{tenant_id}_{source_email.email_id}"
        case_stmt = select(CaseRecord).where(
            CaseRecord.tenant_id == tenant_id,
            CaseRecord.email_id == source_email.email_id,
        )
        case = self._session.scalar(case_stmt)
        if case is None:
            case = CaseRecord(
                case_id=case_id,
                tenant_id=tenant_id,
                email_id=source_email.email_id,
                category=category,
                case_title=case_title,
                case_summary=case_summary,
                case_priority=case_priority,
                next_best_action=next_best_action,
                next_best_action_reason=next_best_action_reason,
                status="new",
            )
            self._session.add(case)
        else:
            case.category = category
            case.case_title = case_title
            case.case_summary = case_summary
            case.case_priority = case_priority
            case.next_best_action = next_best_action
            case.next_best_action_reason = next_best_action_reason
            case.updated_at = datetime.utcnow()

        class_stmt = (
            select(ClassifiedEmailRecord)
            .options(selectinload(ClassifiedEmailRecord.case))
            .where(ClassifiedEmailRecord.source_email_id == source_email.source_email_id)
        )
        record = self._session.scalar(class_stmt)
        parsed_dates = [date.fromisoformat(v) for v in (mentioned_dates or [])]
        if record is None:
            record = ClassifiedEmailRecord(
                source_email_id=source_email.source_email_id,
                tenant_id=tenant_id,
                email_id=source_email.email_id,
                received_at=source_email.received_at,
                from_email=source_email.from_email,
                subject=source_email.subject,
                body=source_email.body,
                category=category,
                confidence=confidence,
                reason=reason,
                classification_source=classification_source,
                customer_name=customer_name,
                invoice_references=invoice_references or [],
                amounts=amounts or [],
                mentioned_dates=parsed_dates,
                detail=detail,
                invoice_match_summary=invoice_match_summary,
                invoice_matches=invoice_matches,
                reply_draft_subject=reply_draft_subject,
                reply_draft_body=reply_draft_body,
                extraction_source=extraction_source,
                case=case,
            )
            self._session.add(record)
        else:
            record.category = category
            record.confidence = confidence
            record.reason = reason
            record.classification_source = classification_source
            record.customer_name = customer_name
            record.invoice_references = invoice_references or []
            record.amounts = amounts or []
            record.mentioned_dates = parsed_dates
            record.detail = detail
            record.invoice_match_summary = invoice_match_summary
            record.invoice_matches = invoice_matches
            record.reply_draft_subject = reply_draft_subject
            record.reply_draft_body = reply_draft_body
            record.extraction_source = extraction_source
            record.case = case

        self._session.commit()
        self._session.refresh(record)
        self._session.refresh(case)
        return self._to_classified_email(record)

    def list_emails(
        self,
        tenant_id: str,
        category: Category | None = None,
        on_date: date | None = None,
        order: Literal["asc", "desc"] = "desc",
    ) -> list[ClassifiedEmail]:
        stmt = (
            select(ClassifiedEmailRecord)
            .options(selectinload(ClassifiedEmailRecord.case))
            .where(ClassifiedEmailRecord.tenant_id == tenant_id)
        )
        if category:
            stmt = stmt.where(ClassifiedEmailRecord.category == category)
        if on_date:
            stmt = stmt.where(func.date(ClassifiedEmailRecord.received_at) == on_date)
        sort_col = ClassifiedEmailRecord.received_at.desc() if order == "desc" else ClassifiedEmailRecord.received_at.asc()
        stmt = stmt.order_by(sort_col)
        rows = self._session.scalars(stmt).all()
        return [self._to_classified_email(row) for row in rows]

    def category_counts(self, tenant_id: str, on_date: date | None = None) -> dict[Category, int]:
        stmt = (
            select(ClassifiedEmailRecord.category, func.count(ClassifiedEmailRecord.source_email_id))
            .where(ClassifiedEmailRecord.tenant_id == tenant_id)
            .group_by(ClassifiedEmailRecord.category)
        )
        if on_date:
            stmt = stmt.where(func.date(ClassifiedEmailRecord.received_at) == on_date)
        rows = self._session.execute(stmt).all()
        result = {"payment_claim": 0, "dispute": 0, "general_ar_request": 0}
        for category_value, count in rows:
            if category_value in result:
                result[category_value] = int(count)
        return result

    def update_reply_draft(
        self,
        tenant_id: str,
        source_email_id: str,
        reply_subject: str,
        reply_body: str,
    ) -> ClassifiedEmail:
        source_uuid = uuid.UUID(source_email_id)
        stmt = (
            select(ClassifiedEmailRecord)
            .options(selectinload(ClassifiedEmailRecord.case))
            .where(
                ClassifiedEmailRecord.tenant_id == tenant_id,
                ClassifiedEmailRecord.source_email_id == source_uuid,
            )
        )
        record = self._session.scalar(stmt)
        if record is None:
            raise ValueError(f"classified email not found for source_email_id {source_email_id}")
        record.reply_draft_subject = reply_subject
        record.reply_draft_body = reply_body
        self._session.commit()
        self._session.refresh(record)
        return self._to_classified_email(record)

    def update_case_status(
        self,
        tenant_id: str,
        source_email_id: str,
        status: str,
    ) -> ClassifiedEmail:
        source_uuid = uuid.UUID(source_email_id)
        stmt = (
            select(ClassifiedEmailRecord)
            .options(selectinload(ClassifiedEmailRecord.case))
            .where(
                ClassifiedEmailRecord.tenant_id == tenant_id,
                ClassifiedEmailRecord.source_email_id == source_uuid,
            )
        )
        record = self._session.scalar(stmt)
        if record is None or record.case is None:
            raise ValueError(f"classified email not found for source_email_id {source_email_id}")
        normalized = self._normalize_case_status(status)
        if normalized not in VALID_CASE_STATUSES:
            raise ValueError(f"invalid status '{status}'")
        record.case.status = normalized
        record.case.updated_at = datetime.utcnow()
        self._session.commit()
        self._session.refresh(record)
        return self._to_classified_email(record)

    def _to_classified_email(self, row: ClassifiedEmailRecord | None) -> ClassifiedEmail:
        if row is None or row.case is None:
            raise ValueError("Classification row missing case relation.")
        return ClassifiedEmail(
            source_email_id=str(row.source_email_id),
            id=row.email_id,
            tenant_id=row.tenant_id,
            received_at=self._dt_to_iso(row.received_at),
            from_email=row.from_email,
            subject=row.subject,
            body=row.body,
            category=row.category,
            confidence=float(row.confidence),
            reason=row.reason,
            classification_source=row.classification_source,
            customer_name=row.customer_name,
            invoice_references=list(row.invoice_references or []) or None,
            amounts=[float(v) for v in (row.amounts or [])] or None,
            mentioned_dates=[d.isoformat() for d in (row.mentioned_dates or [])] or None,
            detail=row.detail,
            extraction_source=row.extraction_source,
            invoice_match_summary=row.invoice_match_summary,
            invoice_matches=row.invoice_matches,
            case_id=row.case_id,
            case_title=row.case.case_title,
            case_summary=row.case.case_summary,
            case_priority=row.case.case_priority,
            next_best_action=row.case.next_best_action,
            next_best_action_reason=row.case.next_best_action_reason,
            reply_draft_subject=row.reply_draft_subject,
            reply_draft_body=row.reply_draft_body,
            case_status=self._normalize_case_status(row.case.status),
        )

    @staticmethod
    def _dt_to_iso(value: datetime | str) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    @staticmethod
    def _normalize_case_status(value: str | None) -> str:
        if not value:
            return "new"
        lowered = value.strip().lower()
        mapped = CASE_STATUS_MAP.get(lowered, lowered)
        if mapped in VALID_CASE_STATUSES:
            return mapped
        return "under_review"
