from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.services.llm.llm import LangChainLLMService
from app.services.llm.workflow_nodes import (
    case_create_node,
    classify_node,
    extract_node,
    invoice_match_node,
    next_step_node,
    reply_draft_node,
    should_generate_reply,
)
from app.services.llm.workflow_state import EmailWorkflowState


@lru_cache
def build_email_workflow_graph(service: LangChainLLMService):
    graph = StateGraph(EmailWorkflowState)
    graph.add_node("classify", lambda state: classify_node(service, state))
    graph.add_node("extract", lambda state: extract_node(service, state))
    graph.add_node("invoice_match", invoice_match_node)
    graph.add_node("case_create", lambda state: case_create_node(service, state))
    graph.add_node("next_step", lambda state: next_step_node(service, state))
    graph.add_node("reply_draft", reply_draft_node)

    graph.add_edge(START, "classify")
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "invoice_match")
    graph.add_edge("classify", "case_create")
    graph.add_edge("invoice_match", "case_create")
    graph.add_edge("case_create", "next_step")
    graph.add_conditional_edges(
        "next_step",
        should_generate_reply,
        {
            "reply_draft": "reply_draft",
            "end": END,
        },
    )
    graph.add_edge("reply_draft", END)
    return graph.compile()
