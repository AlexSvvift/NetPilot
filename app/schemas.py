from datetime import datetime
from enum import Enum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class TargetKind(str, Enum):
    HTTP = "http"
    TCP = "tcp"
    UDP = "udp"


class TargetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    kind: TargetKind
    url: AnyHttpUrl | None = None
    host: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    enabled: bool = True
    interval_seconds: int = Field(default=60, ge=10, le=86400)
    timeout_seconds: float = Field(default=5.0, gt=0, le=60)

    @model_validator(mode="after")
    def validate_connection_fields(self) -> "TargetCreate":
        if self.kind == TargetKind.HTTP and self.url is None:
            raise ValueError("Для HTTP-проверки нужно указать url")
        if self.kind in {TargetKind.TCP, TargetKind.UDP} and (not self.host or self.port is None):
            raise ValueError("Для TCP/UDP-проверки нужны host и port")
        return self


class TargetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=10, le=86400)
    timeout_seconds: float | None = Field(default=None, gt=0, le=60)


class CheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_id: int
    status: bool
    latency_ms: float | None
    status_code: int | None
    error: str | None
    checked_at: datetime


class TargetResponse(BaseModel):
    id: int
    name: str
    kind: TargetKind
    url: str | None
    host: str | None
    port: int | None
    enabled: bool
    interval_seconds: int
    timeout_seconds: float
    created_at: datetime
    updated_at: datetime
    last_check: CheckResponse | None = None


class DashboardResponse(BaseModel):
    total: int
    enabled: int
    up: int
    down: int
    never_checked: int


class HealthResponse(BaseModel):
    status: str
    service: str
    monitoring_enabled: bool

