from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Auth
    trusted_forwarded_hosts: frozenset[str] = frozenset({"localhost"})
    secret_token: str

    @field_validator("trusted_forwarded_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, v: object) -> object:
        if isinstance(v, str):
            return frozenset(h.strip() for h in v.split(",") if h.strip())
        return v


settings = Settings()
