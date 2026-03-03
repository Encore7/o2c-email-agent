from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.repositories.classified_email_repository import ClassifiedEmailRepository
from app.repositories.outbound_email_repository import OutboundEmailRepository
from app.repositories.source_email_repository import SourceEmailRepository
from app.services.analysis import HybridEmailAnalyzer, LangChainLLMService, LLMUnavailableError
from app.services.email_processing import EmailProcessingService
from app.services.gmail import GmailClient
from app.services.reply_actions import ReplyActionsService


def get_settings_dep() -> Settings:
    return get_settings()


@lru_cache
def _llm_service_cached(
    provider: str,
    model: str,
    temperature: float,
    ollama_base_url: str,
    groq_api_key: str | None,
    openai_api_key: str | None,
    anthropic_api_key: str | None,
    google_api_key: str | None,
) -> LangChainLLMService | None:
    if not provider:
        return None
    try:
        return LangChainLLMService(
            provider=provider,
            model=model,
            temperature=temperature,
            ollama_base_url=ollama_base_url,
            api_keys={
                "groq": groq_api_key,
                "openai": openai_api_key,
                "anthropic": anthropic_api_key,
                "google": google_api_key,
            },
        )
    except LLMUnavailableError:
        return None


def _llm_service(settings: Settings) -> LangChainLLMService | None:
    if not settings.llm_enabled:
        return None
    return _llm_service_cached(
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        ollama_base_url=settings.ollama_base_url,
        groq_api_key=settings.groq_api_key,
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        google_api_key=settings.google_api_key,
    )


def _llm_fallback_service(settings: Settings) -> LangChainLLMService | None:
    if not settings.llm_enabled or not settings.llm_fallback_provider or not settings.llm_fallback_model:
        return None
    return _llm_service_cached(
        provider=settings.llm_fallback_provider,
        model=settings.llm_fallback_model,
        temperature=settings.llm_temperature,
        ollama_base_url=settings.ollama_base_url,
        groq_api_key=settings.groq_api_key,
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
        google_api_key=settings.google_api_key,
    )


def get_db_session(settings: Settings = Depends(get_settings_dep)):
    session_factory = get_session_factory(settings.postgres_dsn)
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_source_email_repository(session: Session = Depends(get_db_session)) -> SourceEmailRepository:
    return SourceEmailRepository(session=session)


def get_classified_email_repository(
    session: Session = Depends(get_db_session),
) -> ClassifiedEmailRepository:
    return ClassifiedEmailRepository(session=session)


def get_outbound_email_repository(
    session: Session = Depends(get_db_session),
) -> OutboundEmailRepository:
    return OutboundEmailRepository(session=session)


def get_email_repository(
    repository: ClassifiedEmailRepository = Depends(get_classified_email_repository),
) -> ClassifiedEmailRepository:
    return repository


def get_email_analyzer(settings: Settings = Depends(get_settings_dep)) -> HybridEmailAnalyzer:
    return HybridEmailAnalyzer(
        primary_llm_service=_llm_service(settings),
        fallback_llm_service=_llm_fallback_service(settings),
    )


def get_processing_service(
    source_repository: SourceEmailRepository = Depends(get_source_email_repository),
    classified_repository: ClassifiedEmailRepository = Depends(get_classified_email_repository),
    analyzer: HybridEmailAnalyzer = Depends(get_email_analyzer),
) -> EmailProcessingService:
    return EmailProcessingService(
        source_repository=source_repository,
        classified_repository=classified_repository,
        analyzer=analyzer,
    )


def get_reply_actions_service(
    source_repository: SourceEmailRepository = Depends(get_source_email_repository),
    classified_repository: ClassifiedEmailRepository = Depends(get_classified_email_repository),
    outbound_repository: OutboundEmailRepository = Depends(get_outbound_email_repository),
    settings: Settings = Depends(get_settings_dep),
) -> ReplyActionsService:
    gmail_client = None
    if (
        settings.gmail_enabled
        and settings.gmail_client_id
        and settings.gmail_client_secret
        and settings.gmail_refresh_token
    ):
        gmail_client = GmailClient(
            client_id=settings.gmail_client_id,
            client_secret=settings.gmail_client_secret,
            refresh_token=settings.gmail_refresh_token,
            user_id=settings.gmail_user_id,
        )
    return ReplyActionsService(
        source_repository=source_repository,
        classified_repository=classified_repository,
        outbound_repository=outbound_repository,
        gmail_client=gmail_client,
    )


def get_ingestion_service(
    processing_service: EmailProcessingService = Depends(get_processing_service),
) -> EmailProcessingService:
    return processing_service
