"""FastAPI dependency injection."""

from app.config import get_settings
from app.integrations.connectors.base import StoreConnector
from app.integrations.connectors.mock import MockConnector
from app.integrations.db.firestore import get_firestore_client

_connector_cache: dict[str, StoreConnector] = {}


def get_connector() -> StoreConnector:
    settings = get_settings()
    connector_type = settings.default_connector

    if connector_type not in _connector_cache:
        if connector_type == "mock":
            _connector_cache[connector_type] = MockConnector()
        else:
            raise ValueError(f"Unknown connector type: {connector_type}")

    return _connector_cache[connector_type]


def get_firestore():
    return get_firestore_client()


def get_llm():
    """Provide a ChatGoogleGenerativeAI instance for dependency injection.

    Lazy-imported so endpoints that don't need the LLM (i.e. the default
    pipeline) never pay the import cost or require a GEMINI_API_KEY.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI

    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.gemini_api_key,
        temperature=settings.gemini_temperature,
    )
