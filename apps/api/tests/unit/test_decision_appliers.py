from datetime import date
from decimal import Decimal

from src.domain.decisions import appliers
from src.domain.decisions.context import DecisionContext
from src.domain.obligations.entities import IncomeSource
from src.domain.shared.enums import IncomeStability, Recurrence
from src.domain.shared.money import Money

CURRENCY = "BRL"
TODAY = date(2026, 7, 1)


def _income(amount: str, income_id: str = "income-1") -> IncomeSource:
    return IncomeSource(
        id=income_id,
        profile_id="profile-1",
        description="Salário",
        amount=Money(Decimal(amount), CURRENCY),
        frequency=Recurrence.MONTHLY,
        start_date=date(2024, 1, 1),
        end_date=None,
        stability=IncomeStability.STABLE,
    )


def test_cash_purchase_adds_one_off_expense_event():
    context = DecisionContext()
    result = appliers.apply_cash_purchase(context, {"amount": "500.00", "description": "Notebook"}, CURRENCY, TODAY)

    assert len(result.events) == 1
    assert result.events[0].amount == Money(Decimal("500.00"), CURRENCY)
    assert not context.events


def test_installment_purchase_creates_debt_and_down_payment_event():
    context = DecisionContext()
    result = appliers.apply_installment_purchase(
        context,
        {"amount": "1200.00", "down_payment": "200.00", "installments": 10, "description": "TV"},
        CURRENCY,
        TODAY,
    )

    assert len(result.events) == 1
    assert result.events[0].amount == Money(Decimal("200.00"), CURRENCY)
    assert len(result.debts) == 1
    debt = result.debts[0]
    assert debt.outstanding_balance == Money(Decimal("1000.00"), CURRENCY)
    assert debt.installment_amount == Money(Decimal("100.00"), CURRENCY)
    assert debt.remaining_installments == 10


def test_financing_creates_debt_recurring_and_one_off_costs():
    context = DecisionContext()
    result = appliers.apply_financing(
        context,
        {
            "total_amount": "50000.00",
            "down_payment": "10000.00",
            "installments": 40,
            "description": "Carro",
            "recurring_costs": [{"description": "Seguro", "amount": "150.00"}],
            "one_off_costs": [{"description": "Documentação", "amount": "800.00"}],
        },
        CURRENCY,
        TODAY,
    )

    assert len(result.debts) == 1
    assert result.debts[0].outstanding_balance == Money(Decimal("40000.00"), CURRENCY)
    assert len(result.obligations) == 1
    assert result.obligations[0].category == "financing_cost"
    assert len(result.events) == 2  # entrada + custo pontual


def test_loan_defaults_down_payment_to_zero():
    context = DecisionContext()
    result = appliers.apply_loan(
        context,
        {"amount": "5000.00", "installments": 12, "description": "Empréstimo pessoal"},
        CURRENCY,
        TODAY,
    )

    assert not result.events  # sem entrada
    assert result.debts[0].outstanding_balance == Money(Decimal("5000.00"), CURRENCY)


def test_income_loss_zeroes_income_for_duration_then_resumes():
    context = DecisionContext(incomes=[_income("5000.00")])
    result = appliers.apply_income_loss(
        context,
        {"income_source_id": "income-1", "months": 2},
        CURRENCY,
        TODAY,
    )

    assert len(result.incomes) == 2
    reduced = next(i for i in result.incomes if i.end_date is not None)
    resumed = next(i for i in result.incomes if i.start_date > TODAY)
    assert reduced.amount == Money(Decimal("0.00"), CURRENCY)
    assert resumed.amount == Money(Decimal("5000.00"), CURRENCY)


def test_salary_reduction_applies_permanent_partial_cut():
    context = DecisionContext(incomes=[_income("5000.00")])
    result = appliers.apply_salary_reduction(
        context,
        {"income_source_id": "income-1", "reduction_pct": "0.20"},
        CURRENCY,
        TODAY,
    )

    assert len(result.incomes) == 1
    assert result.incomes[0].amount == Money(Decimal("4000.00"), CURRENCY)
    assert result.incomes[0].end_date is None


def test_new_recurring_expense_adds_obligation():
    context = DecisionContext()
    result = appliers.apply_new_recurring_expense(
        context,
        {"description": "Streaming", "amount": "40.00", "category": "lazer", "frequency": "monthly", "essential": False},
        CURRENCY,
        TODAY,
    )

    assert len(result.obligations) == 1
    assert result.obligations[0].essential is False


def test_new_goal_adds_goal():
    context = DecisionContext()
    result = appliers.apply_new_goal(
        context,
        {"description": "Viagem", "target_amount": "6000.00", "monthly_contribution": "500.00", "priority": 2},
        CURRENCY,
        TODAY,
    )

    assert len(result.goals) == 1
    assert result.goals[0].monthly_contribution == Money(Decimal("500.00"), CURRENCY)


def test_reserve_increase_adds_nonessential_obligation():
    context = DecisionContext()
    result = appliers.apply_reserve_increase(context, {"monthly_amount": "300.00"}, CURRENCY, TODAY)

    assert len(result.obligations) == 1
    assert result.obligations[0].category == "reserve_increase"
    assert result.obligations[0].essential is False
