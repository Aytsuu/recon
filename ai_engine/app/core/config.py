from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEFAULT_CORS_ORIGINS = (
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AI_ENGINE_",
        extra="ignore",
    )

    env: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )

    assemblyai_api_key: str | None = None

    supabase_url: str | None = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(
        default=None,
        validation_alias="SUPABASE_SERVICE_ROLE_KEY",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return list(DEFAULT_CORS_ORIGINS)
        if isinstance(value, str):
            parsed = [origin.strip() for origin in value.split(",") if origin.strip()]
            return parsed or list(DEFAULT_CORS_ORIGINS)
        return value

    @model_validator(mode="after")
    def merge_dev_cors_origins(self) -> Self:
        if self.env != "development":
            return self
        self.cors_origins = list(dict.fromkeys([*self.cors_origins, *DEFAULT_CORS_ORIGINS]))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
