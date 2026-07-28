# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.expense_breakdown_use_cases import GetExpenseBreakdownByCategoryUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.dashboard import CategoryBreakdownResponse
from src.interfaces.http.schemas.obligation import ObligationCreateRequest, ObligationResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["obligations"])
obligations_router = APIRouter(prefix="/api/v1/obligations", tags=["obligations"])


@profiles_router.post("/{profile_id}/obligations", response_model=ObligationResponse, status_code=201)
def create_obligation(
    profile_id: str, payload: ObligationCreateRequest, session: Session = Depends(get_session)
) -> ObligationResponse:
    repo = SqlAlchemyObligationRepository(session)
    obligation = CreateObligationUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        amount=payload.amount.to_domain(),
        category=payload.category,
        frequency=payload.frequency,
        due_day=payload.due_day,
        start_date=payload.start_date,
        end_date=payload.end_date,
        essential=payload.essential,
        debt_related=payload.debt_related,
    )
    return ObligationResponse.from_domain(obligation)


@profiles_router.get("/{profile_id}/obligations", response_model=list[ObligationResponse])
def list_obligations(profile_id: str, session: Session = Depends(get_session)) -> list[ObligationResponse]:
    repo = SqlAlchemyObligationRepository(session)
    obligations = ListByProfileUseCase(repo).execute(profile_id)
    return [ObligationResponse.from_domain(obligation) for obligation in obligations]


@profiles_router.get("/{profile_id}/obligations/by-category", response_model=list[CategoryBreakdownResponse])
def get_obligations_by_category(
    profile_id: str, session: Session = Depends(get_session)
) -> list[CategoryBreakdownResponse]:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    obligation_repo = SqlAlchemyObligationRepository(session)
    breakdown = GetExpenseBreakdownByCategoryUseCase(obligation_repo).execute(profile_id, profile.currency)
    return [CategoryBreakdownResponse.from_domain(item) for item in breakdown]


@obligations_router.put("/{obligation_id}", response_model=ObligationResponse)
def update_obligation(
    obligation_id: str, payload: ObligationCreateRequest, session: Session = Depends(get_session)
) -> ObligationResponse:
    repo = SqlAlchemyObligationRepository(session)
    obligation = GetUseCase(repo).execute(obligation_id)
    if obligation is None:
        raise HTTPException(status_code=404, detail="Obrigação não encontrada.")
    obligation.description = payload.description
    obligation.amount = payload.amount.to_domain()
    obligation.category = payload.category
    obligation.frequency = payload.frequency
    obligation.due_day = payload.due_day
    obligation.start_date = payload.start_date
    obligation.end_date = payload.end_date
    obligation.essential = payload.essential
    obligation.debt_related = payload.debt_related
    UpdateUseCase(repo).execute(obligation)
    return ObligationResponse.from_domain(obligation)


@obligations_router.delete("/{obligation_id}", status_code=204)
def delete_obligation(obligation_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyObligationRepository(session)
    DeleteUseCase(repo).execute(obligation_id)
