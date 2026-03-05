from app.services.llm.workflow_nodes import (
    case_create_node,
    classify_extract_node,
    invoice_match_node,
    next_step_node,
    reply_draft_node,
    should_generate_reply,
)
from tests.mocks.mock_llm import MockLLM


def test_classify_extract_node():
    state = {"subject": "Payment sent INV-10000", "body": "Regards,\nFreshMart Retail Finance Team"}
    out = classify_extract_node(MockLLM(), state)
    assert out["classification"].category == "payment_claim"
    assert out["extraction"].customer_name is not None


def test_invoice_match_node():
    llm = MockLLM()
    state = {
        "subject": "s",
        "body": "b",
        "extraction": llm.extract("s", "b"),
        "invoice_catalog": [{"invoice_id": "INV-10000", "amount": 1375.0, "status": "open"}],
    }
    out = invoice_match_node(state)
    assert out["invoice_match"]["match_count"] == 1


def test_case_next_reply_nodes():
    llm = MockLLM()
    state = {
        "subject": "s",
        "body": "b",
        "classification": llm.classify("s", "b"),
        "extraction": llm.extract("s", "b"),
        "invoice_match": {"summary": "1 invoice match(es) found."},
    }
    case_out = case_create_node(llm, state)
    state.update(case_out)
    next_out = next_step_node(llm, state)
    state.update(next_out)
    reply_out = reply_draft_node(state)
    assert "case_draft" in case_out
    assert "next_step" in next_out
    assert reply_out["reply_draft"]["reply_subject"]


def test_should_generate_reply_branch():
    assert should_generate_reply({"should_generate_reply": True}) == "reply_draft"
    assert should_generate_reply({"should_generate_reply": False}) == "end"
