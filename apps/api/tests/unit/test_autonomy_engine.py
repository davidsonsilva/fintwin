from datetime import date
from decimal import Decimal

from src.domain.autonomy.engine import calculate_autonomy
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.shared.enums import IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)


def _account(balance: str, eligible: bool) -> FinancialAccount:
    return FinancialAccount(
        id="acc",
        profile_id="profile-1",
        description="Conta",
        balance=Money(Decimal(balance), CURRENCY),
        liquidity_type=LiquidityType.EMERGENCY_FUND if eligible else LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=eligible,
    )


def _income(amount: str) -> IncomeSource:
    return IncomeSource(
        id="income",
        profile_id="profile-1",
        description="Salário",
        amount=Money(Decimal(amount), CURRENCY),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def _obligation(amount: str, essential: bool) -> FinancialObligation:
    return FinancialObligation(
        id="obl",
        profile_id="profile-1",
        description="Despesa",
        amount=Money(Decimal(amount), CURRENCY),
        category="moradia",
        frequency=Recurrence.MONTHLY,
        due_day=5,
        start_date=date(2024, 1, 1),
        end_date=None,
        essential=essential,
        debt_related=False,
    )


def test_basic_autonomy_uses_only_eligible_assets_and_essential_expenses() -> None:
    result = calculate_autonomy(
        accounts=[_account("6000.00", eligible=True), _account("10000.00", eligible=False)],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True), _obligation("500.00", essential=False)],
        debts=[],
        goals=[],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.eligible_assets == Money(Decimal("6000.00"), CURRENCY)
    assert result.essential_expenses_monthly == Money(Decimal("2000.00"), CURRENCY)
    assert result.basic_autonomy_months == Decimal("3")
    assert len(result.eligible_accounts) == 1
    assert len(result.essential_obligations) == 1


def test_basic_autonomy_is_none_without_essential_expenses() -> None:
    result = calculate_autonomy(
        accounts=[_account("1000.00", eligible=True)],
        incomes=[],
        obligations=[],
        debts=[],
        goals=[],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.basic_autonomy_months is None


def test_scenario_burns_apply_each_scenarios_own_multipliers() -> None:
    # Com nonessential (500) bem menor que essential (2000): o aumento de 5%
    # nas essenciais do cenário adverso pesa mais que o corte de 10% nas não
    # essenciais, então adverso > provável. income_loss não soma o multiplicador
    # essencial do adverso, apenas corta 30% das não essenciais — não é
    # necessariamente o pior burn, já que autonomia mede queima de despesas,
    # não o impacto da renda perdida (isso aparece no fluxo de caixa, VS-04).
    result = calculate_autonomy(
        accounts=[_account("6000.00", eligible=True)],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True), _obligation("500.00", essential=False)],
        debts=[],
        goals=[],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.probable_monthly_burn == Money(Decimal("2500.00"), CURRENCY)
    assert result.adverse_monthly_burn == Money(Decimal("2550.00"), CURRENCY)
    assert result.income_loss_monthly_burn == Money(Decimal("2350.00"), CURRENCY)

    assert result.adverse_autonomy_months < result.probable_autonomy_months


def test_expense_reduction_capacity_reduces_adjusted_burn() -> None:
    common_kwargs = dict(
        accounts=[_account("6000.00", eligible=True)],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        debts=[],
        goals=[],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    without_capacity = calculate_autonomy(**common_kwargs)
    with_capacity = calculate_autonomy(expense_reduction_capacity=Percentage(Decimal("0.20")), **common_kwargs)

    assert with_capacity.probable_monthly_burn.amount < without_capacity.probable_monthly_burn.amount
    assert with_capacity.probable_monthly_burn == Money(Decimal("1600.00"), CURRENCY)
    assert with_capacity.probable_autonomy_months > without_capacity.probable_autonomy_months


def test_debt_installments_increase_adjusted_burn_but_not_basic_autonomy() -> None:
    debt = Debt(
        id="debt",
        profile_id="profile-1",
        description="Financiamento",
        outstanding_balance=Money(Decimal("10000.00"), CURRENCY),
        installment_amount=Money(Decimal("500.00"), CURRENCY),
        remaining_installments=10,
        interest_rate_optional=None,
        due_day=10,
    )

    result = calculate_autonomy(
        accounts=[_account("6000.00", eligible=True)],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        debts=[debt],
        goals=[],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.essential_expenses_monthly == Money(Decimal("2000.00"), CURRENCY)
    assert result.probable_monthly_burn == Money(Decimal("2500.00"), CURRENCY)


def test_goal_contribution_included_in_adjusted_burn() -> None:
    goal = FinancialGoal(
        id="goal",
        profile_id="profile-1",
        description="Reserva",
        target_amount=Money(Decimal("10000.00"), CURRENCY),
        current_amount=Money(Decimal("1000.00"), CURRENCY),
        deadline=None,
        priority=1,
        monthly_contribution=Money(Decimal("300.00"), CURRENCY),
    )

    result = calculate_autonomy(
        accounts=[_account("6000.00", eligible=True)],
        incomes=[_income("4000.00")],
        obligations=[_obligation("2000.00", essential=True)],
        debts=[],
        goals=[goal],
        events=[],
        currency=CURRENCY,
        today=TODAY,
    )

    assert result.probable_monthly_burn == Money(Decimal("2300.00"), CURRENCY)
