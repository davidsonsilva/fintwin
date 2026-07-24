from datetime import date, timedelta
from decimal import Decimal

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.fragility.detector import detect_fragilities
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.projection.engine import project_cashflow
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Direction, IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)


def _account(balance: str, eligible: bool = True) -> FinancialAccount:
    return FinancialAccount(
        id="acc",
        profile_id="profile-1",
        description="Conta",
        balance=Money(Decimal(balance), CURRENCY),
        liquidity_type=LiquidityType.EMERGENCY_FUND if eligible else LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=eligible,
    )


def _income(amount: str, description: str = "Renda", frequency: Recurrence = Recurrence.MONTHLY) -> IncomeSource:
    return IncomeSource(
        id=f"income-{description}",
        profile_id="profile-1",
        description=description,
        amount=Money(Decimal(amount), CURRENCY),
        frequency=frequency,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def _obligation(
    amount: str,
    essential: bool = True,
    debt_related: bool = False,
    due_day: int = 5,
    frequency: Recurrence = Recurrence.MONTHLY,
    description: str = "Obrigação",
) -> FinancialObligation:
    return FinancialObligation(
        id=f"obl-{description}",
        profile_id="profile-1",
        description=description,
        amount=Money(Decimal(amount), CURRENCY),
        category="geral",
        frequency=frequency,
        due_day=due_day,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=essential,
        debt_related=debt_related,
    )


def _debt(installment: str, remaining: int = 12, due_day: int = 10, description: str = "Dívida") -> Debt:
    return Debt(
        id=f"debt-{description}",
        profile_id="profile-1",
        description=description,
        outstanding_balance=Money(Decimal("10000.00"), CURRENCY),
        installment_amount=Money(Decimal(installment), CURRENCY),
        remaining_installments=remaining,
        interest_rate_optional=None,
        due_day=due_day,
    )


def _goal(contribution: str, priority: int = 1, description: str = "Meta") -> FinancialGoal:
    return FinancialGoal(
        id=f"goal-{description}",
        profile_id="profile-1",
        description=description,
        target_amount=Money(Decimal("10000.00"), CURRENCY),
        current_amount=Money(Decimal("1000.00"), CURRENCY),
        deadline=None,
        priority=priority,
        monthly_contribution=Money(Decimal(contribution), CURRENCY),
    )


def _event(
    amount: str,
    event_date: date,
    direction: Direction = Direction.EXPENSE,
    recurrence=None,
    description: str = "Evento",
) -> FinancialEvent:
    return FinancialEvent(
        id=f"event-{description}",
        profile_id="profile-1",
        description=description,
        event_type="tax",
        amount=Money(Decimal(amount), CURRENCY),
        date=event_date,
        recurrence=recurrence,
        direction=direction,
    )


def _detect(
    accounts=None,
    incomes=None,
    obligations=None,
    debts=None,
    goals=None,
    events=None,
):
    accounts = accounts or []
    incomes = incomes or []
    obligations = obligations or []
    debts = debts or []
    goals = goals or []
    events = events or []

    projection = project_cashflow(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        horizon_months=3,
        scenario=ScenarioParameters.probable(CURRENCY),
        currency=CURRENCY,
        today=TODAY,
    )
    autonomy = calculate_autonomy(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=CURRENCY,
        expense_reduction_capacity=None,
        today=TODAY,
    )
    return detect_fragilities(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=CURRENCY,
        projection=projection,
        autonomy=autonomy,
    )


def _codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_healthy_profile_triggers_no_fragilities() -> None:
    # Duas fontes de renda (nenhuma > 80%) para não disparar INCOME_CONCENTRATION,
    # que dispararia trivialmente com uma única fonte de renda.
    findings = _detect(
        accounts=[_account("30000.00")],
        incomes=[_income("5000.00", description="Principal"), _income("3000.00", description="Secundária")],
        obligations=[_obligation("2000.00", essential=True, due_day=5)],
    )
    assert findings == []


def test_income_concentration_fires_above_eighty_percent() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("9000.00", description="Principal"), _income("500.00", description="Extra")],
    )
    assert "INCOME_CONCENTRATION" in _codes(findings)


