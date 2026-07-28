from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.application.use_cases.account_use_cases import CreateAccountUseCase
from src.application.use_cases.dashboard_use_cases import GetDashboardSummaryUseCase
from src.application.use_cases.event_use_cases import CreateEventUseCase
from src.application.use_cases.goal_use_cases import CreateGoalUseCase
from src.application.use_cases.income_use_cases import CreateIncomeSourceUseCase
from src.application.use_cases.obligation_use_cases import CreateObligationUseCase
from src.application.use_cases.profile_use_cases import CreateProfileUseCase
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money
from src.infrastructure.repositories.account_repository import SqlAlchemyAccountRepository
from src.infrastructure.repositories.balance_snapshot_repository import SqlAlchemyBalanceSnapshotRepository
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


def _make_use_case(session: Session) -> GetDashboardSummaryUseCase:
    return GetDashboardSummaryUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
    )


def test_summary_with_no_income_has_no_commitment_pct(session: Session) -> None:
    profile_id = _create_profile(session)
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile_id,
        description="Conta",
        balance=Money(Decimal("1000.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=False,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
        profile_id=profile_id,
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

    summary = _make_use_case(session).execute(profile_id, "BRL")

    assert summary.net_balance == Money(Decimal("1000.00"), "BRL")
    assert summary.monthly_obligations_total == Money(Decimal("1000.00"), "BRL")
    assert summary.income_commitment_pct is None
    assert summary.main_goal is None
    assert summary.upcoming_events == []


def test_summary_with_no_goals_returns_none_main_goal(session: Session) -> None:
    profile_id = _create_profile(session)
    summary = _make_use_case(session).execute(profile_id, "BRL")
    assert summary.main_goal is None


def test_summary_computes_income_commitment_and_main_goal(session: Session) -> None:
    profile_id = _create_profile(session)
    CreateIncomeSourceUseCase(SqlAlchemyIncomeSourceRepository(session)).execute(
        profile_id=profile_id,
        description="Salário",
        amount=Money(Decimal("4000.00"), "BRL"),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )
    CreateObligationUseCase(SqlAlchemyObligationRepository(session)).execute(
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
    CreateGoalUseCase(SqlAlchemyGoalRepository(session)).execute(
        profile_id=profile_id,
        description="Reserva",
        target_amount=Money(Decimal("10000.00"), "BRL"),
        current_amount=Money(Decimal("2500.00"), "BRL"),
        deadline=None,
        priority=1,
        monthly_contribution=Money(Decimal("500.00"), "BRL"),
    )
    CreateGoalUseCase(SqlAlchemyGoalRepository(session)).execute(
        profile_id=profile_id,
        description="Meta secundária",
        target_amount=Money(Decimal("5000.00"), "BRL"),
        current_amount=Money(Decimal("1000.00"), "BRL"),
        deadline=None,
        priority=2,
        monthly_contribution=Money(Decimal("200.00"), "BRL"),
    )

    summary = _make_use_case(session).execute(profile_id, "BRL")

    assert summary.income_commitment_pct is not None
    assert summary.income_commitment_pct.as_fraction() == Decimal("0.50")
    assert summary.main_goal is not None
    assert summary.main_goal.description == "Reserva"
    assert summary.main_goal.progress_pct.as_fraction() == Decimal("0.25")


def test_summary_filters_past_events_and_limits_to_five(session: Session) -> None:
    profile_id = _create_profile(session)
    today = date.today()
    event_repo = SqlAlchemyEventRepository(session)
    use_case_events = CreateEventUseCase(event_repo)

    use_case_events.execute(
        profile_id=profile_id,
        description="Evento passado",
        event_type="tax",
        amount=Money(Decimal("100.00"), "BRL"),
        event_date=today - timedelta(days=10),
        recurrence=None,
        direction=Direction.EXPENSE,
    )
    for i in range(6):
        use_case_events.execute(
            profile_id=profile_id,
            description=f"Evento futuro {i}",
            event_type="tax",
            amount=Money(Decimal("100.00"), "BRL"),
            event_date=today + timedelta(days=i + 1),
            recurrence=None,
            direction=Direction.EXPENSE,
        )

    summary = _make_use_case(session).execute(profile_id, "BRL")

    assert len(summary.upcoming_events) == 5
    assert all(event.date >= today for event in summary.upcoming_events)


def test_summary_captures_balance_snapshot_idempotently(session: Session) -> None:
    profile_id = _create_profile(session)
    CreateAccountUseCase(SqlAlchemyAccountRepository(session)).execute(
        profile_id=profile_id,
        description="Conta",
        balance=Money(Decimal("1500.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=False,
    )
    snapshot_repo = SqlAlchemyBalanceSnapshotRepository(session)
    use_case = GetDashboardSummaryUseCase(
        account_repo=SqlAlchemyAccountRepository(session),
        income_repo=SqlAlchemyIncomeSourceRepository(session),
        obligation_repo=SqlAlchemyObligationRepository(session),
        goal_repo=SqlAlchemyGoalRepository(session),
        event_repo=SqlAlchemyEventRepository(session),
        balance_snapshot_repo=snapshot_repo,
    )

    use_case.execute(profile_id, "BRL")
    use_case.execute(profile_id, "BRL")

    period = date.today().strftime("%Y-%m")
    snapshots = snapshot_repo.list_by_profile_ordered(profile_id, 12)
    matching = [snapshot for snapshot in snapshots if snapshot.period == period]
    assert len(matching) == 1
    assert matching[0].net_balance == Money(Decimal("1500.00"), "BRL")
