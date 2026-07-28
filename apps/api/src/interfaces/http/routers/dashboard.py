# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.application.use_cases.autonomy_use_cases import GetAutonomyUseCase
from src.application.use_cases.dashboard_use_cases import GetBalanceHistoryUseCase, GetDashboardSummaryUseCase
from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.application.use_cases.projection_use_cases import GetProjectionUseCase
from src.domain.shared.enums import ScenarioType
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.balance_snapshot_repository import SqlAlchemyBalanceSnapshotRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.interfaces.http.schemas.autonomy import AutonomyResponse
from src.interfaces.http.schemas.dashboard import BalanceSnapshotResponse, DashboardSummaryResponse
from src.interfaces.http.schemas.projection import ProjectionRequest, ProjectionResponse

router = APIRouter(prefix="/api/v1/profiles", tags=["dashboard"])


def _get_profile_or_404(profile_id: str, session: Session):
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


@router.get("/{profile_id}/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(profile_id: str, session: Session = Depends(get_session)) -> DashboardSummaryResponse:
    profile = _get_profile_or_404(profile_id, session)

    use_case = GetDashboardSummaryUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        balance_snapshot_repo=SqlAlchemyBalanceSnapshotRepository(session),
    )
    summary = use_case.execute(profile_id, profile.currency)
    return DashboardSummaryResponse.from_domain(summary)


@router.get("/{profile_id}/balance-history", response_model=list[BalanceSnapshotResponse])
def get_balance_history(
    profile_id: str,
    months: int = Query(default=6, ge=1, le=60),
    session: Session = Depends(get_session),
) -> list[BalanceSnapshotResponse]:
    _get_profile_or_404(profile_id, session)

    use_case = GetBalanceHistoryUseCase(balance_snapshot_repo=SqlAlchemyBalanceSnapshotRepository(session))
    snapshots = use_case.execute(profile_id, months)
    return [BalanceSnapshotResponse.from_domain(snapshot) for snapshot in snapshots]


@router.post("/{profile_id}/projections", response_model=ProjectionResponse)
def get_projection(
    profile_id: str, payload: ProjectionRequest, session: Session = Depends(get_session)
) -> ProjectionResponse:
    profile = _get_profile_or_404(profile_id, session)

    use_case = GetProjectionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
    )
    scenario_type = ScenarioType.PROBABLE if payload.scenario == "probable" else ScenarioType.ADVERSE
    result = use_case.execute(profile_id, profile.currency, payload.months, scenario_type)
    return ProjectionResponse.from_domain(result)


@router.post("/{profile_id}/autonomy", response_model=AutonomyResponse)
def get_autonomy(profile_id: str, session: Session = Depends(get_session)) -> AutonomyResponse:
    profile = _get_profile_or_404(profile_id, session)

    use_case = GetAutonomyUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
    )
    result = use_case.execute(profile_id, profile.currency, profile.monthly_expense_reduction_capacity)
    return AutonomyResponse.from_domain(result)
