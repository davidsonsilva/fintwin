# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Detector de fragilidades (Spec seção 11), puro e determinístico.

Reaproveita `project_cashflow` (VS-04) e `calculate_autonomy` (VS-05) — ambos
já calculados uma vez pelo caso de uso e passados aqui, sem recomputar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional

from src.domain.autonomy.entities import AutonomyResult
from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.projection.entities import ProjectionResult
from src.domain.shared.enums import Direction, Recurrence, Severity
from src.domain.shared.money import Money
from src.domain.shared.recurrence import monthly_equivalent


@dataclass
class DetectedFragility:
    code: str
    severity: Severity
    evidence: dict[str, Any]


@dataclass
class FragilityContext:
    accounts: list[FinancialAccount]
    incomes: list[IncomeSource]
    obligations: list[FinancialObligation]
    debts: list[Debt]
    goals: list[FinancialGoal]
    events: list[FinancialEvent]
    currency: str
    projection: ProjectionResult
    autonomy: AutonomyResult
    total_income_monthly: Money = field(init=False)
    debt_service_monthly: Money = field(init=False)

    def __post_init__(self) -> None:
        zero = Money(Decimal("0"), self.currency)
        total_income = zero
        for income in self.incomes:
            monthly = monthly_equivalent(income.amount, income.frequency)
            if monthly is not None:
                total_income = total_income.add(monthly)
        self.total_income_monthly = total_income

        debt_service = zero
        for debt in self.debts:
            if debt.remaining_installments > 0:
                debt_service = debt_service.add(debt.installment_amount)
        self.debt_service_monthly = debt_service


def _rule_income_concentration(ctx: FragilityContext) -> Optional[DetectedFragility]:
    entries = []
    for income in ctx.incomes:
        monthly = monthly_equivalent(income.amount, income.frequency)
        if monthly is not None:
            entries.append((income.description, monthly))
    if not entries:
        return None
    total = sum((amount.amount for _, amount in entries), Decimal("0"))
    if total <= 0:
        return None
    main_description, main_amount = max(entries, key=lambda entry: entry[1].amount)
    fraction = main_amount.amount / total
    if fraction <= Decimal("0.80"):
        return None
    return DetectedFragility(
        code="INCOME_CONCENTRATION",
        severity=Severity.HIGH,
        evidence={
            "main_source_description": main_description,
            "main_source_percentage": str(fraction),
            "total_income_monthly": str(total),
        },
    )


def _rule_essential_expense_ratio(ctx: FragilityContext) -> Optional[DetectedFragility]:
    if ctx.total_income_monthly.amount <= 0:
        return None
    fraction = ctx.autonomy.essential_expenses_monthly.amount / ctx.total_income_monthly.amount
    if fraction <= Decimal("0.60"):
        return None
    return DetectedFragility(
        code="ESSENTIAL_EXPENSE_RATIO",
        severity=Severity.HIGH,
        evidence={
            "essential_expenses_monthly": str(ctx.autonomy.essential_expenses_monthly.amount),
            "total_income_monthly": str(ctx.total_income_monthly.amount),
            "ratio": str(fraction),
        },
    )


def _rule_debt_service_ratio(ctx: FragilityContext) -> Optional[DetectedFragility]:
    if ctx.total_income_monthly.amount <= 0:
        return None
    fraction = ctx.debt_service_monthly.amount / ctx.total_income_monthly.amount
    if fraction <= Decimal("0.30"):
        return None
    return DetectedFragility(
        code="DEBT_SERVICE_RATIO",
        severity=Severity.HIGH,
        evidence={
            "debt_service_monthly": str(ctx.debt_service_monthly.amount),
            "total_income_monthly": str(ctx.total_income_monthly.amount),
            "ratio": str(fraction),
        },
    )


def _rule_recurring_credit_for_essentials(ctx: FragilityContext) -> Optional[DetectedFragility]:
    matches = [
        obligation
        for obligation in ctx.obligations
        if obligation.essential and obligation.debt_related and obligation.frequency != Recurrence.ONE_OFF
    ]
    if not matches:
        return None
    return DetectedFragility(
        code="RECURRING_CREDIT_FOR_ESSENTIALS",
        severity=Severity.MEDIUM,
        evidence={"obligations": [obligation.description for obligation in matches]},
    )


def _rule_projected_reserve_decline(ctx: FragilityContext) -> Optional[DetectedFragility]:
    periods = ctx.projection.periods[:3]
    if len(periods) < 3:
        return None
    if not all(period.net_cashflow.is_negative() for period in periods):
        return None
    return DetectedFragility(
        code="PROJECTED_RESERVE_DECLINE",
        severity=Severity.MEDIUM,
        evidence={"periods": [period.period for period in periods]},
    )


