"""
Centralized application configuration via pydantic-settings.

Values can be overridden through environment variables or a `.env` file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Anthropic ─────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API key")
    MODEL: str = Field(default="claude-sonnet-4-6", description="Claude model id")

    # ── Databases ─────────────────────────────────────────────────────────────
    DATA_DB_PATH: str = Field(
        default=str(_BASE_DIR / "ecommerce.db"),
        description="Primary application data database",
    )
    META_DB_PATH: str = Field(
        default=str(_BASE_DIR / "metadata.db"),
        description="Metadata database for history & saved queries",
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")

    # ── Behavior ──────────────────────────────────────────────────────────────
    MAX_RESULTS_DEFAULT: int = Field(default=100)

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_CAPACITY: int = Field(default=60, description="Tokens per bucket")
    RATE_LIMIT_REFILL_PER_SEC: float = Field(default=1.0)

    # ── Multi-DB registry ────────────────────────────────────────────────────
    @property
    def ALLOWED_DBS(self) -> Dict[str, str]:
        """Mapping of DB short-name -> filesystem path."""
        return {
            "ecommerce": self.DATA_DB_PATH,
        }


settings = Settings()
