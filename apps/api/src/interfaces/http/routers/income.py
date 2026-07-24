from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.interfaces.http.schemas.income import IncomeCreateRequest, IncomeResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["incomes"])
incomes_router = APIRouter(prefix="/api/v1/incomes", tags=["incomes"])


@profiles_router.post("/{profile_id}/incomes", response_model=IncomeResponse, status_code=201)
def create_income(
    profile_id: str, payload: IncomeCreateRequest, session: Session = Depends(get_session)
) -> IncomeResponse:
    repo = SqlAlchemyIncomeSourceRepository(session)
    income = CreateIncomeSourceUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        amount=payload.amount.to_domain(),
        frequency=payload.frequency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        stability=payload.stability,
    )
    return IncomeResponse.from_domain(income)


@profiles_router.get("/{profile_id}/incomes", response_model=list[IncomeResponse])
def list_incomes(profile_id: str, session: Session = Depends(get_session)) -> list[IncomeResponse]:
    repo = SqlAlchemyIncomeSourceRepository(session)
    incomes = ListByProfileUseCase(repo).execute(profile_id)
    return [IncomeResponse.from_domain(income) for income in incomes]


@incomes_router.put("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: str, payload: IncomeCreateRequest, session: Session = Depends(get_session)
) -> IncomeResponse:
    repo = SqlAlchemyIncomeSourceRepository(session)
    income = GetUseCase(repo).execute(income_id)
    if income is None:
        raise HTTPException(status_code=404, detail="Renda não encontrada.")
    income.description = payload.description
    income.amount = payload.amount.to_domain()
    income.frequency = payload.frequency
    income.start_date = payload.start_date
    income.end_date = payload.end_date
    income.stability = payload.stability
    UpdateUseCase(repo).execute(income)
    return IncomeResponse.from_domain(income)


@incomes_router.delete("/{income_id}", status_code=204)
def delete_income(income_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyIncomeSourceRepository(session)
    DeleteUseCase(repo).execute(income_id)