def _rule_concentrated_due_dates(ctx: FragilityContext) -> Optional[DetectedFragility]:
    items: list[tuple[int, str]] = [
        (obligation.due_day, obligation.description) for obligation in ctx.obligations if obligation.essential
    ]
    items += [(debt.due_day, debt.description) for debt in ctx.debts]
    if len(items) < 3:
        return None
    for window_start in range(1, 32):
        window_items = [description for day, description in items if window_start <= day <= window_start + 6]
        if len(window_items) >= 3:
            return DetectedFragility(
                code="CONCENTRATED_DUE_DATES",
                severity=Severity.LOW,
                evidence={"window_start_day": window_start, "items": window_items},
            )
    return None


def _rule_projected_deficit_90_days(ctx: FragilityContext) -> Optional[DetectedFragility]:
    deficit_periods = [period.period for period in ctx.projection.periods if period.deficit]
    if not deficit_periods:
        return None
    return DetectedFragility(
        code="PROJECTED_DEFICIT_90_DAYS",
        severity=Severity.CRITICAL,
        evidence={"first_deficit_period": deficit_periods[0], "deficit_periods": deficit_periods},
    )


def _rule_reserve_below_three_months(ctx: FragilityContext) -> Optional[DetectedFragility]:
    months = ctx.autonomy.basic_autonomy_months
    if months is None or months >= Decimal("3"):
        return None
    return DetectedFragility(
        code="RESERVE_BELOW_THREE_MONTHS",
        severity=Severity.HIGH,
        evidence={"basic_autonomy_months": str(months)},
    )


def _rule_unprovisioned_annual_expense(ctx: FragilityContext) -> Optional[DetectedFragility]:
    items = [obligation.description for obligation in ctx.obligations if obligation.frequency == Recurrence.YEARLY]
    items += [
        event.description
        for event in ctx.events
        if event.recurrence == Recurrence.YEARLY and event.direction == Direction.EXPENSE
    ]
    if not items:
        return None
    return DetectedFragility(
        code="UNPROVISIONED_ANNUAL_EXPENSE",
        severity=Severity.MEDIUM,
        evidence={"items": items},
    )


def _rule_uncovered_future_installments(ctx: FragilityContext) -> Optional[DetectedFragility]:
    disposable = ctx.total_income_monthly.amount - ctx.autonomy.essential_expenses_monthly.amount
    if ctx.debt_service_monthly.amount <= disposable:
        return None
    return DetectedFragility(
        code="UNCOVERED_FUTURE_INSTALLMENTS",
        severity=Severity.HIGH,
        evidence={
            "debt_service_monthly": str(ctx.debt_service_monthly.amount),
            "disposable_income_after_essentials": str(disposable),
        },
    )


def _rule_incompatible_goal(ctx: FragilityContext) -> Optional[DetectedFragility]:
    if not ctx.goals:
        return None
    top_goal = min(ctx.goals, key=lambda goal: goal.priority)
    disposable = (
        ctx.total_income_monthly.amount
        - ctx.autonomy.essential_expenses_monthly.amount
        - ctx.debt_service_monthly.amount
    )
    if disposable >= top_goal.monthly_contribution.amount:
        return None
    return DetectedFragility(
        code="INCOMPATIBLE_GOAL",
        severity=Severity.MEDIUM,
        evidence={
            "goal_description": top_goal.description,
            "goal_monthly_contribution": str(top_goal.monthly_contribution.amount),
            "disposable_income": str(disposable),
        },
    )


_RULES = [
    _rule_income_concentration,
    _rule_essential_expense_ratio,
    _rule_debt_service_ratio,
    _rule_recurring_credit_for_essentials,
    _rule_projected_reserve_decline,
    _rule_concentrated_due_dates,
    _rule_projected_deficit_90_days,
    _rule_reserve_below_three_months,
    _rule_unprovisioned_annual_expense,
    _rule_uncovered_future_installments,
    _rule_incompatible_goal,
]


def detect_fragilities(
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    currency: str,
    projection: ProjectionResult,
    autonomy: AutonomyResult,
) -> list[DetectedFragility]:
    context = FragilityContext(
        accounts=accounts,
        incomes=incomes,
        obligations=obligations,
        debts=debts,
        goals=goals,
        events=events,
        currency=currency,
        projection=projection,
        autonomy=autonomy,
    )
    findings = []
    for rule in _RULES:
        result = rule(context)
        if result is not None:
            findings.append(result)
    return findings
