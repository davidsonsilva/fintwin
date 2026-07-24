from datetime import date
from decimal import Decimal

from src.domain.decisions.context import DecisionContext
from src.domain.decisions.engine import simulate_decision
from src.domain.decisions.entities import FinancialGoal
from src.domain.decisions.scenario_override import ScenarioOverride
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import FinancialObligation, IncomeSource
from src.domain.shared.enums import IncomeStability, LiquidityType, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)


def _base_context() -> DecisionContext:
    return DecisionContext(
        accounts=[
            FinancialAccount(
                id="acc-1",
                profile_id="profile-1",
                description="Reserva",
                balance=Money(Decimal("20000.00"), CURRENCY),
                liquidity_type=LiquidityType.EMERGENCY_FUND,
                eligible_for_autonomy=True,
            )
        ],
        incomes=[
            IncomeSource(
                id="income-1",
                profile_id="profile-1",
                description="Salário",
                amount=Money(Decimal("6000.00"), CURRENCY),
                frequency=Recurrence.MONTHLY,
                start_date=date(2024, 1, 1),
                end_date=None,
                stability=IncomeStability.STABLE,
            )
        ],
        obligations=[
            FinancialObligation(
                id="obl-1",
                profile_id="profile-1",
                description="Aluguel",
                amount=Money(Decimal("2000.00"), CURRENCY),
                category="moradia",
                frequency=Recurrence.MONTHLY,
                due_day=5,
                start_date=date(2024, 1, 1),
                end_date=None,
                essential=True,
                debt_related=False,
            )
        ],
    )


def test_simulate_cash_purchase_reduces_final_balance():
    context = _base_context()
    outcome = simulate_decision(
        context=context,
        decision_type="CASH_PURCHASE",
        parameters={"amount": "3000.00", "description": "Notebook"},
        scenario_override=None,
        horizon_months=3,
        currency=CURRENCY,
        today=TODAY,
    )

    assert Decimal(outcome.impact["closing_balance_delta"]) == Decimal("-3000.00")
    assert outcome.total_cost is None


def test_simulate_installment_purchase_computes_total_cost():
    context = _base_context()
    outcome = simulate_decision(
        context=context,
        decision_type="INSTALLMENT_PURCHASE",
        parameters={"amount": "1200.00", "down_payment": "200.00", "installments": 10, "description": "TV"},
        scenario_override=None,
        horizon_months=3,
        currency=CURRENCY,
        today=TODAY,
    )

    assert outcome.total_cost is not None
    assert outcome.total_cost["total_cost"]["amount"] == "1200.00"


def test_simulate_income_loss_creates_deficit_in_projection():
    context = _base_context()
    context.accounts[0] = FinancialAccount(
        id="acc-1",
        profile_id="profile-1",
        description="Reserva",
        balance=Money(Decimal("3000.00"), CURRENCY),
        liquidity_type=LiquidityType.EMERGENCY_FUND,
        eligible_for_autonomy=True,
    )
    outcome = simulate_decision(
        context=context,
        decision_type="INCOME_LOSS",
        parameters={"income_source_id": "income-1", "months": 6},
        scenario_override=None,
        horizon_months=3,
        currency=CURRENCY,
        today=TODAY,
    )

    # Autonomia mede ativos/queima (despesas), não é afetada pela perda de renda em si
    # (achado documentado na VS-05) — o impacto de uma perda de renda aparece como déficit
    # projetado no fluxo de caixa, não como delta de autonomia.
    assert Decimal(outcome.impact["autonomy_delta_months"]) == 0
    assert outcome.simulated_result["first_deficit_period"] is not None
    assert outcome.baseline_result["first_deficit_period"] is None


def test_simulate_new_goal_reports_goal_delay_none_when_no_baseline_goal():
    context = _base_context()
    outcome = simulate_decision(
        context=context,
        decision_type="NEW_GOAL",
        parameters={"description": "Viagem", "target_amount": "6000.00", "monthly_contribution": "500.00"},
        scenario_override=None,
        horizon_months=3,
        currency=CURRENCY,
        today=TODAY,
    )

    assert outcome.impact["goal_delay_months"] is None


def test_simulate_with_custom_scenario_override_applies_multipliers():
    context = _base_context()
    outcome = simulate_decision(
        context=context,
        decision_type="NEW_RECURRING_EXPENSE",
        parameters={"description": "Streaming", "amount": "40.00", "category": "lazer", "frequency": "monthly", "essential": False},
        scenario_override=ScenarioOverride(essential_expense_multiplier=Decimal("1.10")),
        horizon_months=1,
        currency=CURRENCY,
        today=TODAY,
    )

    assert outcome.simulated_result["scenario"] == "custom"


def test_goal_delay_computed_when_baseline_and_simulated_goals_exist():
    context = _base_context()
    context.goals.append(
        FinancialGoal(
            id="goal-1",
            profile_id="profile-1",
            description="Entrada de imóvel",
            target_amount=Money(Decimal("50000.00"), CURRENCY),
            current_amount=Money(Decimal("10000.00"), CURRENCY),
            deadline=None,
            priority=1,
            monthly_contribution=Money(Decimal("1000.00"), CURRENCY),
        )
    )
    outcome = simulate_decision(
        context=context,
        decision_type="CASH_PURCHASE",
        parameters={"amount": "500.00", "description": "Notebook"},
        scenario_override=None,
        horizon_months=1,
        currency=CURRENCY,
        today=TODAY,
    )

    assert outcome.impact["goal_delay_months"] == 0
