"""Company / Department / Role repositories."""
from __future__ import annotations

from app.models.company import Company, Department, Role
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company


class DepartmentRepository(BaseRepository[Department]):
    model = Department

    def list_for_company(self, company_id: str) -> list[Department]:
        return self.list(company_id=company_id, limit=500)


class RoleRepository(BaseRepository[Role]):
    model = Role

    def list_for_department(self, department_id: str) -> list[Role]:
        return self.list(department_id=department_id, limit=500)
