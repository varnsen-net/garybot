"""Configuration management using pydantic-settings."""
from pathlib import Path
from functools import lru_cache
from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJ_ROOT = Path(__file__).parent.parent.parent


class AppSettings(BaseSettings):
    """Base config — values shared across all environments.

    pydantic-settings automatically reads from:
      1. Environment variables (highest priority)
      2. The .env file specified in model_config
      3. Field defaults (lowest priority)

    Field names map to env vars by uppercasing: `irc_host` -> IRC_HOST
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    irc_nick: str = Field(description="IRC bot nickname")
    irc_server: str = Field(description="IRC server address")
    irc_port: int = Field(ge=1, le=65535, description="IRC server port")
    irc_main_channel: str = Field(description="IRC channel to join on startup")
    irc_llm_model: str = Field(description="LLM model to use for IRC interactions")
    irc_ignore_list: str = Field(default='', description="List of IRC nicknames to ignore")

    wolfram_api_key: SecretStr = Field(description="API key for Wolfram Alpha")
    odds_api_key: SecretStr = Field(description="API key for The Odds API")
    llm_api_key: SecretStr = Field(description="API key for the LLM provider")
    nasa_api_key: SecretStr = Field(description="API key for NASA APIs")
    youtube_api_key: SecretStr = Field(description="API key for YouTube Data API")

    project_root: Path = Field(default=PROJ_ROOT.resolve())
    user_logs_path: Path = Field(default=PROJ_ROOT.resolve() / "data" / "user_logs" / "user_logs.db")

    @field_validator("irc_ignore_list", mode="after")
    @classmethod
    def append_to_ignore_list(cls, value: str) -> str:
        """Append default ignored nicks to the ignore list."""
        defaults = "NickServ,ChanServ"
        if value:
            return f"{defaults},{value}"
        return defaults


@lru_cache
def get_config() -> AppSettings:
    """
    @lru_cache means this runs once — the same object is returned on
    every subsequent call, so your whole app shares one config instance.

    Usage:
        from config import get_config
        settings = get_config()
        print(settings.irc_host)
    """
    return AppSettings()
