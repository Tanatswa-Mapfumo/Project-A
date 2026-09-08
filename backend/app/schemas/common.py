"""Shared schema primitives: error envelope and pagination."""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int


class HealthOut(BaseModel):
    status: str
    service: str
    version: str


class VersionOut(BaseModel):
    version: str
    generator_version: str
    env: str
