import re

from app.services.analysis.models import AnalysisResult, LLMUnavailableError
from app.services.analysis.normalization import (
    dedupe_strings,
    limit_detail,
    to_float_amounts,
    to_iso_dates,
)
from app.services.llm import LangChainLLMService
from app.services.llm.workflow_graph import build_email_workflow_graph


class HybridEmailAnalyzer:
    invoice_pattern = re.compile(r"\b(?:INV[-\s]?\d+|\d{6,})\b", re.IGNORECASE)
    amount_pattern = re.compile(
        r"\b(?:USD|EUR|GBP|INR|\$|€|£)\s?\d[\d,]*(?:\.\d{1,2})?\b|\b\d[\d,]*(?:\.\d{1,2})\b"
    )
    date_pattern = re.compile(
        r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b",
        re.IGNORECASE,
    )

    def __init__(
        self,
        primary_llm_service: LangChainLLMService | None,
        fallback_llm_service: LangChainLLMService | None = None,
    ) -> None:
        self._primary_llm_service = primary_llm_service
        self._fallback_llm_service = fallback_llm_service

    def analyze(self, subject: str, body: str, invoice_catalog: list[dict]) -> AnalysisResult:
        classification_payload = None
        extraction_payload = None
        case_draft_payload = None
        next_step_payload = None
        invoice_match_payload = None
        reply_draft_payload = None
        llm_error: str | None = None
        llm_source = "none"

        for source_name, service in (
            ("llm_primary", self._primary_llm_service),
            ("llm_fallback_model", self._fallback_llm_service),
        ):
            if service is None:
                continue
            try:
                graph = build_email_workflow_graph(service)
                state = graph.invoke(
                    {
                        "subject": subject,
                        "body": body,
                        "invoice_catalog": invoice_catalog,
                        "should_generate_reply": True,
                    }
                )
                classification_payload = state.get("classification")
                extraction_payload = state.get("extraction")
                case_draft_payload = state.get("case_draft")
                next_step_payload = state.get("next_step")
                invoice_match_payload = state.get("invoice_match")
                reply_draft_payload = state.get("reply_draft")
                llm_source = source_name
                break
            except Exception as exc:  # noqa: BLE001
                llm_error = str(exc)

        if classification_payload and extraction_payload and next_step_payload and case_draft_payload:
            category = classification_payload.category
            confidence = float(classification_payload.confidence)
            reason = classification_payload.reason
            classification_source = llm_source
        else:
            raise LLMUnavailableError(
                "All configured models are unavailable. Please try again later."
                + (f" Last error: {llm_error}" if llm_error else "")
            )

        text = f"{subject}\n{body}"
        regex_invoice_refs = dedupe_strings(self.invoice_pattern.findall(text))
        regex_amounts = dedupe_strings(self.amount_pattern.findall(text))
        regex_dates = dedupe_strings(self.date_pattern.findall(text))

        llm_invoice_refs = extraction_payload.invoice_references or []
        llm_amounts = extraction_payload.amounts or []
        llm_dates = extraction_payload.mentioned_dates or []

        invoice_refs = dedupe_strings(regex_invoice_refs + llm_invoice_refs)
        amount_values = to_float_amounts(regex_amounts + llm_amounts)
        date_values = to_iso_dates(regex_dates + llm_dates)

        customer_name = extraction_payload.customer_name
        detail = extraction_payload.detail
        extraction_source = "hybrid_llm_regex"

        if category == "dispute" and not detail:
            detail = "Customer indicates a dispute that needs analyst review."

        return AnalysisResult(
            category=category,
            confidence=max(0.0, min(1.0, confidence)),
            reason=reason,
            classification_source=classification_source,
            customer_name=customer_name,
            invoice_references=invoice_refs or None,
            amounts=amount_values or None,
            mentioned_dates=date_values or None,
            detail=limit_detail(detail) if detail else None,
            extraction_source=extraction_source,
            case_title=case_draft_payload.case_title,
            case_summary=case_draft_payload.case_summary,
            case_priority=case_draft_payload.case_priority,
            invoice_match_summary=(invoice_match_payload or {}).get("summary"),
            invoice_matches=(invoice_match_payload or {}).get("matches"),
            next_best_action=limit_detail(next_step_payload.next_best_action),
            next_best_action_reason=limit_detail(next_step_payload.next_best_action_reason),
            reply_draft_subject=str((reply_draft_payload or {}).get("reply_subject", "")),
            reply_draft_body=str((reply_draft_payload or {}).get("reply_body", "")),
        )
