from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Auth
    trusted_forwarded_hosts: frozenset[str] = frozenset({"localhost"})
    secret_token: str = ""  # Obligatoire en prod — doit être fourni via .env ou variable d'environnement

    @field_validator("secret_token")
    @classmethod
    def secret_token_must_not_be_empty(cls, v: str) -> str:
        import os
        if not v and os.getenv("ENV", "development") == "production":
            raise ValueError("SECRET_TOKEN must be set in production")
        return v

    @field_validator("trusted_forwarded_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, v: object) -> object:
        if isinstance(v, str):
            return frozenset(h.strip() for h in v.split(",") if h.strip())
        return v


settings = Settings()
