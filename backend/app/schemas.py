"""Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationBase(BaseModel):
    """Fields shared across create/update/read."""

    company: str
    position: str
    status: str = "applied"
    url: str | None = None
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    """Payload for creating an application."""


class ApplicationUpdate(BaseModel):
    """Payload for partially updating an application."""

    company: str | None = None
    position: str | None = None
    status: str | None = None
    url: str | None = None
    notes: str | None = None


class Application(ApplicationBase):
    """Application as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class User(BaseModel):
    """A logged-in user as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    picture: str | None = None
