import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SourceEmail(Base):
    __tablename__ = "source_emails"
    __table_args__ = (UniqueConstraint("tenant_id", "email_id", name="uq_source_tenant_email"),)

    source_email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    email_id: Mapped[str] = mapped_column(String, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    from_email: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    classification: Mapped["ClassifiedEmailRecord"] = relationship(
        back_populates="source_email", uselist=False
    )
    outbound_emails: Mapped[list["OutboundEmailRecord"]] = relationship(
        back_populates="source_email"
    )


class InvoiceRecord(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_id", name="uq_invoice_tenant_invoice"),)

    invoice_pk: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    invoice_id: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaseRecord(Base):
    __tablename__ = "cases"
    __table_args__ = (UniqueConstraint("tenant_id", "email_id", name="uq_case_tenant_email"),)

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    email_id: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    case_title: Mapped[str | None] = mapped_column(String)
    case_summary: Mapped[str | None] = mapped_column("dispute_details", Text)
    case_priority: Mapped[str | None] = mapped_column(String)
    next_best_action: Mapped[str] = mapped_column(Text, nullable=False)
    next_best_action_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    classifications: Mapped[list["ClassifiedEmailRecord"]] = relationship(back_populates="case")


class ClassifiedEmailRecord(Base):
    __tablename__ = "classified_emails"
    __table_args__ = (UniqueConstraint("tenant_id", "email_id", name="uq_class_tenant_email"),)

    source_email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_emails.source_email_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    email_id: Mapped[str] = mapped_column(String, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    from_email: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    classification_source: Mapped[str] = mapped_column(String, nullable=False, default="llm_primary")
    customer_name: Mapped[str | None] = mapped_column(String)
    invoice_references: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    amounts: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False, default=list)
    mentioned_dates: Mapped[list[datetime.date]] = mapped_column(ARRAY(Date), nullable=False, default=list)
    detail: Mapped[str | None] = mapped_column(Text)
    invoice_match_summary: Mapped[str | None] = mapped_column(Text)
    invoice_matches: Mapped[list[dict] | None] = mapped_column(JSONB)
    reply_draft_subject: Mapped[str | None] = mapped_column(Text)
    reply_draft_body: Mapped[str | None] = mapped_column(Text)
    extraction_source: Mapped[str] = mapped_column(String, nullable=False, default="hybrid_llm_regex")
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.case_id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_email: Mapped[SourceEmail] = relationship(back_populates="classification")
    case: Mapped[CaseRecord] = relationship(back_populates="classifications")


class OutboundEmailRecord(Base):
    __tablename__ = "outbound_emails"

    outbound_email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_emails.source_email_id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    email_id: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="sent_simulated")
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_email: Mapped[SourceEmail] = relationship(back_populates="outbound_emails")
