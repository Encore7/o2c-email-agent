import logging

from opentelemetry import trace

from app.schemas.email import ClassifiedEmail, ProcessSourceEmailRequest
from app.repositories.classified_email_repository import ClassifiedEmailRepository
from app.repositories.source_email_repository import SourceEmailRepository
from app.services.analysis import HybridEmailAnalyzer

tracer = trace.get_tracer(__name__)
logger = logging.getLogger("app.email_processing")


class EmailProcessingService:
    def __init__(
        self,
        source_repository: SourceEmailRepository,
        classified_repository: ClassifiedEmailRepository,
        analyzer: HybridEmailAnalyzer,
    ) -> None:
        self._source_repository = source_repository
        self._classified_repository = classified_repository
        self._analyzer = analyzer

    def process_source_email(
        self, tenant_id: str, request: ProcessSourceEmailRequest
    ) -> tuple[str, ClassifiedEmail]:
        with tracer.start_as_current_span("email_processing.process_source_email") as span:
            span.set_attribute("o2c.tenant_id", tenant_id)
            span.set_attribute("o2c.source_email_id", str(request.source_email_id))
            existing = self._classified_repository.get_classified_by_source(
                tenant_id=tenant_id, source_email_id=request.source_email_id
            )
            if existing is not None:
                span.set_attribute("o2c.status", "duplicate")
                logger.info(
                    "email_processing_duplicate",
                    extra={
                        "tenant_id": tenant_id,
                        "source_email_id": str(request.source_email_id),
                    },
                )
                return "duplicate", existing

            source_email = self._source_repository.get_source_email(
                tenant_id=tenant_id, source_email_id=request.source_email_id
            )
            if source_email is None:
                raise ValueError(f"source_email_id {request.source_email_id} not found")

            invoice_catalog = self._source_repository.list_invoice_catalog(tenant_id=tenant_id)

            analysis = self._analyzer.analyze(
                subject=source_email.subject,
                body=source_email.body,
                invoice_catalog=invoice_catalog,
            )

            saved = self._classified_repository.save_case_and_classification(
                tenant_id=tenant_id,
                source_email=source_email,
                category=analysis.category,
                confidence=analysis.confidence,
                reason=analysis.reason,
                classification_source=analysis.classification_source,
                customer_name=analysis.customer_name,
                invoice_references=analysis.invoice_references,
                amounts=analysis.amounts,
                mentioned_dates=analysis.mentioned_dates,
                detail=analysis.detail,
                extraction_source=analysis.extraction_source,
                case_title=analysis.case_title,
                case_summary=analysis.case_summary,
                case_priority=analysis.case_priority,
                invoice_match_summary=analysis.invoice_match_summary,
                invoice_matches=analysis.invoice_matches,
                next_best_action=analysis.next_best_action,
                next_best_action_reason=analysis.next_best_action_reason,
                reply_draft_subject=analysis.reply_draft_subject,
                reply_draft_body=analysis.reply_draft_body,
            )
            span.set_attribute("o2c.status", "processed")
            logger.info(
                "email_processed",
                extra={
                    "tenant_id": tenant_id,
                    "source_email_id": str(request.source_email_id),
                },
            )
            return "processed", saved
