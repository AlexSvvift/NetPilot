from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "NetPilot"
    database_url: str = "sqlite:///./data/netpilot.db"
    api_key: str = ""
    monitoring_enabled: bool = True
    scheduler_tick_seconds: int = Field(default=5, ge=1, le=60)
    log_level: str = "INFO"
    cors_origins: str = "*"

    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

