"""Report repository."""
from __future__ import annotations

from app.models.report import HiringReport
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[HiringReport]):
    model = HiringReport
