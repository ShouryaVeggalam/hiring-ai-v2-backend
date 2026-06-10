"""Company, Department, and Role endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_manager
from app.core.exceptions import NotFoundError
from app.repositories.company import (
    CompanyRepository,
    DepartmentRepository,
    RoleRepository,
)
from app.schemas.company import (
    CompanyCreate,
    CompanyRead,
    CompanyUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    RoleCreate,
    RoleRead,
)

router = APIRouter(prefix="/companies", tags=["companies"])


# ---- Companies ----
@router.get("", response_model=list[CompanyRead])
def list_companies(db: DbSession) -> list[CompanyRead]:
    return [CompanyRead.model_validate(c) for c in CompanyRepository(db).list(limit=500)]


@router.post("", response_model=CompanyRead, status_code=201, dependencies=[Depends(require_manager)])
def create_company(payload: CompanyCreate, db: DbSession) -> CompanyRead:
    company = CompanyRepository(db).create(payload.model_dump())
    db.commit()
    return CompanyRead.model_validate(company)


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: str, db: DbSession) -> CompanyRead:
    company = CompanyRepository(db).get(company_id)
    if not company:
        raise NotFoundError("Company not found")
    return CompanyRead.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyRead, dependencies=[Depends(require_manager)])
def update_company(company_id: str, payload: CompanyUpdate, db: DbSession) -> CompanyRead:
    repo = CompanyRepository(db)
    company = repo.get(company_id)
    if not company:
        raise NotFoundError("Company not found")
    company = repo.update(company, payload.model_dump(exclude_unset=True))
    db.commit()
    return CompanyRead.model_validate(company)


# ---- Departments ----
@router.get("/{company_id}/departments", response_model=list[DepartmentRead])
def list_departments(company_id: str, db: DbSession) -> list[DepartmentRead]:
    items = DepartmentRepository(db).list_for_company(company_id)
    return [DepartmentRead.model_validate(d) for d in items]


@router.post(
    "/departments", response_model=DepartmentRead, status_code=201,
    dependencies=[Depends(require_manager)],
)
def create_department(payload: DepartmentCreate, db: DbSession) -> DepartmentRead:
    dept = DepartmentRepository(db).create(payload.model_dump())
    db.commit()
    return DepartmentRead.model_validate(dept)


@router.patch(
    "/departments/{department_id}", response_model=DepartmentRead,
    dependencies=[Depends(require_manager)],
)
def update_department(
    department_id: str, payload: DepartmentUpdate, db: DbSession
) -> DepartmentRead:
    repo = DepartmentRepository(db)
    dept = repo.get(department_id)
    if not dept:
        raise NotFoundError("Department not found")
    dept = repo.update(dept, payload.model_dump(exclude_unset=True))
    db.commit()
    return DepartmentRead.model_validate(dept)


# ---- Roles ----
@router.get("/departments/{department_id}/roles", response_model=list[RoleRead])
def list_roles(department_id: str, db: DbSession) -> list[RoleRead]:
    items = RoleRepository(db).list_for_department(department_id)
    return [RoleRead.model_validate(r) for r in items]


@router.post(
    "/roles", response_model=RoleRead, status_code=201, dependencies=[Depends(require_manager)]
)
def create_role(payload: RoleCreate, db: DbSession) -> RoleRead:
    role = RoleRepository(db).create(payload.model_dump())
    db.commit()
    return RoleRead.model_validate(role)
