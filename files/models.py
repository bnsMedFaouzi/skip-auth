from enum import StrEnum
from pydantic import BaseModel


class AuthMethod(StrEnum):
    BEARER = "bearer"
    TRUSTED_HOST = "trusted_host"


class AuthContext(BaseModel):
    model_config = {"frozen": True}  # immutable

    user: str
    method: AuthMethod
    forwarded_host: str | None = None

    @property
    def is_internal(self) -> bool:
        return self.method == AuthMethod.TRUSTED_HOST
