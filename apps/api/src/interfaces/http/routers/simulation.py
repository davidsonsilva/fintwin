from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.application.use_cases.profile_use_cases import GetProfileUseCase
from src.application.use_cases.simulation_use_cases import (
    DeleteSimulationUseCase,
    GetSimulationUseCase,
    ListSimulationsUseCase,
    SimulateDecisionUseCase,
)
from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.decisions.validation import InvalidDecisionParametersError
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.infrastructure.persistence.session import get_session
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.simulation_repository import SqlAlchemySimulationRepository
from src.interfaces.http.schemas.simulation import ScenarioOverrideSchema, SimulationRequest, SimulationResponse

profiles_router = APIRouter(prefix="/api/v1/profiles", tags=["simulations"])
simulations_router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])


def _get_profile_or_404(profile_id: str, session: Session):
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = GetProfileUseCase(profile_repo).execute(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")
    return profile


def _to_scenario_override(schema: ScenarioOverrideSchema, currency: str) -> ScenarioOverride:
    return ScenarioOverride(
        income_multiplier=Decimal(schema.income_multiplier) if schema.income_multiplier is not None else None,
        essential_expense_multiplier=(
            Decimal(schema.essential_expense_multiplier) if schema.essential_expense_multiplier is not None else None
        ),
        nonessential_expense_multiplier=(
            Decimal(schema.nonessential_expense_multiplier) if schema.nonessential_expense_multiplier is not None else None
        ),
        unexpected_expense=(
            Money(Decimal(schema.unexpected_expense), currency) if schema.unexpected_expense is not None else None
        ),
        expense_reduction_capacity=(
            Percentage(Decimal(schema.expense_reduction_capacity)) if schema.expense_reduction_capacity is not None else None
        ),
    )


@profiles_router.post("/{profile_id}/simulations", response_model=SimulationResponse, status_code=201)
def create_simulation(
    profile_id: str, payload: SimulationRequest, session: Session = Depends(get_session)
) -> SimulationResponse:
    profile = _get_profile_or_404(profile_id, session)

    scenario_override = (
        _to_scenario_override(payload.scenario_override, profile.currency) if payload.scenario_override is not None else None
    )

    use_case = SimulateDecisionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        simulation_repo=SqlAlchemySimulationRepository(session),
    )
    try:
        simulation = use_case.execute(
            profile_id=profile_id,
            decision_type=payload.decision_type,
            parameters=payload.parameters,
            scenario_override=scenario_override,
            horizon_months=payload.horizon_months,
            currency=profile.currency,
        )
    except InvalidDecisionParametersError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SimulationResponse.from_domain(simulation)


@profiles_router.get("/{profile_id}/simulations", response_model=list[SimulationResponse])
def list_simulations(profile_id: str, session: Session = Depends(get_session)) -> list[SimulationResponse]:
    _get_profile_or_404(profile_id, session)
    simulations = ListSimulationsUseCase(SqlAlchemySimulationRepository(session)).execute(profile_id)
    return [SimulationResponse.from_domain(simulation) for simulation in simulations]


@simulations_router.get("/{simulation_id}", response_model=SimulationResponse)
def get_simulation(simulation_id: str, session: Session = Depends(get_session)) -> SimulationResponse:
    simulation = GetSimulationUseCase(SqlAlchemySimulationRepository(session)).execute(simulation_id)
    if simulation is None:
        raise HTTPException(status_code=404, detail="Simulação não encontrada.")
    return SimulationResponse.from_domain(simulation)


@simulations_router.delete("/{simulation_id}", status_code=204)
def delete_simulation(simulation_id: str, session: Session = Depends(get_session)) -> None:
    DeleteSimulationUseCase(SqlAlchemySimulationRepository(session)).execute(simulation_id)
