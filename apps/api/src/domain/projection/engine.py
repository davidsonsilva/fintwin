# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Motor de projeção de fluxo de caixa (Spec seção 8), puro e determinístico.

Sem imports de framework — reutilizado pela VS-05 (autonomia ajustada),
VS-06 (radar de fragilidade) e VS-07 (simulador).
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.financial_profile.entities import FinancialAccount
from src.domain.obligations.entities import Debt, FinancialObligation, IncomeSource
from src.domain.projection.entities import PeriodProjection, ProjectionResult
from src.domain.projection.scenario import ScenarioParameters
from src.domain.shared.enums import Direction, Recurrence
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent


def _add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _period_bounds(period_start: date) -> tuple[date, date]:
    period_end = _add_months(period_start, 1) - timedelta(days=1)
    return period_start, period_end


def _is_active(start_date: date, end_date: Optional[date], period_start: date, period_end: date) -> bool:
    if start_date > period_end:
        return False
    if end_date is not None and end_date < period_start:
        return False
    return True


def _event_occurrences(event: FinancialEvent, period_start: date, period_end: date) -> int:
    if event.date > period_end:
        return 0
    if event.recurrence is None or event.recurrence == Recurrence.ONE_OFF:
        return 1 if period_start <= event.date <= period_end else 0
    if event.recurrence == Recurrence.MONTHLY:
        return 1
    if event.recurrence == Recurrence.YEARLY:
        return 1 if event.date.month == period_start.month else 0
    if event.recurrence == Recurrence.WEEKLY:
        count = 0
        occurrence = event.date
        while occurrence <= period_end:
            if occurrence >= period_start:
                count += 1
            occurrence += timedelta(days=7)
        return count
    return 0


def project_cashflow(
    accounts: list[FinancialAccount],
    incomes: list[IncomeSource],
    obligations: list[FinancialObligation],
    debts: list[Debt],
    goals: list[FinancialGoal],
    events: list[FinancialEvent],
    horizon_months: int,
    scenario: ScenarioParameters,
    currency: str,
    today: Optional[date] = None,
) -> ProjectionResult:
    today = today or date.today()
    zero = Money(Decimal("0"), currency)

    opening_balance = zero
    for account in accounts:
        opening_balance = opening_balance.add(account.balance)

    period_start = today.replace(day=1)
    remaining_installments = {debt.id: debt.remaining_installments for debt in debts}

    periods: list[PeriodProjection] = []
    relevant_events: list[FinancialEvent] = []
    running_balance = opening_balance

    for _ in range(horizon_months):
        p_start, p_end = _period_bounds(period_start)
        opening = running_balance

        income_total = zero
        for income in incomes:
            if income.frequency == Recurrence.ONE_OFF:
                if p_start <= income.start_date <= p_end:
                    income_total = income_total.add(income.amount.multiply(scenario.income_multiplier))
                continue
            if _is_active(income.start_date, income.end_date, p_start, p_end):
                monthly = monthly_equivalent(income.amount, income.frequency)
                if monthly is not None:
                    income_total = income_total.add(monthly.multiply(scenario.income_multiplier))

        expense_total = zero
        for obligation in obligations:
            multiplier = (
                scenario.essential_expense_multiplier
                if obligation.essential
                else scenario.nonessential_expense_multiplier
            )
            if obligation.frequency == Recurrence.ONE_OFF:
                if p_start <= obligation.start_date <= p_end:
                    expense_total = expense_total.add(obligation.amount.multiply(multiplier))
                continue
            if _is_active(obligation.start_date, obligation.end_date, p_start, p_end):
                monthly = monthly_equivalent(obligation.amount, obligation.frequency)
                if monthly is not None:
                    expense_total = expense_total.add(monthly.multiply(multiplier))

        for debt in debts:
            if remaining_installments[debt.id] > 0:
                expense_total = expense_total.add(debt.installment_amount)
                remaining_installments[debt.id] -= 1

        for goal in goals:
            expense_total = expense_total.add(goal.monthly_contribution.multiply(scenario.nonessential_expense_multiplier))

        for event in events:
            occurrences = _event_occurrences(event, p_start, p_end)
            if occurrences == 0:
                continue
            total_amount = event.amount.multiply(Decimal(occurrences))
            if event.direction == Direction.INCOME:
                income_total = income_total.add(total_amount)
            else:
                expense_total = expense_total.add(total_amount)
            relevant_events.append(event)

        expense_total = expense_total.add(scenario.unexpected_expense)

        net_cashflow = income_total.subtract(expense_total)
        closing_balance = opening.add(net_cashflow)

        income_commitment_percentage = None
        if income_total.amount > 0:
            fraction = min(expense_total.amount / income_total.amount, Decimal("1"))
            income_commitment_percentage = Percentage(fraction)

        periods.append(
            PeriodProjection(
                period=f"{p_start.year:04d}-{p_start.month:02d}",
                opening_balance=opening,
                income_total=income_total,
                expense_total=expense_total,
                net_cashflow=net_cashflow,
                closing_balance=closing_balance,
                income_commitment_percentage=income_commitment_percentage,
                deficit=closing_balance.is_negative(),
            )
        )

        running_balance = closing_balance
        period_start = _add_months(period_start, 1)

    first_deficit_period = next((p.period for p in periods if p.deficit), None)
    lowest_balance = min([opening_balance] + [p.closing_balance for p in periods], key=lambda m: m.amount)
    final_balance = periods[-1].closing_balance
    total_income = zero
    total_expenses = zero
    for p in periods:
        total_income = total_income.add(p.income_total)
        total_expenses = total_expenses.add(p.expense_total)

    essential_categories = sorted(
        {obligation.category for obligation in obligations if obligation.essential},
    )
    main_pressures = essential_categories[:3]

    assumptions = [
        f"Cenário {scenario.scenario_type.value}: renda x{scenario.income_multiplier}, "
        f"despesas essenciais x{scenario.essential_expense_multiplier}, "
        f"despesas não essenciais x{scenario.nonessential_expense_multiplier}.",
        "Despesa inesperada não configurada nesta simulação (0,00).",
        "Eventos futuros e dívidas entram pelo valor contratual/cadastrado, sem ajuste de cenário.",
    ]

    return ProjectionResult(
        scenario=scenario.scenario_type,
        periods=periods,
        first_deficit_period=first_deficit_period,
        lowest_balance=lowest_balance,
        final_balance=final_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        main_pressures=main_pressures,
        relevant_events=relevant_events,
        assumptions=assumptions,
    )