def test_essential_expense_ratio_fires_above_sixty_percent() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
    )
    assert "ESSENTIAL_EXPENSE_RATIO" in _codes(findings)


def test_debt_service_ratio_fires_above_thirty_percent() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("500.00", essential=True)],
        debts=[_debt("1500.00", remaining=6)],
    )
    assert "DEBT_SERVICE_RATIO" in _codes(findings)


def test_recurring_credit_for_essentials_fires_when_debt_related_essential_exists() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("500.00", essential=True, debt_related=True)],
    )
    assert "RECURRING_CREDIT_FOR_ESSENTIALS" in _codes(findings)


def test_projected_reserve_decline_fires_when_three_consecutive_negative_months() -> None:
    findings = _detect(
        accounts=[_account("5000.00")],
        incomes=[_income("1000.00")],
        obligations=[_obligation("3000.00", essential=True)],
    )
    assert "PROJECTED_RESERVE_DECLINE" in _codes(findings)


def test_concentrated_due_dates_fires_with_three_essential_items_in_a_week() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("6000.00")],
        obligations=[
            _obligation("500.00", essential=True, due_day=5, description="Aluguel"),
            _obligation("300.00", essential=True, due_day=7, description="Água"),
            _obligation("200.00", essential=True, due_day=10, description="Luz"),
        ],
    )
    assert "CONCENTRATED_DUE_DATES" in _codes(findings)


def test_projected_deficit_90_days_fires_when_a_period_goes_negative() -> None:
    findings = _detect(
        accounts=[_account("100.00")],
        incomes=[_income("500.00")],
        obligations=[_obligation("3000.00", essential=True)],
    )
    assert "PROJECTED_DEFICIT_90_DAYS" in _codes(findings)


def test_reserve_below_three_months_fires_when_autonomy_under_threshold() -> None:
    findings = _detect(
        accounts=[_account("2000.00")],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
    )
    assert "RESERVE_BELOW_THREE_MONTHS" in _codes(findings)


def test_reserve_below_three_months_does_not_fire_without_essential_expenses() -> None:
    findings = _detect(accounts=[_account("100.00")], incomes=[_income("4000.00")])
    assert "RESERVE_BELOW_THREE_MONTHS" not in _codes(findings)


def test_unprovisioned_annual_expense_fires_for_yearly_obligation() -> None:
    findings = _detect(
        accounts=[_account("30000.00")],
        incomes=[_income("8000.00")],
        obligations=[
            _obligation("2000.00", essential=True),
            _obligation("1200.00", essential=True, frequency=Recurrence.YEARLY, description="IPTU"),
        ],
    )
    assert "UNPROVISIONED_ANNUAL_EXPENSE" in _codes(findings)


def test_unprovisioned_annual_expense_fires_for_yearly_event() -> None:
    findings = _detect(
        accounts=[_account("30000.00")],
        incomes=[_income("8000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        events=[_event("1200.00", TODAY + timedelta(days=30), direction=Direction.EXPENSE, recurrence=Recurrence.YEARLY)],
    )
    assert "UNPROVISIONED_ANNUAL_EXPENSE" in _codes(findings)


def test_uncovered_future_installments_fires_when_debt_exceeds_disposable_income() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
        debts=[_debt("1000.00", remaining=6)],
    )
    assert "UNCOVERED_FUTURE_INSTALLMENTS" in _codes(findings)


def test_incompatible_goal_fires_when_contribution_exceeds_disposable_income() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("3000.00")],
        obligations=[_obligation("2500.00", essential=True)],
        goals=[_goal("600.00", priority=1)],
    )
    assert "INCOMPATIBLE_GOAL" in _codes(findings)


def test_incompatible_goal_does_not_fire_when_affordable() -> None:
    findings = _detect(
        accounts=[_account("10000.00")],
        incomes=[_income("6000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        goals=[_goal("500.00", priority=1)],
    )
    assert "INCOMPATIBLE_GOAL" not in _codes(findings)
