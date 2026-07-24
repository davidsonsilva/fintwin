from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.use_cases.preventive_plan_use_cases import (
    GeneratePreventivePlansUseCase,
    ListPreventivePlansUseCase,
    PreventivePlanNotFoundError,
    UpdatePlanStatusUseCase,
)
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.domain.preventive_plans.validation import InvalidPlanStatusTransitionError
from src.domain.shared.enums import PlanStatus
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.fragility_repository import SqlAlchemyFragilityRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.preventive_plan_repository import SqlAlchemyPreventivePlanRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.preventive_plan import PlanStatusUpdateRequest, PreventivePlanResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["preventive-plans"])
plans_router = APIRouter(prefix="/api/v1/plans", tags=["preventive-plans"])


def _get_profile_or_404(profile_id: str, session: Session):
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


@profiles_router.post("/{profile_id}/plans/generate", response_model=list[PreventivePlanResponse], status_code=201)
def generate_plans(profile_id: str, session: Session = Depends(get_session)) -> list[PreventivePlanResponse]:
    profile = _get_profile_or_404(profile_id, session)

    use_case = GeneratePreventivePlansUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        fragility_repo=SqlAlchemyFragilityRepository(session),
        plan_repo=SqlAlchemyPreventivePlanRepository(session),
    )
    plans = use_case.execute(profile_id, profile.currency)
    return [PreventivePlanResponse.from_domain(plan) for plan in plans]


@profiles_router.get("/{profile_id}/plans", response_model=list[PreventivePlanResponse])
def list_plans(
    profile_id: str,
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> list[PreventivePlanResponse]:
    _get_profile_or_404(profile_id, session)

    try:
        status_enum = PlanStatus(status) if status is not None else None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Status inválido: {status!r}") from exc

    plans = ListPreventivePlansUseCase(SqlAlchemyPreventivePlanRepository(session)).execute(
        profile_id, status=status_enum
    )
    return [PreventivePlanResponse.from_domain(plan) for plan in plans]


@plans_router.patch("/{plan_id}/status", response_model=PreventivePlanResponse)
def update_plan_status(
    plan_id: str, payload: PlanStatusUpdateRequest, session: Session = Depends(get_session)
) -> PreventivePlanResponse:
    use_case = UpdatePlanStatusUseCase(SqlAlchemyPreventivePlanRepository(session))
    try:
        plan = use_case.execute(plan_id, PlanStatus(payload.status))
    except PreventivePlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPlanStatusTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PreventivePlanResponse.from_domain(plan)
