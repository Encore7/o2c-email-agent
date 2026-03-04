from langchain_core.tools import tool


@tool("draft_customer_reply")
def draft_customer_reply_tool(
    customer_name: str | None,
    category: str,
    next_best_action: str,
) -> dict:
    """Draft a concise customer email reply from the generated case and recommendation."""
    greeting = f"Hi {customer_name}," if customer_name else "Hi,"
    body = (
        f"{greeting}\n\n"
        f"Thanks for your message regarding {category.replace('_', ' ')}.\n"
        f"Our AR team will now: {next_best_action}\n"
        "We will update you once this step is completed.\n\n"
        "Regards,\nAR Team"
    )
    return {"reply_subject": "Next Steps on Your AR Request", "reply_body": body}
