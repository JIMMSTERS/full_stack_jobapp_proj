"""Pydantic schemas for request/response validation."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ApplicationBase(BaseModel):
    """Fields shared across create/update/read."""

    company: str
    position: str
    status: str = "applied"
    url: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None


class ApplicationCreate(ApplicationBase):
    """Payload for creating an application."""


class ApplicationUpdate(BaseModel):
    """Payload for partially updating an application."""

    company: str | None = None
    position: str | None = None
    status: str | None = None
    url: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None


class Application(ApplicationBase):
    """Application as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str = "manual"
    created_at: datetime
    updated_at: datetime


class ImportSummary(BaseModel):
    """Result of importing applications from Gmail."""

    created: int
    updated: int
    unchanged: int


class StatusEvent(BaseModel):
    """A single entry in an application's activity timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: str | None = None
    to_status: str
    created_at: datetime


class WeeklyPoint(BaseModel):
    """Number of applications created in the week starting ``week`` (ISO date)."""

    week: str
    count: int


class ApplicationStats(BaseModel):
    """Aggregated analytics over a user's applications for the dashboard."""

    total: int
    by_status: dict[str, int]
    active: int
    responded: int
    offers: int
    this_week: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    weekly: list[WeeklyPoint]


class User(BaseModel):
    """A logged-in user as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    picture: str | None = None
