from typing import Any, TypedDict

from app.services.analysis.models import CaseDraftPayload, ClassificationPayload, ExtractionPayload, NextStepPayload


class EmailWorkflowState(TypedDict, total=False):
    subject: str
    body: str
    invoice_catalog: list[dict]
    classification: ClassificationPayload
    extraction: ExtractionPayload
    invoice_match: dict[str, Any]
    case_draft: CaseDraftPayload
    next_step: NextStepPayload
    reply_draft: dict[str, str]
    tool_logs: list[dict[str, Any]]
    errors: list[str]
    should_generate_reply: bool
