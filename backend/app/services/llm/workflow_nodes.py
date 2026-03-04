from app.services.llm.llm import LangChainLLMService
from app.services.analysis.models import LLMUnavailableError
from app.services.analysis.normalization import to_float_amounts
from app.services.llm.workflow_state import EmailWorkflowState
from app.services.tools import (
    attempt_invoice_match_tool,
    create_structured_case_for_review_tool,
    draft_customer_reply_tool,
)


def classify_extract_node(service: LangChainLLMService, state: EmailWorkflowState) -> EmailWorkflowState:
    subject = state["subject"]
    body = state["body"]
    classification = service.classify(subject=subject, body=body)
    extraction = service.extract(subject=subject, body=body)
    return {"classification": classification, "extraction": extraction}


def invoice_match_node(state: EmailWorkflowState) -> EmailWorkflowState:
    extraction = state["extraction"]
    invoice_catalog = state.get("invoice_catalog", [])
    invoice_match = attempt_invoice_match_tool.invoke(
        {
            "invoice_references": extraction.invoice_references,
            "amounts": to_float_amounts(extraction.amounts or []),
            "invoice_catalog": invoice_catalog,
        }
    )
    return {"invoice_match": invoice_match}


def case_create_node(service: LangChainLLMService, state: EmailWorkflowState) -> EmailWorkflowState:
    subject = state["subject"]
    body = state["body"]
    classification = state["classification"]
    extraction = state["extraction"]

    case_draft = service.draft_case_for_review(
        subject=subject,
        body=body,
        classification=classification,
        extraction=extraction,
    )
    normalized = create_structured_case_for_review_tool.invoke(case_draft.model_dump())
    try:
        normalized_case = case_draft.model_validate(normalized)
    except Exception as exc:  # noqa: BLE001
        raise LLMUnavailableError(f"Case tool output invalid: {exc}") from exc
    return {"case_draft": normalized_case}


def next_step_node(service: LangChainLLMService, state: EmailWorkflowState) -> EmailWorkflowState:
    classification = state["classification"]
    case_draft = state["case_draft"]
    invoice_match_summary = (state.get("invoice_match") or {}).get("summary")
    next_step = service.recommend_next_step(
        category=classification.category,
        case_draft=case_draft,
        invoice_match_summary=invoice_match_summary,
    )
    return {"next_step": next_step}


def reply_draft_node(state: EmailWorkflowState) -> EmailWorkflowState:
    extraction = state["extraction"]
    classification = state["classification"]
    next_step = state["next_step"]
    draft = draft_customer_reply_tool.invoke(
        {
            "customer_name": extraction.customer_name,
            "category": classification.category,
            "next_best_action": next_step.next_best_action,
        }
    )
    return {"reply_draft": draft}


def should_generate_reply(state: EmailWorkflowState) -> str:
    return "reply_draft" if state.get("should_generate_reply") else "end"
