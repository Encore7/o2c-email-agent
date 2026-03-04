from langchain_core.tools import tool


@tool("attempt_invoice_match")
def attempt_invoice_match_tool(
    invoice_references: list[str] | None,
    amounts: list[float] | None,
    invoice_catalog: list[dict],
) -> dict:
    """Attempt invoice matching against internal invoice dataset."""
    refs = {ref.strip().lower() for ref in (invoice_references or []) if ref.strip()}
    amount_set = {round(val, 2) for val in (amounts or [])}
    matches: list[dict] = []
    for record in invoice_catalog:
        id_match = record["invoice_id"].lower() in refs
        amount_match = round(float(record["amount"]), 2) in amount_set if amount_set else False
        if id_match or amount_match:
            confidence = 1.0 if id_match and amount_match else 0.85 if id_match else 0.7
            matches.append(
                {
                    "invoice_id": record["invoice_id"],
                    "amount": float(record["amount"]),
                    "status": record["status"],
                    "match_confidence": confidence,
                }
            )
    return {
        "matches": matches,
        "match_count": len(matches),
        "summary": (
            f"{len(matches)} invoice match(es) found."
            if matches
            else "No reliable invoice match found in dataset."
        ),
    }
