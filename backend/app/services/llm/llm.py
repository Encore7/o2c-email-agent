from app.services.analysis.models import (
    CaseDraftPayload,
    ClassificationPayload,
    ExtractionPayload,
    LLMUnavailableError,
    NextStepPayload,
)
from app.services.llm.prompts import (
    build_case_prompt,
    build_classification_prompt,
    build_extraction_prompt,
    build_next_step_prompt,
)
from app.services.llm.providers import build_chat_model


class LangChainLLMService:
    def __init__(
        self,
        provider: str,
        model: str,
        temperature: float,
        ollama_base_url: str,
        api_keys: dict[str, str | None],
    ) -> None:
        self._llm = build_chat_model(
            provider=provider,
            model=model,
            temperature=temperature,
            ollama_base_url=ollama_base_url,
            api_keys=api_keys,
        )
        self._classification_prompt = build_classification_prompt()
        self._extraction_prompt = build_extraction_prompt()
        self._case_prompt = build_case_prompt()
        self._next_step_prompt = build_next_step_prompt()

    def classify(self, subject: str, body: str) -> ClassificationPayload:
        return self._invoke_structured(
            prompt=self._classification_prompt,
            schema=ClassificationPayload,
            inputs={"subject": subject, "body": body},
        )

    def extract(self, subject: str, body: str) -> ExtractionPayload:
        return self._invoke_structured(
            prompt=self._extraction_prompt,
            schema=ExtractionPayload,
            inputs={"subject": subject, "body": body},
        )

    def recommend_next_step(
        self,
        category: str,
        case_draft: CaseDraftPayload,
        invoice_match_summary: str | None = None,
    ) -> NextStepPayload:
        return self._invoke_structured(
            prompt=self._next_step_prompt,
            schema=NextStepPayload,
            inputs={
                "category": category,
                "case_title": case_draft.case_title,
                "case_summary": case_draft.case_summary,
                "case_priority": case_draft.case_priority,
                "invoice_match_summary": invoice_match_summary or "No invoice matching attempted.",
            },
        )

    def draft_case_for_review(
        self,
        subject: str,
        body: str,
        classification: ClassificationPayload,
        extraction: ExtractionPayload,
    ) -> CaseDraftPayload:
        return self._invoke_structured(
            prompt=self._case_prompt,
            schema=CaseDraftPayload,
            inputs={
                "subject": subject,
                "body": body,
                "category": classification.category,
                "classification_reason": classification.reason,
                "customer_name": extraction.customer_name,
                "invoice_references": extraction.invoice_references,
                "amounts": extraction.amounts,
                "mentioned_dates": extraction.mentioned_dates,
                "detail": extraction.detail,
            },
        )

    def _invoke_structured(self, prompt, schema, inputs: dict):
        structured_llm = self._llm.with_structured_output(schema)
        chain = prompt | structured_llm
        response = chain.invoke(inputs)
        if isinstance(response, schema):
            return response
        if isinstance(response, dict):
            return schema.model_validate(response)
        raise LLMUnavailableError("Structured output parsing failed.")
