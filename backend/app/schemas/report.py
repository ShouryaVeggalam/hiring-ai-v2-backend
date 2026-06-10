"""Report schemas."""
from __future__ import annotations

from pydantic import BaseModel

from app.core.constants import ReportType
from app.schemas.common import TimestampedSchema


class ReportRead(TimestampedSchema):
    report_type: ReportType
    title: str
    summary: str | None = None
    content: dict | None = None
    period_start: str | None = None
    period_end: str | None = None
    generated_by: str | None = None
    company_id: str | None = None


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    company_id: str | None = None
    period_start: str | None = None
    period_end: str | None = None
