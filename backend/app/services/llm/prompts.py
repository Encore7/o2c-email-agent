from langchain_core.prompts import ChatPromptTemplate


def build_classification_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are an O2C AR email classifier. Output must match structured schema."),
            (
                "human",
                (
                    "Classify this customer AR email into exactly one category:\n"
                    "1) payment_claim: customer says payment was made/sent/processed.\n"
                    "2) dispute: customer reports issue, short pay, damaged goods, wrong invoice, deductions.\n"
                    "3) general_ar_request: asks for invoice copy, statement, account details, billing updates.\n"
                    "Return confidence in [0,1] and a concise reason.\n"
                    "Use evidence from subject and body only.\n"
                    "Subject: {subject}\nBody: {body}"
                ),
            ),
        ]
    )


def build_extraction_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are an O2C AR data extractor. Output must match structured schema."),
            (
                "human",
                (
                    "Extract fields from this AR email using subject and body:\n"
                    "- customer_name: explicit customer/account name; check signature/footer lines after closings like 'Regards', 'Best regards', 'Thanks'.\n"
                    "- invoice_references: explicit invoice IDs.\n"
                    "- amounts: explicit amounts as strings.\n"
                    "- mentioned_dates: explicit date mentions.\n"
                    "- detail: one-line key context (<=140 chars).\n"
                    "If a field is not present, return null.\n"
                    "Do not invent values.\n"
                    "Subject: {subject}\nBody: {body}"
                ),
            ),
        ]
    )


def build_case_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are an O2C AR case drafting assistant. Output must match structured schema."),
            (
                "human",
                (
                    "Create a structured finance case for human review from classification and extraction output.\n"
                    "Return:\n"
                    "- case_title: brief, actionable title.\n"
                    "- case_summary: concise operational summary (facts only, max 280 chars).\n"
                    "- case_priority: low/medium/high.\n"
                    "Priority rubric:\n"
                    "- high: urgent financial or operational risk (large amount, repeated follow-up, escalation/legal/service impact).\n"
                    "- medium: standard payment/dispute handling with moderate business impact.\n"
                    "- low: routine informational/admin request with no urgency.\n"
                    "Do not invent facts.\n"
                    "Subject: {subject}\n"
                    "Body: {body}\n"
                    "Category: {category}\n"
                    "Classification reason: {classification_reason}\n"
                    "Customer: {customer_name}\n"
                    "Invoices: {invoice_references}\n"
                    "Amounts: {amounts}\n"
                    "Dates: {mentioned_dates}\n"
                    "Detail: {detail}"
                ),
            ),
        ]
    )


def build_next_step_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are an O2C AR operations assistant. Output must match structured schema."),
            (
                "human",
                (
                    "Given this structured case, recommend one immediate AR next action.\n"
                    "Action should be operational and concise (<=140 chars).\n"
                    "Examples: payment match workflow, dispute analyst handoff, send document reply.\n"
                    "Also provide short reason (<=140 chars).\n"
                    "Case title: {case_title}\n"
                    "Case summary: {case_summary}\n"
                    "Case priority: {case_priority}\n"
                    "Invoice match summary: {invoice_match_summary}\n"
                    "Category: {category}"
                ),
            ),
        ]
    )
