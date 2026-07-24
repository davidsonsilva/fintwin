from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.application.use_cases.fragility_use_cases import DetectFragilitiesUseCase, ListFragilitiesUseCase
from src.domain.shared.enums import IncomeStability, LiquidityType, Recurrence, Severity
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.debt_repository import SqlAlchemyDebtRepository
from src.infrastructure.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.repositories.fragility_repository import SqlAlchemyFragilityRepository
from src.infrastructure.repositories.goal_repository import SqlAlchemyGoalRepository
from src.infrastructure.repositories.income_repository import SqlAlchemyIncomeSourceRepository
from src.infrastructure.repositories.obligation_repository import SqlAlchemyObligationRepository
from src.infrastructure.repositories.profile_repository import SqlAlchemyProfileRepository


def _make_detect_use_case(session: Session) -> DetectFragilitiesUseCase:
    return DetectFragilitiesUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        debt_repo=SqlAlchemyDebtRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        fragility_repo=SqlAlchemyFragilityRepository(session),
    )


def test_detect_persists_findings_and_rerun_replaces_snapshot(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Reserva",
        balance=Money(Decimal("1000.00"), "BRL"),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )
    CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)).execute(
        profile_id=profile.id,
        description="Salário único",
        amount=Money(Decimal("4000.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
        profile_id=profile.id,
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

    use_case = _make_detect_use_case(session)
    first_run = use_case.execute(profile.id, "BRL", None)
    assert len(first_run) > 0
    assert any(f.code == "RESERVE_BELOW_THREE_MONTHS" for f in first_run)

    second_run = use_case.execute(profile.id, "BRL", None)
    fragility_repo = SqlAlchemyFragilityRepository(session)
    persisted = fragility_repo.list_by_profile(profile.id)
    assert len(persisted) == len(second_run)


def test_list_fragilities_filters_by_severity(session: Session) -> None:
    profile_repo = SqlAlchemyProfileRepository(session)
    profile = CreateProfileUseCase(profile_repo).execute(
        currency="BRL", dependents=0, monthly_expense_reduction_capacity=None
    )
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile.id,
        description="Reserva",
        balance=Money(Decimal("500.00"), "BRL"),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )
    CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)).execute(
        profile_id=profile.id,
        description="Salário",
        amount=Money(Decimal("500.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
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

    _make_detect_use_case(session).execute(profile.id, "BRL", None)

    list_use_case = ListFragilitiesUseCase(SqlAlchemyFragilityRepository(session))
    all_findings = list_use_case.execute(profile.id)
    critical_only = list_use_case.execute(profile.id, severity=Severity.CRITICAL)

    assert len(critical_only) <= len(all_findings)
    assert all(f.severity == Severity.CRITICAL for f in critical_only)
