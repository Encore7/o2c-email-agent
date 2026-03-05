from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.email import Category


@dataclass
class AnalysisResult:
    category: Category
    confidence: float
    reason: str
    classification_source: str
    customer_name: str | None
    invoice_references: list[str] | None
    amounts: list[float] | None
    mentioned_dates: list[str] | None
    detail: str | None
    extraction_source: str
    case_title: str
    case_summary: str
    case_priority: str
    invoice_match_summary: str | None
    invoice_matches: list[dict] | None
    next_best_action: str
    next_best_action_reason: str
    reply_draft_subject: str
    reply_draft_body: str


class LLMUnavailableError(RuntimeError):
    """Raised when provider is not configured or LLM output is invalid."""


class ClassificationPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    category: Category
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ExtractionPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    customer_name: str | None = Field(
        default=None,
        description="Customer or account name explicitly stated in email subject/body; null if missing.",
    )
    invoice_references: list[str] | None = Field(
        default=None,
        description="Invoice identifiers explicitly referenced (for example INV-1032); null if none found.",
    )
    amounts: list[str] | None = Field(
        default=None,
        description="Monetary values explicitly referenced as strings; null if none found.",
    )
    mentioned_dates: list[str] | None = Field(
        default=None,
        description="Date expressions explicitly referenced in subject/body; null if none found.",
    )
    detail: str | None = Field(
        default=None,
        description="One-line key business context from the email, max 140 chars; null if not confidently inferred.",
    )


class NextStepPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    next_best_action: str = Field(
        description="One concrete next action for AR team, max 140 chars."
    )
    next_best_action_reason: str = Field(
        description="Short rationale for the next action, max 140 chars."
    )


class CaseDraftPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    case_title: str = Field(description="Short case title for human reviewer, max 100 chars.")
    case_summary: str = Field(
        description="Clear case summary with key context and extracted facts, max 280 chars."
    )
    case_priority: str = Field(
        description="One of: low, medium, high based on urgency and financial impact."
    )
