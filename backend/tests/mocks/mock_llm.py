from app.services.analysis.models import (
    CaseDraftPayload,
    ClassificationPayload,
    ExtractionPayload,
    NextStepPayload,
)


class MockLLM:
    def classify(self, subject: str, body: str) -> ClassificationPayload:
        del subject, body
        return ClassificationPayload(
            category="payment_claim",
            confidence=0.92,
            reason="Customer states payment was sent.",
        )

    def extract(self, subject: str, body: str) -> ExtractionPayload:
        del subject, body
        return ExtractionPayload(
            customer_name="FreshMart Retail Finance Team",
            invoice_references=["INV-10000"],
            amounts=["1375.00"],
            mentioned_dates=["2026-01-20"],
            detail="Customer says payment was transferred today for INV-10000.",
        )

    def draft_case_for_review(
        self,
        subject: str,
        body: str,
        classification: ClassificationPayload,
        extraction: ExtractionPayload,
    ) -> CaseDraftPayload:
        del subject, body, classification, extraction
        return CaseDraftPayload(
            case_title="Payment claim for INV-10000",
            case_summary="Customer claims payment already sent for INV-10000.",
            case_priority="medium",
        )

    def recommend_next_step(
        self,
        category: str,
        case_draft: CaseDraftPayload,
        invoice_match_summary: str | None = None,
    ) -> NextStepPayload:
        del category, case_draft, invoice_match_summary
        return NextStepPayload(
            next_best_action="Match remittance against open invoice and post receipt.",
            next_best_action_reason="Payment claim requires ledger validation before closure.",
        )
