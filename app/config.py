"""Central configuration helpers for the Finance Planner app."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    import streamlit as st  # type: ignore
    _secrets = st.secrets
except Exception:  # pragma: no cover - streamlit not available during tests
    _secrets = {}

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
ENV_FILE = APP_DIR / '.env'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


def _get_secret(name: str, env_name: str | None = None, default: str | None = None) -> str | None:
    """Retrieve configuration from Streamlit secrets or environment variables."""
    if name in _secrets:
        return _secrets.get(name)
    value = os.getenv(env_name or name.upper())
    return value if value not in (None, '') else default


@dataclass(frozen=True)
class Settings:
    """Application level configuration values."""

    openai_api_key: str | None
    openai_model: str
    serpapi_api_key: str | None
    google_api_key: str | None
    google_cse_id: str | None
    email_host: str | None
    email_port: int
    email_user: str | None
    email_password: str | None
    email_from: str | None

    @property
    def are_llm_keys_configured(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != 'OPENAI_API_KEY_PLACEHOLDER')

    @property
    def is_search_configured(self) -> bool:
        return bool(self.serpapi_api_key and self.serpapi_api_key != 'SERPAPI_API_KEY_PLACEHOLDER')


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings(
        openai_api_key=_get_secret('openai_api_key', 'OPENAI_API_KEY', 'OPENAI_API_KEY_PLACEHOLDER'),
        openai_model=_get_secret('openai_model', 'OPENAI_MODEL', 'gpt-4o-mini') or 'gpt-4o-mini',
        serpapi_api_key=_get_secret('serpapi_api_key', 'SERPAPI_API_KEY', 'SERPAPI_API_KEY_PLACEHOLDER'),
        google_api_key=_get_secret('google_api_key', 'GOOGLE_API_KEY'),
        google_cse_id=_get_secret('google_cse_id', 'GOOGLE_CSE_ID'),
        email_host=_get_secret('email_host', 'EMAIL_HOST'),
        email_port=int(_get_secret('email_port', 'EMAIL_PORT', '587') or 587),
        email_user=_get_secret('email_user', 'EMAIL_USER'),
        email_password=_get_secret('email_password', 'EMAIL_PASSWORD'),
        email_from=_get_secret('email_from', 'EMAIL_FROM'),
    )


def get_path(*parts: str) -> Path:
    """Helper to resolve a path inside the app directory."""
    return APP_DIR.joinpath(*parts)
