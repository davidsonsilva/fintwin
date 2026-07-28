# Copyright (C) 2026 Davidson Silva
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 of the License.

"""Distribuição das despesas mensais por categoria (linha de gráficos do dashboard)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.domain.obligations.entities import FinancialObligation
from src.domain.shared.money import Money
from src.domain.shared.percentage import Percentage
from src.domain.shared.recurrence import monthly_equivalent


@dataclass
class CategoryBreakdown:
    category: str
    amount: Money
    percentage: Percentage


class GetExpenseBreakdownByCategoryUseCase:
    def __init__(self, obligation_repo: Any) -> None:
        self._obligation_repo = obligation_repo

    def execute(self, profile_id: str, currency: str) -> list[CategoryBreakdown]:
        obligations: list[FinancialObligation] = self._obligation_repo.list_by_profile(profile_id)

        totals: dict[str, Decimal] = {}
        for obligation in obligations:
            monthly = monthly_equivalent(obligation.amount, obligation.frequency)
            if monthly is None:
                continue
            totals[obligation.category] = totals.get(obligation.category, Decimal("0")) + monthly.amount

        grand_total = sum(totals.values(), Decimal("0"))

        breakdown = [
            CategoryBreakdown(
                category=category,
                amount=Money(amount, currency),
                percentage=Percentage(amount / grand_total if grand_total > 0 else Decimal("0")),
            )
            for category, amount in totals.items()
        ]
        return sorted(breakdown, key=lambda item: item.amount.amount, reverse=True)
