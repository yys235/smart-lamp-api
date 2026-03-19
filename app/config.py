"""Smart Lamp API Configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # API Security
    api_key: Optional[str] = None

    # UDP Configuration
    udp_port: int = 41328
    udp_buffer_size: int = 2048

    # TCP Configuration
    tcp_port: int = 41330
    tcp_timeout: int = 5
    tcp_connect_timeout: int = 5

    # Gateway
    gateway_discovery_timeout: int = 30

    # Retry
    max_retries: int = 3
    retry_delay: float = 1.0

    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_rotation: str = "10 MB"  # Rotate when log file reaches 10MB
    log_retention: str = "7 days"  # Keep logs for 7 days
    log_compression: str = "zip"  # Compress rotated logs

    # Database
    database_url: str = "sqlite+aiosqlite:///./smartlamp.db"
    database_echo: bool = False

    @property
    def log_path(self) -> Path:
        """Get log directory path."""
        return Path(self.log_dir)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
