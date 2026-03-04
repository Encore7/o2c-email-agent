from langchain_core.tools import tool

from app.services.analysis.models import CaseDraftPayload
from app.services.analysis.normalization import limit_detail


VALID_PRIORITIES = {"low", "medium", "high"}


def create_structured_case_for_review(case_draft: CaseDraftPayload) -> CaseDraftPayload:
    title = limit_detail(case_draft.case_title, max_len=100)
    summary = limit_detail(case_draft.case_summary, max_len=280)
    priority = case_draft.case_priority.strip().lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"
    return CaseDraftPayload(
        case_title=title,
        case_summary=summary,
        case_priority=priority,
    )


@tool("create_structured_case_for_review")
def create_structured_case_for_review_tool(
    case_title: str,
    case_summary: str,
    case_priority: str,
) -> dict:
    """Normalize a draft case so finance team gets a concise, valid structured case."""
    normalized = create_structured_case_for_review(
        CaseDraftPayload(
            case_title=case_title,
            case_summary=case_summary,
            case_priority=case_priority,
        )
    )
    return normalized.model_dump()
