from datetime import date, timedelta
from decimal import Decimal

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)


def _account(balance: str) -> FinancialAccount:
    return FinancialAccount(
        id="acc-1",
        profile_id="profile-1",
        description="Conta",
        balance=Money(Decimal(balance), CURRENCY),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=False,
    )


def _income(amount: str, frequency: Recurrence = Recurrence.MONTHLY, start: date = date(2024, 1, 1)) -> IncomeSource:
    return IncomeSource(
        id="income-1",
        profile_id="profile-1",
        description="Salário",
        amount=Money(Decimal(amount), CURRENCY),
        frequency=frequency,
        start_date=start,
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def _obligation(
    amount: str,
    essential: bool = True,
    frequency: Recurrence = Recurrence.MONTHLY,
    start: date = date(2024, 1, 1),
) -> FinancialObligation:
    return FinancialObligation(
        id="obl-1",
        profile_id="profile-1",
        description="Aluguel",
        amount=Money(Decimal(amount), CURRENCY),
        category="moradia",
        frequency=frequency,
        due_day=5,
        start_date=start,
        end_date=None,
        essential=essential,
        debt_related=False,
    )


def _debt(installment: str, remaining: int) -> Debt:
    return Debt(
        id="debt-1",
        profile_id="profile-1",
        description="Financiamento",
        outstanding_balance=Money(Decimal("10000.00"), CURRENCY),
        installment_amount=Money(Decimal(installment), CURRENCY),
        remaining_installments=remaining,
        interest_rate_optional=None,
        due_day=10,
    )


def _goal(contribution: str) -> FinancialGoal:
    return FinancialGoal(
        id="goal-1",
        profile_id="profile-1",
        description="Reserva",
        target_amount=Money(Decimal("10000.00"), CURRENCY),
        current_amount=Money(Decimal("1000.00"), CURRENCY),
        deadline=None,
        priority=1,
        monthly_contribution=Money(Decimal(contribution), CURRENCY),
    )


def _event(
    amount: str,
    event_date: date,
    direction: Direction = Direction.EXPENSE,
    recurrence: Recurrence | None = None,
) -> FinancialEvent:
    return FinancialEvent(
        id="event-1",
        profile_id="profile-1",
        description="Evento",
        event_type="tax",
        amount=Money(Decimal(amount), CURRENCY),
        date=event_date,
        recurrence=recurrence,
        direction=direction,
    )


def test_simple_projection_no_deficit() -> None:
    result = project_cashflow(
        accounts=[_account("5000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00")],
        debts=[],
        goals=[],
        events=[],
        horizon_months=3,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    assert len(result.periods) == 3
    first = result.periods[0]
    assert first.period == "2026-07"
    assert first.opening_balance == Money(Decimal("5000.00"), CURRENCY)
    assert first.income_total == Money(Decimal("4000.00"), CURRENCY)
    assert first.expense_total == Money(Decimal("2000.00"), CURRENCY)
    assert first.net_cashflow == Money(Decimal("2000.00"), CURRENCY)
    assert first.closing_balance == Money(Decimal("7000.00"), CURRENCY)
    assert first.income_commitment_percentage.as_fraction() == Decimal("0.50")
    assert first.deficit is False
    assert result.first_deficit_period is None
    assert result.final_balance == Money(Decimal("11000.00"), CURRENCY)


def test_projection_detects_deficit() -> None:
    result = project_cashflow(
        accounts=[_account("1000.00")],
        incomes=[_income("1000.00")],
        obligations=[_obligation("3000.00")],
        debts=[],
        goals=[],
        events=[],
        horizon_months=2,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.first_deficit_period == "2026-07"
    assert result.periods[0].deficit is True
    assert result.lowest_balance.is_negative()


def test_debt_installments_stop_after_remaining_count() -> None:
    result = project_cashflow(
        accounts=[_account("50000.00")],
        incomes=[_income("5000.00")],
        obligations=[],
        debts=[_debt("1000.00", remaining=2)],
        goals=[],
        events=[],
        horizon_months=4,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.periods[0].expense_total == Money(Decimal("1000.00"), CURRENCY)
    assert result.periods[1].expense_total == Money(Decimal("1000.00"), CURRENCY)
    assert result.periods[2].expense_total == Money(Decimal("0.00"), CURRENCY)
    assert result.periods[3].expense_total == Money(Decimal("0.00"), CURRENCY)


def test_yearly_event_occurs_once_within_twelve_month_horizon() -> None:
    result = project_cashflow(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[],
        debts=[],
        goals=[],
        events=[_event("1200.00", date(2026, 2, 10), direction=Direction.EXPENSE, recurrence=Recurrence.YEARLY)],
        horizon_months=12,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    periods_with_event_expense = [p for p in result.periods if p.expense_total.amount > 0]
    assert len(periods_with_event_expense) == 1
    assert periods_with_event_expense[0].period == "2027-02"
    assert len(result.relevant_events) == 1


def test_income_event_not_affected_by_scenario_multiplier() -> None:
    result = project_cashflow(
        accounts=[_account("0.00")],
        incomes=[],
        obligations=[],
        debts=[],
        goals=[],
        events=[_event("1000.00", TODAY, direction=Direction.INCOME)],
        horizon_months=1,
        scenario=ScenarioParameters.adverse(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.periods[0].income_total == Money(Decimal("1000.00"), CURRENCY)


def test_adverse_scenario_reduces_income_and_raises_essential_expenses() -> None:
    common_kwargs = dict(
        accounts=[_account("5000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        debts=[],
        goals=[],
        events=[],
        horizon_months=1,
        currency=CURRENCY,
        today=TODAY,
    )

    probable = project_cashflow(scenario=ScenarioParameters.probable(CURRENCY), **common_kwargs)
    adverse = project_cashflow(scenario=ScenarioParameters.adverse(CURRENCY), **common_kwargs)

    assert adverse.periods[0].income_total == Money(Decimal("3000.00"), CURRENCY)
    assert adverse.periods[0].expense_total == Money(Decimal("2100.00"), CURRENCY)
    assert adverse.final_balance.amount < probable.final_balance.amount


def test_goal_contribution_uses_nonessential_multiplier() -> None:
    result = project_cashflow(
        accounts=[_account("0.00")],
        incomes=[],
        obligations=[],
        debts=[],
        goals=[_goal("500.00")],
        events=[],
        horizon_months=1,
        scenario=ScenarioParameters.adverse(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.periods[0].expense_total == Money(Decimal("450.00"), CURRENCY)


def test_horizon_options_return_matching_number_of_periods() -> None:
    for horizon in (3, 6, 12):
        result = project_cashflow(
            accounts=[_account("1000.00")],
            incomes=[_income("1000.00")],
            obligations=[_obligation("500.00")],
            debts=[],
            goals=[],
            events=[],
            horizon_months=horizon,
            scenario=ScenarioParameters.probable(CURRENCY),
            currency=CURRENCY,
            today=TODAY,
        )
        assert len(result.periods) == horizon
