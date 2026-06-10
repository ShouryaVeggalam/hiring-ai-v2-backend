"""Offer Agent endpoints (/offer)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession, require_manager
from app.schemas.agent import AgentRunResult
from app.schemas.common import Page
from app.schemas.offer import OfferGenerateRequest, OfferRead, OfferUpdate
from app.services.offer_service import OfferService

router = APIRouter(prefix="/offer", tags=["offer"])


@router.get("", response_model=Page[OfferRead])
def list_offers(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page[OfferRead]:
    items, total = OfferService(db).list(offset=(page - 1) * page_size, limit=page_size)
    return Page[OfferRead](
        items=[OfferRead.model_validate(o) for o in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{offer_id}", response_model=OfferRead)
def get_offer(offer_id: str, db: DbSession) -> OfferRead:
    return OfferRead.model_validate(OfferService(db).get(offer_id))


@router.post("/generate", response_model=AgentRunResult, dependencies=[Depends(require_manager)])
def generate_offer(
    payload: OfferGenerateRequest, db: DbSession, user: CurrentUser
) -> AgentRunResult:
    return OfferService(db).generate(payload, company_id=user.company_id, actor_id=user.id)


@router.patch("/{offer_id}", response_model=OfferRead, dependencies=[Depends(require_manager)])
def update_offer(offer_id: str, payload: OfferUpdate, db: DbSession) -> OfferRead:
    return OfferRead.model_validate(OfferService(db).update_status(offer_id, payload))
