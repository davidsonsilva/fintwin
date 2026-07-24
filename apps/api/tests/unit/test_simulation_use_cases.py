from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.application.use_cases.simulation_use_cases import SimulateDecisionUseCase
from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.decisions.validation import InvalidDecisionParametersError
from src.domain.shared.enums import LiquidityType
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository
from src.infrastructure.repositories.simulation_repository import SqlAlchemySimulationRepository


def _make_use_case(session: Session) -> SimulateDecisionUseCase:
    return SimulateDecisionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        simulation_repo=SqlAlchemySimulationRepository(session),
    )


def test_simulate_persists_scenario_override_with_simulation(session: Session) -> None:
    profile = CreateProfileUseCase(SqlAlchemyProfileRepository(session)).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Reserva",
        balance=Money(Decimal("5000.00"), "BRL"),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )

    simulation = _make_use_case(session).execute(
        profile_id=profile.id,
        decision_type="CASH_PURCHASE",
        parameters={"description": "Notebook", "amount": "1000.00"},
        scenario_override=ScenarioOverride(income_multiplier=Decimal("0.80")),
        horizon_months=3,
        currency="BRL",
    )

    assert "scenario_override" in simulation.parameters
    assert simulation.parameters["scenario_override"]["income_multiplier"] == "0.80"

    persisted = SqlAlchemySimulationRepository(session).get(simulation.id)
    assert persisted is not None
    assert persisted.parameters["scenario_override"]["income_multiplier"] == "0.80"


def test_simulate_rejects_invalid_parameters_before_touching_repos(session: Session) -> None:
    profile = CreateProfileUseCase(SqlAlchemyProfileRepository(session)).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )

    with pytest.raises(InvalidDecisionParametersError):
        _make_use_case(session).execute(
            profile_id=profile.id,
            decision_type="CASH_PURCHASE",
            parameters={"description": "Notebook", "amount": "-500.00"},
            scenario_override=None,
            horizon_months=3,
            currency="BRL",
        )
