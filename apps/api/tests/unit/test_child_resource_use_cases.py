from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.crud_use_cases import DeleteUseCase, ListByProfileUseCase, UpdateUseCase
from src.application.use_cases.debt_use_cases import CreateDebtUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def _create_profile(session: Session) -> str:
    repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    return profile.id


def test_account_crud(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyAccountRepository(session)
    account = CreateAccountUseCase(repo).execute(
        profile_id=profile_id,
        description="Conta corrente",
        balance=Money(Decimal("1000.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=False,
    )

    listed = ListByProfileUseCase(repo).execute(profile_id)
    assert len(listed) == 1
    assert listed[0].id == account.id

    account.description = "Conta corrente atualizada"
    UpdateUseCase(repo).execute(account)
    listed_after_update = ListByProfileUseCase(repo).execute(profile_id)
    assert listed_after_update[0].description == "Conta corrente atualizada"

    DeleteUseCase(repo).execute(account.id)
    assert ListByProfileUseCase(repo).execute(profile_id) == []


def test_income_source_creation(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyIncomeSourceRepository(session)
    income = CreateIncomeSourceUseCase(repo).execute(
        profile_id=profile_id,
        description="Salário",
        amount=Money(Decimal("5000.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )
    assert income.id is not None
    assert ListByProfileUseCase(repo).execute(profile_id)[0].description == "Salário"


def test_obligation_creation(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyObligationRepository(session)
    obligation = CreateObligationUseCase(repo).execute(
        profile_id=profile_id,
        description="Aluguel",
        amount=Money(Decimal("2000.00"), "BRL"),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=True,
        debt_related=False,
    )
    assert obligation.due_day == 5


def test_debt_creation(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyDebtRepository(session)
    debt = CreateDebtUseCase(repo).execute(
        profile_id=profile_id,
        description="Financiamento",
        outstanding_balance=Money(Decimal("30000.00"), "BRL"),
        installment_amount=Money(Decimal("1400.00"), "BRL"),
        remaining_installments=20,
        interest_rate_optional="1.5% a.m.",
        due_day=10,
    )
    assert debt.remaining_installments == 20


def test_goal_creation(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyGoalRepository(session)
    goal = CreateGoalUseCase(repo).execute(
        profile_id=profile_id,
        description="Imóvel próprio",
        target_amount=Money(Decimal("60000.00"), "BRL"),
        current_amount=Money(Decimal("9000.00"), "BRL"),
        deadline=date(2027, 12, 31),
        priority=1,
        monthly_contribution=Money(Decimal("800.00"), "BRL"),
    )
    assert goal.priority == 1


def test_event_creation(session: Session) -> None:
    profile_id = _create_profile(session)
    repo = SqlAlchemyEventRepository(session)
    event = CreateEventUseCase(repo).execute(
        profile_id=profile_id,
        description="IPTU",
        event_type="tax",
        amount=Money(Decimal("2400.00"), "BRL"),
        event_date=date(2026, 2, 10),
        recurrence=None,
        direction=Direction.EXPENSE,
    )
    assert event.direction == Direction.EXPENSE
