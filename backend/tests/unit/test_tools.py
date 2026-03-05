from app.services.analysis.models import CaseDraftPayload
from app.services.tools.case_builder import create_structured_case_for_review
from app.services.tools.invoice_matcher import attempt_invoice_match_tool
from app.services.tools.reply_drafter import draft_customer_reply_tool


def test_case_builder_normalizes_priority_and_limits_text():
    draft = CaseDraftPayload(
        case_title="X" * 150,
        case_summary="Y" * 400,
        case_priority="CRITICAL",
    )
    out = create_structured_case_for_review(draft)
    assert len(out.case_title) <= 100
    assert len(out.case_summary) <= 280
    assert out.case_priority == "medium"


def test_invoice_match_tool_matches_by_reference():
    out = attempt_invoice_match_tool.invoke(
        {
            "invoice_references": ["INV-10000"],
            "amounts": [1375.0],
            "invoice_catalog": [
                {"invoice_id": "INV-10000", "amount": 1375.0, "status": "open"},
                {"invoice_id": "INV-10001", "amount": 1500.0, "status": "open"},
            ],
        }
    )
    assert out["match_count"] == 1
    assert out["matches"][0]["invoice_id"] == "INV-10000"
    assert out["matches"][0]["match_confidence"] >= 0.85


def test_reply_drafter_generates_multiline_message():
    out = draft_customer_reply_tool.invoke(
        {
            "customer_name": "Alex",
            "category": "dispute",
            "next_best_action": "Review submitted dispute documents.",
        }
    )
    assert out["reply_subject"] == "Next Steps on Your AR Request"
    assert "Hi Alex," in out["reply_body"]
    assert "Our AR team will now:" in out["reply_body"]
    assert "\n\n" in out["reply_body"]
