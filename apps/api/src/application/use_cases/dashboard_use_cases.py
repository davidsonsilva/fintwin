"""Resumo financeiro do dashboard (VS-03): apenas dados calculáveis a partir do
que já está persistido — sem projeção (VS-04), autonomia (VS-05) ou
fragilidades (VS-06), que dependem de motores ainda não implementados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from src.domain.cashflow.entities import FinancialEvent
from src.domain.decisions.entities import FinancialGoal
from src.domain.obligations.entities import FinancialObligation, IncomeSource
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent


def _sum_money(currency: str, values: list[Money]) -> Money:
    total = Money(Decimal("0"), currency)
    for value in values:
        total = total.add(value)
    return total


@dataclass
class MainGoalSummary:
    description: str
    progress_pct: Percentage


@dataclass
class DashboardSummary:
    currency: str
    net_balance: Money
    monthly_obligations_total: Money
    income_commitment_pct: Optional[Percentage]
    main_goal: Optional[MainGoalSummary]
    upcoming_events: list[FinancialEvent]


class GetDashboardSummaryUseCase:
    def __init__(
        self,
        account_repo: Any,
        income_repo: Any,
        obligation_repo: Any,
        goal_repo: Any,
        event_repo: Any,
    ) -> None:
        self._account_repo = account_repo
        self._income_repo = income_repo
        self._obligation_repo = obligation_repo
        self._goal_repo = goal_repo
        self._event_repo = event_repo

    def execute(self, profile_id: str, currency: str) -> DashboardSummary:
        accounts = self._account_repo.list_by_profile(profile_id)
        incomes: list[IncomeSource] = self._income_repo.list_by_profile(profile_id)
        obligations: list[FinancialObligation] = self._obligation_repo.list_by_profile(profile_id)
        goals: list[FinancialGoal] = self._goal_repo.list_by_profile(profile_id)
        events: list[FinancialEvent] = self._event_repo.list_by_profile(profile_id)

        net_balance = _sum_money(currency, [account.balance for account in accounts])

        monthly_obligations = [
            monthly
            for obligation in obligations
            if (monthly := monthly_equivalent(obligation.amount, obligation.frequency)) is not None
        ]
        monthly_obligations_total = _sum_money(currency, monthly_obligations)

        monthly_incomes = [
            monthly for income in incomes if (monthly := monthly_equivalent(income.amount, income.frequency)) is not None
        ]
        monthly_income_total = _sum_money(currency, monthly_incomes)

        income_commitment_pct = None
        if monthly_income_total.amount > 0:
            fraction = min(monthly_obligations_total.amount / monthly_income_total.amount, Decimal("1"))
            income_commitment_pct = Percentage(fraction)

        main_goal = None
        if goals:
            top_goal = min(goals, key=lambda goal: goal.priority)
            fraction = Decimal("0")
            if top_goal.target_amount.amount > 0:
                fraction = min(top_goal.current_amount.amount / top_goal.target_amount.amount, Decimal("1"))
            main_goal = MainGoalSummary(description=top_goal.description, progress_pct=Percentage(fraction))

        today = date.today()
        upcoming_events = sorted((event for event in events if event.date >= today), key=lambda event: event.date)[:5]

        return DashboardSummary(
            currency=currency,
            net_balance=net_balance,
            monthly_obligations_total=monthly_obligations_total,
            income_commitment_pct=income_commitment_pct,
            main_goal=main_goal,
            upcoming_events=upcoming_events,
        )
