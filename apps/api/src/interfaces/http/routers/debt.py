from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.crud_use_cases import DeleteUseCase, GetUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.debt_use_cases import CreateDebtUseCase
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.interfaces.http.schemas.debt import DebtCreateRequest, DebtResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["debts"])
debts_router = APIRouter(prefix="/api/v1/debts", tags=["debts"])


@profiles_router.post("/{profile_id}/debts", response_model=DebtResponse, status_code=201)
def create_debt(
    profile_id: str, payload: DebtCreateRequest, session: Session = Depends(get_session)
) -> DebtResponse:
    repo = SqlAlchemyDebtRepository(session)
    debt = CreateDebtUseCase(repo).execute(
        profile_id=profile_id,
        description=payload.description,
        outstanding_balance=payload.outstanding_balance.to_domain(),
        installment_amount=payload.installment_amount.to_domain(),
        remaining_installments=payload.remaining_installments,
        interest_rate_optional=payload.interest_rate_optional,
        due_day=payload.due_day,
    )
    return DebtResponse.from_domain(debt)


@profiles_router.get("/{profile_id}/debts", response_model=list[DebtResponse])
def list_debts(profile_id: str, session: Session = Depends(get_session)) -> list[DebtResponse]:
    repo = SqlAlchemyDebtRepository(session)
    debts = ListByProfileUseCase(repo).execute(profile_id)
    return [DebtResponse.from_domain(debt) for debt in debts]


@debts_router.put("/{debt_id}", response_model=DebtResponse)
def update_debt(debt_id: str, payload: DebtCreateRequest, session: Session = Depends(get_session)) -> DebtResponse:
    repo = SqlAlchemyDebtRepository(session)
    debt = GetUseCase(repo).execute(debt_id)
    if debt is None:
        raise HTTPException(status_code=404, detail="Dívida não encontrada.")
    debt.description = payload.description
    debt.outstanding_balance = payload.outstanding_balance.to_domain()
    debt.installment_amount = payload.installment_amount.to_domain()
    debt.remaining_installments = payload.remaining_installments
    debt.interest_rate_optional = payload.interest_rate_optional
    debt.due_day = payload.due_day
    UpdateUseCase(repo).execute(debt)
    return DebtResponse.from_domain(debt)


@debts_router.delete("/{debt_id}", status_code=204)
def delete_debt(debt_id: str, session: Session = Depends(get_session)) -> None:
    repo = SqlAlchemyDebtRepository(session)
    DeleteUseCase(repo).execute(debt_id)
