from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.application.use_cases.projection_use_cases import GetProjectionUseCase
from src.domain.shared.enums import IncomeStability, LiquidityType, Recurrence, ScenarioType
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def _make_use_case(session: Session) -> GetProjectionUseCase:
    return GetProjectionUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
    )


def test_get_projection_use_case_loads_persisted_entities(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Conta",
        balance=Money(Decimal("2000.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=False,
    )
    CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)).execute(
        profile_id=profile.id,
        description="Salário",
        amount=Money(Decimal("3000.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
        profile_id=profile.id,
        description="Aluguel",
        amount=Money(Decimal("1000.00"), "BRL"),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )

    result = _make_use_case(session).execute(
        profile_id=profile.id, currency="BRL", horizon_months=6, scenario_type=ScenarioType.PROBABLE
    )

    assert len(result.periods) == 6
    assert result.periods[0].income_total == Money(Decimal("3000.00"), "BRL")
    assert result.periods[0].expense_total == Money(Decimal("1000.00"), "BRL")


def test_get_projection_use_case_adverse_scenario(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )

    result = _make_use_case(session).execute(
        profile_id=profile.id, currency="BRL", horizon_months=3, scenario_type=ScenarioType.ADVERSE
    )

    assert result.scenario == ScenarioType.ADVERSE
    assert len(result.periods) == 3
