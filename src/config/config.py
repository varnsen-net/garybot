""""""
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

    irc_nick: str = Field()
    irc_server: str = Field()
    irc_port: str = Field()
    irc_main_channel: str = Field()
    irc_llm_model: str = Field()
    irc_ignore_list: str = Field()
    irc_admin_nick: str = Field()
    wolfram_api_key: SecretStr = Field()
    odds_api_key: SecretStr = Field()
    llm_api_key: SecretStr = Field()
    nasa_api_key: SecretStr = Field()
    youtube_api_key: SecretStr = Field()

    project_root: Path = Field(default=PROJ_ROOT.resolve())
    user_logs_path: Path = Field(default=PROJ_ROOT.resolve() / "data" / "user_logs" / "user_logs.db")

    @field_validator("irc_port")
    @classmethod
    def valid_port(cls, v: str) -> int:
        try:
            v = int(v)
        except ValueError:
            raise ValueError(f"Port must be an integer: {v}")
        if not (1 <= v <= 65535):
            raise ValueError(f"Invalid port: {v}")
        return v


@lru_cache
def get_config() -> AppSettings:
    """
    @lru_cache means this runs once — the same object is returned on
    every subsequent call, so your whole app shares one config instance.

    Usage:
        from config import get_settings
        settings = get_settings()
        print(settings.irc_host)
    """
    return AppSettings()
