"""
app/core/config.py
──────────────────
Configurações centrais da aplicação via Pydantic BaseSettings.
Lê variáveis de ambiente do arquivo .env automaticamente.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Aplicação ──────────────────────────────────────────────
    APP_NAME: str = "Wattiz"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_VERSION: str = "1.0.0"

    # ── Servidor ──────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Banco de Dados ────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── IA Lume / Ollama ──────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_API_KEY: str = ""          # Chave para Ollama cloud (vazio = local)
    LUME_TEMPERATURE: float = 0.4
    LUME_MAX_TOKENS: int = 1024

    # ── Tarifa padrão ─────────────────────────────────────────
    DEFAULT_TARIFF: float = 0.75  # R$/kWh

    # ── CORS ──────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Singleton de configurações — carregado uma vez via cache."""
    return Settings()


settings = get_settings()
