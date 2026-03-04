from app.services.analysis.models import LLMUnavailableError


def build_chat_model(
    provider: str,
    model: str,
    temperature: float,
    ollama_base_url: str,
    api_keys: dict[str, str | None],
):
    normalized = provider.lower()
    if normalized == "groq":
        from langchain_groq import ChatGroq

        api_key = api_keys.get("groq")
        if not api_key:
            raise LLMUnavailableError("Missing GROQ_API_KEY.")
        return ChatGroq(model=model, temperature=temperature, api_key=api_key)
    if normalized == "openai":
        from langchain_openai import ChatOpenAI

        api_key = api_keys.get("openai")
        if not api_key:
            raise LLMUnavailableError("Missing OPENAI_API_KEY.")
        return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
    if normalized == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = api_keys.get("anthropic")
        if not api_key:
            raise LLMUnavailableError("Missing ANTHROPIC_API_KEY.")
        return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
    if normalized == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = api_keys.get("google")
        if not api_key:
            raise LLMUnavailableError("Missing GOOGLE_API_KEY.")
        return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=api_key)
    if normalized == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, temperature=temperature, base_url=ollama_base_url)
    raise LLMUnavailableError(f"Unsupported LLM_PROVIDER '{provider}'.")
