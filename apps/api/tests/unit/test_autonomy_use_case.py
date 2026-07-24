from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.autonomy_use_cases import GetAutonomyUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.shared.enums import LiquidityType, Recurrence
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def _make_use_case(session: Session) -> GetAutonomyUseCase:
    return GetAutonomyUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
    )


def test_get_autonomy_use_case_loads_persisted_entities(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Reserva",
        balance=Money(Decimal("9000.00"), "BRL"),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
        profile_id=profile.id,
        description="Aluguel",
        amount=Money(Decimal("3000.00"), "BRL"),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )

    result = _make_use_case(session).execute(
        profile_id=profile.id, currency="BRL", expense_reduction_capacity=None
    )

    assert result.eligible_assets == Money(Decimal("9000.00"), "BRL")
    assert result.basic_autonomy_months == Decimal("3")


def test_get_autonomy_use_case_applies_expense_reduction_capacity(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=Percentage(Decimal("0.10"))
    )

    result = _make_use_case(session).execute(
        profile_id=profile.id,
        currency="BRL",
        expense_reduction_capacity=profile.monthly_expense_reduction_capacity,
    )

    assert result.probable_monthly_burn == Money(Decimal("0.00"), "BRL")
