"""Configuration management using Pydantic Settings.

This module provides a centralized configuration system that loads settings
from environment variables and .env files.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Required settings must be provided via environment variables or .env file.
    Optional settings have sensible defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # YouTube API Configuration
    youtube_api_key: str = Field(..., description="YouTube Data API key")
    youtube_client_secrets_file: Path = Field(
        ..., description="Path to YouTube OAuth client secrets JSON file"
    )
    youtube_credentials_file: Path = Field(
        ..., description="Path to stored YouTube OAuth credentials file"
    )

    # Reddit API Configuration
    reddit_client_id: str = Field(..., description="Reddit API client ID")
    reddit_client_secret: str = Field(..., description="Reddit API client secret")
    reddit_user_agent: str = Field(..., description="Reddit API user agent string")

    # Optional AI/LLM Configuration
    groq_api_key: str | None = Field(
        default=None, description="Groq API key (optional)"
    )
    ollama_host: str = Field(
        default="http://localhost:11434", description="Ollama server host URL"
    )

    # Path Configuration
    data_dir: Path = Field(
        default=Path("./data"), description="Directory for data storage"
    )
    output_dir: Path = Field(
        default=Path("./output"), description="Directory for output files"
    )
    cache_dir: Path = Field(
        default=Path("./cache"), description="Directory for cache storage"
    )

    # Quota Configuration
    daily_upload_limit: int = Field(
        default=5, description="Maximum uploads per day", ge=1
    )
    youtube_quota_per_day: int = Field(
        default=10000, description="YouTube API quota units per day", ge=1
    )

    @field_validator("youtube_client_secrets_file", "youtube_credentials_file")
    @classmethod
    def validate_path_exists(cls, v: Path) -> Path:
        """Validate that file paths exist (only for credential files)."""
        # Convert to Path if string
        if isinstance(v, str):
            v = Path(v)
        # Note: We don't enforce existence at import time to allow for
        # initial setup where files may not exist yet
        return v.expanduser().resolve()

    @field_validator("data_dir", "output_dir", "cache_dir")
    @classmethod
    def validate_directory_paths(cls, v: Path) -> Path:
        """Ensure directory paths are resolved."""
        if isinstance(v, str):
            v = Path(v)
        return v.expanduser().resolve()


# Singleton settings instance
settings = Settings()
