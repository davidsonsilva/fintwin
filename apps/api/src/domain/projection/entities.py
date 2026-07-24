"""Estruturas de saída do motor de projeção (Spec seção 8.3/8.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.cashflow.entities import FinancialEvent
from src.domain.shared.enums import ScenarioType
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage


@dataclass
class PeriodProjection:
    period: str  # "YYYY-MM"
    opening_balance: Money
    income_total: Money
    expense_total: Money
    net_cashflow: Money
    closing_balance: Money
    income_commitment_percentage: Optional[Percentage]
    deficit: bool


@dataclass
class ProjectionResult:
    scenario: ScenarioType
    periods: list[PeriodProjection]
    first_deficit_period: Optional[str]
    lowest_balance: Money
    final_balance: Money
    total_income: Money
    total_expenses: Money
    main_pressures: list[str]
    relevant_events: list[FinancialEvent]
    assumptions: list[str]
