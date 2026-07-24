from datetime import date, datetime
from decimal import Decimal

import pytest

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal, Simulation
from src.domain.financial_profile.entities import FinancialAccount, FinancialProfile
from src.domain.fragility.entities import FragilityFinding
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.preventive_plans.entities import PreventivePlan
from src.domain.shared.enums import (
    Direction,
    IncomeStability,
    LiquidityType,
    PlanStatus,
    Recurrence,
    Severity,
)
from src.domain.shared.money import Money


def test_financial_profile_requires_id():
    with pytest.raises(ValueError):
        FinancialProfile(
            id="",
            currency="BRL",
            dependents=0,
            monthly_expense_reduction_capacity=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


def test_financial_profile_rejects_negative_dependents():
    with pytest.raises(ValueError):
        FinancialProfile(
            id="p1",
            currency="BRL",
            dependents=-1,
            monthly_expense_reduction_capacity=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


def test_financial_account_valid():
    account = FinancialAccount(
        id="a1",
        profile_id="p1",
        description="Conta corrente",
        balance=Money(Decimal("1000.00"), "BRL"),
        liquidity_type=LiquidityType.CHECKING_ACCOUNT,
        eligible_for_autonomy=True,
    )
    assert account.balance.amount == Decimal("1000.00")


def test_income_source_rejects_end_before_start():
    with pytest.raises(ValueError):
        IncomeSource(
            id="i1",
            profile_id="p1",
            description="Salário",
            amount=Money(Decimal("5000.00"), "BRL"),
            frequency=Recurrence.MONTHLY,
            start_date=date(2026, 1, 1),
            end_date=date(2025, 1, 1),
            stability=IncomeStability.STABLE,
        )


def test_financial_obligation_rejects_invalid_due_day():
    with pytest.raises(ValueError):
        FinancialObligation(
            id="o1",
            profile_id="p1",
            description="Aluguel",
            amount=Money(Decimal("1500.00"), "BRL"),
            category="moradia",
            frequency=Recurrence.MONTHLY,
            due_day=32,
            start_date=date(2026, 1, 1),
            end_date=None,
            essential=True,
            debt_related=False,
        )


def test_debt_rejects_negative_remaining_installments():
    with pytest.raises(ValueError):
        Debt(
            id="d1",
            profile_id="p1",
            description="Financiamento veículo",
            outstanding_balance=Money(Decimal("40000.00"), "BRL"),
            installment_amount=Money(Decimal("1350.00"), "BRL"),
            remaining_installments=-1,
            interest_rate_optional=None,
            due_day=10,
        )


def test_financial_event_requires_description():
    with pytest.raises(ValueError):
        FinancialEvent(
            id="e1",
            profile_id="p1",
            description="",
            event_type="bonus",
            amount=Money(Decimal("2000.00"), "BRL"),
            date=date(2026, 12, 1),
            recurrence=None,
            direction=Direction.INCOME,
        )


def test_financial_goal_rejects_invalid_priority():
    with pytest.raises(ValueError):
        FinancialGoal(
            id="g1",
            profile_id="p1",
            description="Reserva de emergência",
            target_amount=Money(Decimal("20000.00"), "BRL"),
            current_amount=Money(Decimal("5000.00"), "BRL"),
            deadline=None,
            priority=0,
            monthly_contribution=Money(Decimal("500.00"), "BRL"),
        )


def test_simulation_requires_type():
    with pytest.raises(ValueError):
        Simulation(
            id="s1",
            profile_id="p1",
            type="",
            parameters={},
            baseline_result={},
            simulated_result={},
            created_at=datetime.now(),
        )


def test_fragility_finding_requires_evidence():
    with pytest.raises(ValueError):
        FragilityFinding(
            id="f1",
            profile_id="p1",
            code="INCOME_CONCENTRATION",
            severity=Severity.HIGH,
            evidence={},
            detected_at=date(2026, 7, 22),
            status="open",
        )


def test_fragility_finding_valid_with_evidence():
    finding = FragilityFinding(
        id="f1",
        profile_id="p1",
        code="INCOME_CONCENTRATION",
        severity=Severity.HIGH,
        evidence={"main_source_percentage": "0.92"},
        detected_at=date(2026, 7, 22),
        status="open",
    )
    assert finding.severity == Severity.HIGH


def test_preventive_plan_requires_actions():
    with pytest.raises(ValueError):
        PreventivePlan(
            id="plan-001",
            profile_id="p1",
            risk_code="NEGATIVE_BALANCE_90_DAYS",
            status=PlanStatus.PROPOSED,
            actions=[],
            expected_result={"deficit_avoided": True},
            created_at=datetime.now(),
        )


def test_preventive_plan_valid():
    plan = PreventivePlan(
        id="plan-001",
        profile_id="p1",
        risk_code="NEGATIVE_BALANCE_90_DAYS",
        status=PlanStatus.PROPOSED,
        actions=[{"description": "Reservar R$ 500 por mês", "expected_monthly_impact": "500.00"}],
        expected_result={"deficit_avoided": True},
        created_at=datetime.now(),
    )
    assert plan.status == PlanStatus.PROPOSED
