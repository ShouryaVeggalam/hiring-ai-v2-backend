"""Company / Department / Role schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema


# ---- Company ----
class CompanyBase(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    headquarters: str | None = None
    description: str | None = None
    culture_values: dict = Field(default_factory=dict)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    size: str | None = None
    headquarters: str | None = None
    description: str | None = None
    culture_values: dict | None = None


class CompanyRead(TimestampedSchema, CompanyBase):
    pass


# ---- Department ----
class DepartmentBase(BaseModel):
    name: str
    description: str | None = None
    headcount: int = 0
    target_headcount: int = 0
    company_id: str


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    headcount: int | None = None
    target_headcount: int | None = None


class DepartmentRead(TimestampedSchema):
    name: str
    description: str | None = None
    headcount: int
    target_headcount: int
    capacity_metrics: dict | None = None
    company_id: str


# ---- Role ----
class RoleBase(BaseModel):
    title: str
    level: str | None = None
    description: str | None = None
    salary_band_min: int | None = None
    salary_band_max: int | None = None
    department_id: str


class RoleCreate(RoleBase):
    pass


class RoleRead(TimestampedSchema):
    title: str
    level: str | None = None
    description: str | None = None
    core_competencies: dict | None = None
    salary_band_min: int | None = None
    salary_band_max: int | None = None
    department_id: str
